import logging
import discord
from discord import app_commands
from discord.ext import commands

from config import FLAG_MODERATOR_ROLE_IDS, FLAG_NOTIFY_USER_IDS
from utils.database import add_channel_warning

logger = logging.getLogger(__name__)

class Flag(commands.Cog):
    """A two-tiered channel flagging system for moderation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_moderator(self, user: discord.Member) -> bool:
        """Checks if a user has one of the configured moderator roles."""
        return any(role.id in FLAG_MODERATOR_ROLE_IDS for role in user.roles)

    @app_commands.command(name='yellow', description='Issue a gentle warning to de-escalate a tense conversation.')
    async def yellow_flag(self, interaction: discord.Interaction, reason: str):
        """Sends a gentle, non-militant warning to the channel."""
        if not self._is_moderator(interaction.user):
            return await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)

        embed = discord.Embed(
            title='A Gentle Reminder',
            description='Hey everyone, just a gentle reminder to keep our conversations constructive and welcoming. Let\'s steer this discussion back to a more positive track. Thanks!',
            color=discord.Color.yellow()
        )
        await interaction.channel.send(embed=embed)
        add_channel_warning(interaction.channel.id, interaction.user.id, interaction.guild.id, reason, 'yellow')
        await interaction.response.send_message('Yellow flag has been raised.', ephemeral=True)

    @app_commands.command(name='red', description='Issue an urgent warning and notify staff.')
    async def red_flag(self, interaction: discord.Interaction, reason: str):
        """Sends a firm warning and DM's staff for immediate attention."""
        if not self._is_moderator(interaction.user):
            return await interaction.response.send_message('You do not have permission to use this command.', ephemeral=True)

        # Send warning to the channel
        embed = discord.Embed(
            title='Attention Required',
            description='This conversation has become inappropriate. Please cease the current discussion immediately. Moderators have been notified and will be here shortly.',
            color=discord.Color.red()
        )
        await interaction.channel.send(embed=embed)

        # Log the warning
        add_channel_warning(interaction.channel.id, interaction.user.id, interaction.guild.id, reason, 'red')

        # Notify staff via DM
        notification_embed = discord.Embed(
            title='🚨 Red Flag Alert 🚨',
            description=f'A red flag was raised in `#{interaction.channel.name}` by **{interaction.user.display_name}**.',
            color=discord.Color.dark_red()
        )
        notification_embed.add_field(name='Reason', value=reason, inline=False)
        notification_embed.add_field(name='Jump to Channel', value=f'[Click Here]({interaction.channel.jump_url})', inline=False)

        for user_id in FLAG_NOTIFY_USER_IDS:
            try:
                user = await self.bot.fetch_user(user_id)
                await user.send(embed=notification_embed)
            except discord.NotFound:
                logger.warning(f'Could not find user with ID {user_id} to send red flag notification.')
            except discord.Forbidden:
                logger.warning(f'Could not DM user with ID {user_id}. They may have DMs disabled.')

        await interaction.response.send_message('Red flag has been raised and staff have been notified.', ephemeral=True)

async def setup(bot):
    await bot.add_cog(Flag(bot))
