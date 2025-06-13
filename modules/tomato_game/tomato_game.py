import logging
import discord
from discord import app_commands
from discord.ext import commands

import random
from utils.database import (
    increment_tomato_stat,
    get_leaderboard,
    get_inventory,
    remove_from_inventory,
    claim_starter_tomatoes,
    process_daily_claim,
    get_or_create_tomato_stats,
    add_to_inventory
)

logger = logging.getLogger(__name__)


class DodgeView(discord.ui.View):
    def __init__(self, thrower: discord.Member, target: discord.Member):
        super().__init__(timeout=8.0)  # 8-second window to dodge
        self.thrower = thrower
        self.target = target
        self.dodged = False

    @discord.ui.button(label='Dodge!', style=discord.ButtonStyle.primary, emoji='🏃')
    async def dodge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.target:
            await interaction.response.send_message("This isn't for you to dodge!", ephemeral=True)
            return

        self.dodged = True
        # The view's only job is to report that the dodge was successful.
        # The command will handle stat updates.
        self.clear_items()
        await interaction.response.edit_message(content=f"💨 Whoosh! **{self.target.display_name}** dodged the tomato from **{self.thrower.display_name}**!", view=None)
        self.stop()

    async def on_timeout(self):
        self.stop()


class TomatoGame(commands.Cog):
    """A fun game module for pelting users with tomatoes."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lootbox_cost = 100
        self.loot_table = {
            'Regular Tomato': 0.70,
            'Rotten Tomato': 0.25,
            'Golden Tomato': 0.05,
        }
        # In-memory cache for message-based reward milestones
        # {user_id: message_milestone}
        self.user_milestones = {}

    @app_commands.command(name='claim', description='Claim your starter pack of tomatoes!')
    async def claim(self, interaction: discord.Interaction):
        if claim_starter_tomatoes(interaction.user.id):
            await interaction.response.send_message("You received 5 Regular Tomatoes! Use `/inventory` to see them.", ephemeral=True)
        else:
            await interaction.response.send_message("You have already claimed your starter pack.", ephemeral=True)

    @app_commands.command(name='daily', description='Claim your daily Tomato Coins!')
    async def daily(self, interaction: discord.Interaction):
        success, result = process_daily_claim(interaction.user.id)
        if success:
            stats = get_or_create_tomato_stats(interaction.user.id)
            await interaction.response.send_message(f"🎉 You received {result} Tomato Coins! Your new balance is {stats.coins} coins.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⏳ {result}", ephemeral=True)

    @app_commands.command(name='balance', description='Check your Tomato Coin balance.')
    async def balance(self, interaction: discord.Interaction):
        stats = get_or_create_tomato_stats(interaction.user.id)
        await interaction.response.send_message(f"💰 You have {stats.coins} Tomato Coins.", ephemeral=True)

    @app_commands.command(name='lootbox', description='Buy a lootbox for 100 coins!')
    async def lootbox(self, interaction: discord.Interaction):
        stats = get_or_create_tomato_stats(interaction.user.id)
        
        if stats.coins < self.lootbox_cost:
            return await interaction.response.send_message(f"You don't have enough coins! A lootbox costs {self.lootbox_cost} coins.", ephemeral=True)

        # Deduct coins
        increment_tomato_stat(interaction.user.id, 'coins', -self.lootbox_cost)

        # Roll for loot
        items = list(self.loot_table.keys())
        weights = list(self.loot_table.values())
        chosen_item = random.choices(items, weights=weights, k=1)[0]

        # Add to inventory
        add_to_inventory(interaction.user.id, chosen_item)

        # Announce result
        await interaction.response.send_message(f"You open the lootbox and find... a **{chosen_item}**! It has been added to your inventory.")

    @app_commands.command(name='inventory', description='Check your tomato inventory.')
    async def inventory(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        inv = get_inventory(interaction.user.id)
        embed = discord.Embed(title=f"{interaction.user.display_name}'s Inventory", color=discord.Color.green())
        if not inv:
            embed.description = "Your inventory is empty. Use `/claim` to get some starter tomatoes!"
        else:
            embed.description = "\n".join([f"- **{item.item_name}**: {item.quantity}" for item in inv])
        await interaction.followup.send(embed=embed)

    @app_commands.command(name='tomato', description='Pelt another member with a tomato from your inventory!')
    @app_commands.describe(item='Which tomato to throw? (Defaults to Regular Tomato)')
    @app_commands.choices(item=[
        app_commands.Choice(name='Regular Tomato', value='Regular Tomato'),
        app_commands.Choice(name='Rotten Tomato', value='Rotten Tomato'),
        app_commands.Choice(name='Golden Tomato', value='Golden Tomato'),
    ])
    async def tomato(self, interaction: discord.Interaction, target: discord.Member, item: app_commands.Choice[str] = None):
        if target == interaction.user:
            return await interaction.response.send_message("You can't throw a tomato at yourself!", ephemeral=True)
        if target == self.bot.user:
            return await interaction.response.send_message("You wouldn't dare throw a tomato at me!", ephemeral=True)

        item_to_throw = item.value if item else 'Regular Tomato'

        if not remove_from_inventory(interaction.user.id, item_to_throw):
            return await interaction.response.send_message(f"You don't have any '{item_to_throw}'s to throw!", ephemeral=True)

        increment_tomato_stat(interaction.user.id, 'tomatoes_thrown')

        # Announce the throw
        throw_announcement = f"🍅 **{interaction.user.display_name}** is throwing a **{item_to_throw}** at **{target.display_name}**! Quick, dodge it!"
        
        # Special pre-throw effect for Rotten Tomato
        if item_to_throw == 'Rotten Tomato' and random.random() < 0.1: # 10% chance to backfire
            await interaction.response.send_message(f"🤢 Oh no! Your {item_to_throw} was so rotten it fell apart in your hand! You've made a mess of yourself.")
            return

        view = DodgeView(interaction.user, target)
        await interaction.response.send_message(throw_announcement, view=view)
        await view.wait()

        # Post-throw logic
        if view.dodged:
            increment_tomato_stat(target.id, 'tomatoes_dodged')
            # The dodge message is already handled in the view
        else: # Hit
            increment_tomato_stat(interaction.user.id, 'tomatoes_landed')
            increment_tomato_stat(target.id, 'times_hit')
            
            hit_message = f"Splat! 🍅 **{target.display_name}** wasn't fast enough and got hit by **{interaction.user.display_name}**'s {item_to_throw}!"
            
            # Special hit effects
            if item_to_throw == 'Rotten Tomato':
                hit_message += f"\nUgh, the smell! That's gonna leave a stain."
            elif item_to_throw == 'Golden Tomato':
                bonus_coins = 25
                increment_tomato_stat(interaction.user.id, 'coins', bonus_coins)
                hit_message += f"\n✨ Shiny! **{interaction.user.display_name}** earned {bonus_coins} Tomato Coins for the successful hit!"

            await interaction.edit_original_response(content=hit_message, view=None)

    leaderboard = app_commands.Group(name="tomatoleaderboard", description="View the tomato game leaderboards.")

    async def _send_leaderboard(self, interaction: discord.Interaction, stat_name: str, title: str):
        await interaction.response.defer()
        board_data = get_leaderboard(stat_name, limit=10)
        embed = discord.Embed(title=f"🍅 {title} 🍅", color=discord.Color.red())

        if not board_data:
            embed.description = "The leaderboard is empty! Start throwing tomatoes!"
        else:
            lines = []
            for i, stats in enumerate(board_data):
                user = self.bot.get_user(stats.user_id)
                user_name = user.display_name if user else f"User ID: {stats.user_id}"
                value = getattr(stats, stat_name)
                lines.append(f"**{i+1}.** {user_name} - {value}")
            embed.description = "\n".join(lines)

        await interaction.followup.send(embed=embed)

    @leaderboard.command(name="thrown", description="Top 10 tomato throwers.")
    async def leaderboard_thrown(self, interaction: discord.Interaction):
        await self._send_leaderboard(interaction, 'tomatoes_thrown', "Most Tomatoes Thrown")

    @leaderboard.command(name="landed", description="Top 10 most accurate throwers.")
    async def leaderboard_landed(self, interaction: discord.Interaction):
        await self._send_leaderboard(interaction, 'tomatoes_landed', "Most Tomatoes Landed")

    @leaderboard.command(name="hit", description="Top 10 most pelted members.")
    async def leaderboard_hit(self, interaction: discord.Interaction):
        await self._send_leaderboard(interaction, 'times_hit', "Most Times Hit")

    @leaderboard.command(name="dodged", description="Top 10 best dodgers.")
    async def leaderboard_dodged(self, interaction: discord.Interaction):
        await self._send_leaderboard(interaction, 'tomatoes_dodged', "Most Tomatoes Dodged")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listens to messages to grant coins for activity."""
        # Ignore bots, DMs, and short messages
        if message.author.bot or not message.guild or len(message.content.split()) < 5:
            return

        user_id = message.author.id
        increment_tomato_stat(user_id, 'message_count')
        stats = get_or_create_tomato_stats(user_id)

        # Check if user has a milestone set
        if user_id not in self.user_milestones:
            self.user_milestones[user_id] = stats.message_count + random.randint(15, 30)

        # Check if milestone is reached
        if stats.message_count >= self.user_milestones[user_id]:
            # Grant reward
            reward = random.randint(5, 25)
            increment_tomato_stat(user_id, 'coins', reward)

            logger.info(f"User {user_id} reached activity milestone, granting {reward} coins.")

            # Announce reward and make it disappear after 10s to reduce spam
            try:
                await message.channel.send(
                    f"🎉 **{message.author.display_name}**, your activity has earned you {reward} Tomato Coins!",
                    delete_after=10
                )
            except discord.errors.Forbidden:
                logger.warning(f"Could not send activity reward message in channel {message.channel.id}")

            # Set a new milestone
            self.user_milestones[user_id] = stats.message_count + random.randint(15, 30)


async def setup(bot):
    await bot.add_cog(TomatoGame(bot))
