import config

def validate_config():
    """
    Validates the bot's configuration.
    Returns a list of missing configuration keys.
    """
    missing_keys = []
    
    # Critical environment variables
    if not config.BOT_TOKEN:
        missing_keys.append('DISCORD_BOT_TOKEN (in .env file)')

    # Critical config.py values (check for placeholder values)
    if config.GUILD_ID == 1234567890:
        missing_keys.append('GUILD_ID')
    if config.APPROVAL_WAITING_ROOM_CHANNEL_ID == 1234567890:
        missing_keys.append('APPROVAL_WAITING_ROOM_CHANNEL_ID')
    if config.APPROVAL_UNAPPROVED_ROLE_ID == 1234567890:
        missing_keys.append('APPROVAL_UNAPPROVED_ROLE_ID')
    if config.APPROVAL_MEMBER_ROLE_ID == 1234567890:
        missing_keys.append('APPROVAL_MEMBER_ROLE_ID')
    if config.WELCOME_WAGON_ROLE_ID == 1234567890:
        missing_keys.append('WELCOME_WAGON_ROLE_ID')
    if config.WELCOME_NEW_IN_TOWN_ROLE_ID == 1234567890:
        missing_keys.append('WELCOME_NEW_IN_TOWN_ROLE_ID')
    if not config.FLAG_MODERATOR_ROLE_IDS or config.FLAG_MODERATOR_ROLE_IDS == [1234567890]:
        missing_keys.append('FLAG_MODERATOR_ROLE_IDS')
    if not config.FLAG_NOTIFY_USER_IDS or config.FLAG_NOTIFY_USER_IDS == [1234567890]:
        missing_keys.append('FLAG_NOTIFY_USER_IDS')

    return missing_keys
