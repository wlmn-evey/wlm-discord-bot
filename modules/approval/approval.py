import logging
import re
import discord
from discord.ext import commands, tasks

from config import (
    APPROVAL_WAITING_ROOM_CHANNEL_ID,
    APPROVAL_UNAPPROVED_ROLE_ID,
    APPROVAL_MEMBER_ROLE_ID,
    PRONOUN_REGEX,
    WELCOME_NEW_IN_TOWN_ROLE_ID
)

logger = logging.getLogger(__name__)

# Regex for checking pronouns
pronoun_regex = re.compile(PRONOUN_REGEX)

# --- Helper Functions ---
async def update_nickname_with_pronouns(member: discord.Member, pronouns: str) -> bool:
    """Updates a member's nickname to include pronouns."""
    base_name = member.name
    # If user already has a nickname, strip old pronouns before adding new ones
    if member.nick:
        base_name = re.sub(pronoun_regex, '', member.nick).strip()

    new_nickname = f"{base_name} ({pronouns})"
    if len(new_nickname) > 32:
        await member.send("Your nickname is too long to add pronouns automatically. Please shorten it and try again.")
        return False
    
    try:
        await member.edit(nick=new_nickname)
        return True
    except discord.Forbidden:
        logger.warning(f"Could not change nickname for {member.display_name} - missing permissions.")
        return False

# --- UI Components ---
class PronounModal(discord.ui.Modal, title='Set Custom Pronouns'):
    pronouns = discord.ui.TextInput(
        label='Your Pronouns',
        placeholder='e.g., ze/zir, fae/faer',
        style=discord.TextStyle.short
    )

    async def on_submit(self, interaction: discord.Interaction):
        pronouns_str = self.pronouns.value
        if '/' not in pronouns_str:
            await interaction.response.send_message('Please use the format `pronoun/pronoun`.', ephemeral=True)
            return

        success = await update_nickname_with_pronouns(interaction.user, pronouns_str)
        if success:
            await interaction.response.send_message(f'Your pronouns have been set to `{pronouns_str}`!', ephemeral=True)

class PronounView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Persistent view

    @discord.ui.button(label='she/her', style=discord.ButtonStyle.secondary, custom_id='pronoun_she_her')
    async def she_her(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await update_nickname_with_pronouns(interaction.user, 'she/her')
        if success:
            await interaction.response.send_message('Your pronouns have been set to `she/her`!', ephemeral=True)

    @discord.ui.button(label='he/him', style=discord.ButtonStyle.secondary, custom_id='pronoun_he_him')
    async def he_him(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await update_nickname_with_pronouns(interaction.user, 'he/him')
        if success:
            await interaction.response.send_message('Your pronouns have been set to `he/him`!', ephemeral=True)

    @discord.ui.button(label='they/them', style=discord.ButtonStyle.secondary, custom_id='pronoun_they_them')
    async def they_them(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await update_nickname_with_pronouns(interaction.user, 'they/them')
        if success:
            await interaction.response.send_message('Your pronouns have been set to `they/them`!', ephemeral=True)

    @discord.ui.button(label='Custom', style=discord.ButtonStyle.primary, custom_id='pronoun_custom')
    async def custom(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PronounModal())

# --- Main Cog ---
class MemberApproval(commands.Cog):
    """Handles new member approval and pronoun enforcement."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(PronounView()) # Register the persistent view
        self.enforce_pronouns.start()

    def cog_unload(self):
        self.enforce_pronouns.cancel()

    async def _approve_member(self, member: discord.Member):
        """Grants a member full access to the server."""
        unapproved_role = member.guild.get_role(APPROVAL_UNAPPROVED_ROLE_ID)
        member_role = member.guild.get_role(APPROVAL_MEMBER_ROLE_ID)
        new_in_town_role = member.guild.get_role(WELCOME_NEW_IN_TOWN_ROLE_ID)

        if not unapproved_role or not member_role or not new_in_town_role:
            logger.error('One or more roles not found (Unapproved, Member, or New In Town). Check config.py.')
            return

        if unapproved_role in member.roles:
            await member.remove_roles(unapproved_role, reason='Pronouns set, user approved.')
            await member.add_roles(member_role, new_in_town_role, reason='Pronoun-based approval.')
            logger.info(f'Approved member {member.display_name}. Assigned "New In Town" role.')
            try:
                await member.send(f"Thank you! Your nickname has been updated and you now have full access to the **{member.guild.name}** server.")
            except discord.Forbidden:
                pass # Can't DM user

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Assigns unapproved role and sends welcome message."""
        waiting_room = member.guild.get_channel(APPROVAL_WAITING_ROOM_CHANNEL_ID)
        unapproved_role = member.guild.get_role(APPROVAL_UNAPPROVED_ROLE_ID)

        if not waiting_room or not unapproved_role:
            logger.error('Waiting room or unapproved role not found. Check config.py.')
            return

        await member.add_roles(unapproved_role, reason='New member, awaiting approval.')
        logger.info(f'New member {member.name} has joined and is in the waiting room.')

        embed = discord.Embed(
            title=f'Welcome to {member.guild.name}!',
            description=(
                'To ensure an inclusive community, we ask all members to display their pronouns in their server nickname.\n\n' 
                'Please use the buttons below to set your pronouns. This will automatically update your nickname and grant you access to the server.'
            ),
            color=discord.Color.blue()
        )
        await waiting_room.send(f'Welcome, {member.mention}!', embed=embed, view=PronounView())

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Checks for nickname changes to approve members."""
        unapproved_role = after.guild.get_role(APPROVAL_UNAPPROVED_ROLE_ID)
        if unapproved_role not in after.roles or before.nick == after.nick:
            return # Not an unapproved member or nickname didn't change

        if after.nick and pronoun_regex.search(after.nick):
            logger.info(f'Member {after.display_name} manually set nickname with pronouns.')
            await self._approve_member(after)

    @tasks.loop(hours=1)
    async def enforce_pronouns(self):
        """Periodically check all members for pronoun compliance."""
        logger.info('Running hourly pronoun enforcement check...')
        for guild in self.bot.guilds:
            member_role = guild.get_role(APPROVAL_MEMBER_ROLE_ID)
            unapproved_role = guild.get_role(APPROVAL_UNAPPROVED_ROLE_ID)
            if not member_role or not unapproved_role:
                continue

            for member in guild.members:
                # Check members who have the main role but not the unapproved one
                if member_role in member.roles and unapproved_role not in member.roles:
                    if not member.nick or not pronoun_regex.search(member.nick):
                        logger.info(f'Member {member.display_name} found without pronouns. Reverting to unapproved.')
                        await member.remove_roles(member_role, reason='Pronoun policy enforcement.')
                        await member.add_roles(unapproved_role, reason='Pronoun policy enforcement.')
                        try:
                            await member.send(
                                f"""Hi there! We noticed your nickname on the **{guild.name}** server no longer includes pronouns.

To regain access, please head to the waiting room and set them again. Thank you!"""
                            )
                        except discord.Forbidden:
                            pass # Can't DM

    @enforce_pronouns.before_loop
    async def before_enforce_pronouns(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(MemberApproval(bot))
