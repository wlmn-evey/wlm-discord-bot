import asyncio
import logging
import logging.handlers
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
import uvicorn

from config import BOT_TOKEN, BOT_PREFIX, BOT_OWNER_IDS, LOG_LEVEL, LOG_FILE, MODULES
from dashboard import api as dashboard_api
from utils.sheets_client import init_gsheet_client
from utils.config_validator import validate_config

# Set up logging
os.makedirs('data', exist_ok=True)
logger = logging.getLogger('discord')
logger.setLevel(getattr(logging, LOG_LEVEL))

# File handler
file_handler = logging.handlers.RotatingFileHandler(
    filename=LOG_FILE,
    encoding='utf-8',
    maxBytes=32 * 1024 * 1024,  # 32 MiB
    backupCount=5,
)
dtf = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dtf, style='{')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Initialize bot with intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

class WLMBot(commands.Bot):
    def __init__(self, missing_config: list):
        super().__init__(
            command_prefix=BOT_PREFIX,
            intents=intents,
            owner_ids=set(BOT_OWNER_IDS),
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                roles=False, users=True, everyone=False, replied_user=True
            ),
        )
        self.logger = logger
        self.initial_extensions = MODULES
        self.synced = False
        self.missing_config = missing_config

    async def setup_hook(self):
        """Load all modules on startup."""
        if self.missing_config:
            self.logger.warning("Skipping module loading due to missing configuration.")
            return

        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                self.logger.info(f'Successfully loaded extension {extension}')
            except Exception as e:
                self.logger.error(f'Failed to load extension {extension}: {e}')
        
        await self.tree.sync()
        self.logger.info('Synced application commands')

    async def on_ready(self):
        """Called when the bot is ready."""
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        self.logger.info('------')
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"for {BOT_PREFIX}help"
        )
        await self.change_presence(activity=activity)

    async def on_disconnect(self):
        logger.info("Bot disconnected. Attempting to reconnect...")

    async def on_resumed(self):
        logger.info("Bot has reconnected and resumed session.")

async def run_web_server(bot_instance):
    """Runs the FastAPI web server as a background task."""
    try:
        dashboard_api.setup_api(bot_instance)
        config = uvicorn.Config(dashboard_api.app, host="0.0.0.0", port=8080, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    except asyncio.CancelledError:
        logger.info("Web server task cancelled.")
    except Exception as e:
        logger.error(f"Web server crashed: {e}", exc_info=True)

async def main():
    """Main entry point for the bot."""
    missing_keys = validate_config()
    bot = WLMBot(missing_config=missing_keys)
    
    web_server_task = asyncio.create_task(run_web_server(bot))

    if 'DISCORD_BOT_TOKEN (in .env file)' in missing_keys:
        logger.error("Discord bot token is missing. The bot will not start.")
        if len(missing_keys) > 1:
            other_keys = ", ".join([k for k in missing_keys if k != 'DISCORD_BOT_TOKEN (in .env file)'])
            logger.error(f"Other missing config: {other_keys}")
        await web_server_task
    else:
        logger.info("Starting bot and web server.")
        await asyncio.gather(
            web_server_task,
            bot.start(BOT_TOKEN)
        )

if __name__ == '__main__':
    init_gsheet_client()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Shutting down...')
    except Exception as e:
        logger.critical(f'Fatal error: {e}', exc_info=True)
        sys.exit(1)
