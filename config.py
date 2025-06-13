import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
BOT_PREFIX = '!'
BOT_OWNER_IDS = []  # Add owner Discord IDs here

# Database configuration
DATABASE_URL = 'sqlite:///data/bot.db'

# Module configuration
MODULES = [
    'modules.core.core',
    'modules.sam.sam',
    'modules.approval.approval',
    'modules.welcome_wagon.welcome_wagon',
    'modules.flag.flag',
    'modules.tomato_game.tomato_game',
]

# Logging configuration
LOG_LEVEL = 'INFO'
LOG_FILE = 'data/bot.log'

# Google Sheets configuration
GSHEET_SPREADSHEET_NAME = 'WLM Channel Health'
GSHEET_WORKSHEET_NAME = 'Channel Scores'

# Member Approval module configuration
APPROVAL_WAITING_ROOM_CHANNEL_ID = 1234567890  # Replace with your waiting room channel ID
APPROVAL_UNAPPROVED_ROLE_ID = 1234567890      # Replace with your 'unapproved' role ID
APPROVAL_MEMBER_ROLE_ID = 1234567890          # Replace with your main 'member' role ID
PRONOUN_REGEX = r'\(.*\/.*\)'                # Regex to find pronouns in brackets, e.g., (she/her)

# Welcome Wagon module configuration
WELCOME_WAGON_ROLE_ID = 1234567890         # Replace with your 'Welcome Wagon' team role ID
WELCOME_NEW_IN_TOWN_ROLE_ID = 1234567890  # Replace with your 'New In Town' role ID
WELCOME_GRADUATION_THRESHOLD = 50          # Number of messages to be considered for graduation

# Flag module configuration
FLAG_MODERATOR_ROLE_IDS = [1234567890]  # Replace with your Moderator and Admin role IDs
FLAG_NOTIFY_USER_IDS = [1234567890]      # Replace with user IDs to notify on a /red flag
