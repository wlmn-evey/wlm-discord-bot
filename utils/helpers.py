import discord
import datetime
from typing import Union, Optional
from discord.ext import commands

async def get_or_create_user(session, user_id: int, guild_id: int):
    """Get a user from the database or create them if they don't exist."""
    from utils.database import User
    
    user = session.query(User).filter_by(user_id=user_id, guild_id=guild_id).first()
    if not user:
        user = User(user_id=user_id, guild_id=guild_id)
        session.add(user)
        session.commit()
    return user

async def get_guild_settings(session, guild_id: int):
    """Get guild settings or create default settings if they don't exist."""
    from utils.database import GuildSettings
    
    settings = session.query(GuildSettings).filter_by(guild_id=guild_id).first()
    if not settings:
        settings = GuildSettings(guild_id=guild_id)
        session.add(settings)
        session.commit()
    return settings

def format_time(dt: datetime.datetime) -> str:
    """Format a datetime object to a human-readable string."""
    return f'<t:{int(dt.timestamp())}:F> (<t:{int(dt.timestamp())}:R>)'

async def is_moderator(ctx: commands.Context) -> bool:
    """Check if the command invoker is a moderator or admin."""
    if ctx.author.guild_permissions.administrator:
        return True
    
    from utils.database import GuildSettings, session_scope
    
    with session_scope() as session:
        settings = await get_guild_settings(session, ctx.guild.id)
        if not settings:
            return False
            
        mod_role = settings.mod_role
        admin_role = settings.admin_role
        
        if admin_role and any(role.id == admin_role for role in ctx.author.roles):
            return True
            
        if mod_role and any(role.id == mod_role for role in ctx.author.roles):
            return True
    
    return False

async def send_embed(
    ctx: commands.Context,
    title: str = None,
    description: str = None,
    color: Union[discord.Color, int] = None,
    **kwargs
) -> discord.Message:
    """Send an embed message with consistent styling."""
    if color is None:
        color = discord.Color.blue()
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        **kwargs
    )
    
    return await ctx.send(embed=embed)

def error_embed(description: str, title: str = '❌ Error') -> discord.Embed:
    """Create an error embed with consistent styling."""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )

def success_embed(description: str, title: str = '✅ Success') -> discord.Embed:
    """Create a success embed with consistent styling."""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )

def info_embed(description: str, title: str = 'ℹ️ Info') -> discord.Embed:
    """Create an info embed with consistent styling."""
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blue()
    )

async def paginate(ctx: commands.Context, pages: list, timeout: int = 60) -> None:
    """Paginate a list of embeds or strings."""
    if not pages:
        return
    
    current_page = 0
    message = await ctx.send(embed=pages[0] if isinstance(pages[0], discord.Embed) else pages[0])
    
    if len(pages) == 1:
        return
    
    await message.add_reaction('⏮')
    await message.add_reaction('◀')
    await message.add_reaction('▶')
    await message.add_reaction('⏭')
    
    def check(reaction, user):
        return (
            user == ctx.author
            and reaction.message.id == message.id
            and str(reaction.emoji) in ['⏮', '◀', '▶', '⏭']
        )
    
    while True:
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
            
            if str(reaction.emoji) == '⏮' and current_page != 0:
                current_page = 0
            elif str(reaction.emoji) == '◀' and current_page > 0:
                current_page -= 1
            elif str(reaction.emoji) == '▶' and current_page < len(pages) - 1:
                current_page += 1
            elif str(reaction.emoji) == '⏭' and current_page != len(pages) - 1:
                current_page = len(pages) - 1
            
            try:
                await message.remove_reaction(reaction, user)
            except discord.Forbidden:
                pass
                
            if isinstance(pages[current_page], discord.Embed):
                await message.edit(embed=pages[current_page])
            else:
                await message.edit(content=pages[current_page])
                
        except asyncio.TimeoutError:
            try:
                await message.clear_reactions()
            except discord.Forbidden:
                for reaction in ['⏮', '◀', '▶', '⏭']:
                    await message.remove_reaction(reaction, ctx.bot.user)
            break
