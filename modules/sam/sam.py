import logging
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone

from utils.sheets_client import gsheet_client
from utils.database import session_scope, Warning

logger = logging.getLogger(__name__)

class SAMModule(commands.Cog):
    """Server Appraisal and Moderation Module."""

    def __init__(self, bot):
        self.bot = bot
        if gsheet_client.worksheet:
            self.update_channel_scores.start()
        else:
            logger.error('Google Sheet not available. SAM module task will not start.')

    def cog_unload(self):
        self.update_channel_scores.cancel()

    @tasks.loop(hours=24)
    async def update_channel_scores(self):
        """Periodically update the channel scores in the Google Sheet."""
        logger.info('Starting daily channel score update...')
        if not gsheet_client.worksheet:
            logger.error('Aborting channel score update, Google Sheet is not available.')
            return

        for guild in self.bot.guilds:
            logger.info(f'Processing channels for guild: {guild.name}')
            for channel in guild.text_channels:
                try:
                    data = await self._calculate_channel_metrics(channel)
                    gsheet_client.update_channel_data(channel.id, data)
                except discord.errors.Forbidden:
                    logger.warning(f'No permission to view channel {channel.name} in {guild.name}')
                except Exception as e:
                    logger.error(f'Error processing channel {channel.name}: {e}', exc_info=True)
        logger.info('Finished daily channel score update.')

    async def _calculate_channel_metrics(self, channel: discord.TextChannel) -> dict:
        """Calculate all health metrics for a given channel."""
        score = 100  # Start with a perfect score

        # 1. Best Practices
        has_topic = bool(channel.topic)
        has_pins = bool(await channel.pins())
        naming_ok = '-' in channel.name or '_' in channel.name
        perms_ok = not channel.permissions_for(channel.guild.default_role).send_messages if 'announce' in channel.name.lower() else True

        if not has_topic: score -= 10
        if not has_pins: score -= 5
        if not naming_ok: score -= 5
        if not perms_ok: score -= 20

        # 2. Utilization
        fourteen_days_ago = datetime.now(timezone.utc) - timedelta(days=14)
        try:
            message_count = len([m async for m in channel.history(limit=100, after=fourteen_days_ago)])
            last_message_time = (await channel.history(limit=1).next()).created_at
        except (discord.errors.Forbidden, StopAsyncIteration):
            message_count = 0
            last_message_time = None
        
        is_underutilized = message_count < 10
        if is_underutilized: score -= 15

        # 3. Moderation Problems
        with session_scope() as session:
            mod_actions = session.query(Warning).filter(
                Warning.guild_id == channel.guild.id,
                Warning.channel_id == channel.id,
                Warning.created_at > fourteen_days_ago
            ).count()
        
        score -= mod_actions * 10 # -10 for each warning

        return {
            'Channel ID': str(channel.id),
            'Channel Name': channel.name,
            'Category': channel.category.name if channel.category else 'N/A',
            'Has Topic': 'Yes' if has_topic else 'No',
            'Has Pinned Messages': 'Yes' if has_pins else 'No',
            'Naming Convention OK': 'Yes' if naming_ok else 'No',
            'Permissions OK': 'Yes' if perms_ok else 'No',
            'Last Message Timestamp': last_message_time.isoformat() if last_message_time else 'N/A',
            'Message Count (14d)': message_count,
            'Is Under-utilized': 'Yes' if is_underutilized else 'No',
            'Moderation Actions': mod_actions,
            'Health Score': max(0, score), # Score can't be negative
            'Last Updated': datetime.now(timezone.utc).isoformat()
        }

    @update_channel_scores.before_loop
    async def before_update_channel_scores(self):
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()
        logger.info('SAM module is ready and task loop is starting.')

    @commands.hybrid_command(name='sam_update')
    @commands.is_owner()
    async def force_sam_update(self, ctx: commands.Context):
        """Manually trigger the SAM module channel score update."""
        await ctx.send('🔄 Starting manual channel score update...', ephemeral=True)
        # Run the update in the background
        self.bot.loop.create_task(self.update_channel_scores())

async def setup(bot):
    """Load the SAMModule cog."""
    await bot.add_cog(SAMModule(bot))
