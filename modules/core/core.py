import logging
import platform
from datetime import datetime, timezone

import discord
from discord.ext import commands

from config import BOT_PREFIX

class Core(commands.Cog):
    """Core functionality for the WLM Network bot."""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.now(timezone.utc)
        
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is loaded and ready."""
        self.logger.info(f'Cog {self.qualified_name} is ready')
    
    @commands.hybrid_command()
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)  # Convert to ms
        await ctx.send(f'🏓 Pong! Latency: {latency}ms')
    
    @commands.hybrid_command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Shut down the bot (Bot owner only)."""
        await ctx.send('👋 Shutting down...')
        await self.bot.close()
    
    @commands.hybrid_command()
    async def about(self, ctx):
        """Show information about the bot."""
        embed = discord.Embed(
            title='WLM Network Bot',
            description='A feature-rich bot for the Wanna Learn More Network',
            color=discord.Color.blue()
        )
        
        # Bot information
        uptime = datetime.now(timezone.utc) - self.start_time
        days, seconds = uptime.days, uptime.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        uptime_str = f'{days}d {hours}h {minutes}m'
        
        embed.add_field(name='Uptime', value=uptime_str, inline=True)
        embed.add_field(name='Python Version', value=platform.python_version(), inline=True)
        embed.add_field(name='discord.py Version', value=discord.__version__, inline=True)
        
        # Loaded cogs
        loaded_cogs = [f'`{cog}`' for cog in self.bot.cogs]
        if loaded_cogs:
            embed.add_field(name='Loaded Modules', value=', '.join(loaded_cogs), inline=False)
        
        embed.set_footer(text=f'Use {BOT_PREFIX}help to see available commands')
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command()
    @commands.guild_only()
    async def serverinfo(self, ctx):
        """Display information about the server."""
        guild = ctx.guild
        
        # Count different member statuses
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        # Count different channel types
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Calculate server age
        created_at = guild.created_at.strftime('%B %d, %Y')
        days_old = (datetime.now(timezone.utc) - guild.created_at).days
        
        embed = discord.Embed(
            title=guild.name,
            description=f'Created on {created_at} ({days_old} days ago)',
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Server info fields
        embed.add_field(name='Owner', value=guild.owner.mention, inline=True)
        embed.add_field(name='Region', value=str(guild.region).title(), inline=True)
        embed.add_field(name='Members', value=f'👥 {guild.member_count}', inline=True)
        
        # Member status fields
        embed.add_field(
            name='Status',
            value=f'🟢 {online} 🟠 {idle} 🔴 {dnd} ⚪ {offline}',
            inline=False
        )
        
        # Channel info fields
        embed.add_field(
            name='Channels',
            value=f'📝 {text_channels} text | 🎙️ {voice_channels} voice | 📂 {categories} categories',
            inline=False
        )
        
        # Server features
        if guild.features:
            features = ', '.join(feature.replace('_', ' ').title() for feature in guild.features)
            embed.add_field(name='Features', value=features, inline=False)
        
        # Server boost level if applicable
        if guild.premium_tier != 0:
            boost_level = guild.premium_tier
            boost_count = guild.premium_subscription_count
            boosters = len(guild.premium_subscribers)
            embed.add_field(
                name='Server Boost',
                value=f'Level {boost_level} with {boost_count} boosts ({boosters} boosters)',
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Load the Core cog."""
    await bot.add_cog(Core(bot))
