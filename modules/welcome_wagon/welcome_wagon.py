import logging
import discord
from discord.ext import commands, tasks

from config import (
    WELCOME_WAGON_ROLE_ID,
    WELCOME_NEW_IN_TOWN_ROLE_ID,
    WELCOME_GRADUATION_THRESHOLD
)
from utils.database import get_or_create_activity, increment_message_count, get_and_clear_graduation_queue

logger = logging.getLogger(__name__)

class WelcomeWagon(commands.Cog):
    """Tools for the Welcome Wagon team to manage new members."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.suggest_graduates.start()
        self.process_graduation_queue.start()

    def cog_unload(self):
        self.suggest_graduates.cancel()
        self.process_graduation_queue.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Tracks message activity for all non-bot users."""
        if message.author.bot:
            return
        increment_message_count(message.author.id)

    @commands.command(name='newmembers', help='Lists all new members and their activity.')
    @commands.has_role(WELCOME_WAGON_ROLE_ID)
    async def list_new_members(self, ctx: commands.Context):
        """Shows a list of all members with the 'New In Town' role."""
        new_in_town_role = ctx.guild.get_role(WELCOME_NEW_IN_TOWN_ROLE_ID)
        if not new_in_town_role:
            return await ctx.send('"New In Town" role not found. Check config.')

        new_members = [m for m in ctx.guild.members if new_in_town_role in m.roles]

        if not new_members:
            return await ctx.send('No members are currently "New In Town".')

        embed = discord.Embed(
            title='New Members Activity Report',
            color=discord.Color.green()
        )

        member_lines = []
        for member in new_members:
            activity = get_or_create_activity(member.id)
            member_lines.append(f'**{member.display_name}**: {activity.message_count} messages')
        
        embed.description = '\n'.join(member_lines)
        await ctx.send(embed=embed)

    @commands.command(name='graduate', help='Graduates a member, removing the New In Town role.')
    @commands.has_role(WELCOME_WAGON_ROLE_ID)
    async def graduate_member(self, ctx: commands.Context, member: discord.Member):
        """Manually graduates a member from the 'New In Town' program."""
        new_in_town_role = ctx.guild.get_role(WELCOME_NEW_IN_TOWN_ROLE_ID)
        if not new_in_town_role or new_in_town_role not in member.roles:
            return await ctx.send(f'{member.display_name} is not in the "New In Town" program.')

        await member.remove_roles(new_in_town_role, reason='Graduated by Welcome Wagon.')
        logger.info(f'{member.display_name} was graduated by {ctx.author.display_name}.')
        await ctx.send(f'🎓 **{member.display_name}** has been successfully graduated!')

    @tasks.loop(hours=24)
    async def suggest_graduates(self):
        """Daily task to suggest active new members for graduation."""
        logger.info('Running daily check for graduation suggestions.')
        for guild in self.bot.guilds:
            welcome_wagon_role = guild.get_role(WELCOME_WAGON_ROLE_ID)
            new_in_town_role = guild.get_role(WELCOME_NEW_IN_TOWN_ROLE_ID)

            if not welcome_wagon_role or not new_in_town_role:
                continue

            # Find a channel the Welcome Wagon team can see
            # This is a simple approach; a dedicated channel ID in config is better
            report_channel = discord.utils.find(lambda c: welcome_wagon_role in c.changed_roles, guild.text_channels)
            if not report_channel:
                logger.warning(f'No suitable channel found in guild {guild.name} to post graduation suggestions.')
                continue

            new_members = [m for m in guild.members if new_in_town_role in m.roles]
            suggestions = []
            for member in new_members:
                activity = get_or_create_activity(member.id)
                if activity.message_count >= WELCOME_GRADUATION_THRESHOLD:
                    suggestions.append(member)
            
            if suggestions:
                embed = discord.Embed(
                    title='🎓 Graduation Suggestions',
                    description='The following members have been highly active and could be ready for graduation:',
                    color=discord.Color.gold()
                )
                for member in suggestions:
                    embed.add_field(name=member.display_name, value=f'{get_or_create_activity(member.id).message_count} messages', inline=False)
                
                await report_channel.send(embed=embed)

    @suggest_graduates.before_loop
    async def before_suggest_graduates(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=30)
    async def process_graduation_queue(self):
        """Processes graduation requests from the web dashboard queue."""
        user_ids = get_and_clear_graduation_queue()
        if not user_ids:
            return

        logger.info(f'Processing {len(user_ids)} graduations from the web dashboard.')
        for guild in self.bot.guilds:
            new_in_town_role = guild.get_role(WELCOME_NEW_IN_TOWN_ROLE_ID)
            if not new_in_town_role:
                logger.warning(f'Could not find \'New In Town\' role in guild {guild.name} to process queue.')
                continue

            for user_id in user_ids:
                member = guild.get_member(user_id)
                if member and new_in_town_role in member.roles:
                    try:
                        await member.remove_roles(new_in_town_role, reason='Graduated via Web Dashboard.')
                        logger.info(f'Graduated {member.display_name} ({user_id}) via web dashboard.')
                    except discord.Forbidden:
                        logger.error(f'Bot lacks permissions to graduate {member.display_name} in {guild.name}.')
                    except discord.HTTPException as e:
                        logger.error(f'HTTP error while graduating {member.display_name}: {e}')
                elif member:
                    logger.warning(f'User {user_id} from queue was found but did not have the \'New In Town\' role.')

    @process_graduation_queue.before_loop
    async def before_process_graduation_queue(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(WelcomeWagon(bot))
