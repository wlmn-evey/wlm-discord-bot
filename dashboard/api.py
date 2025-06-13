from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import discord
from typing import List, Optional

import config

# This will be set by the bot process on startup
bot_instance: Optional[discord.Client] = None

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5173",  # React frontend
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the bot instance
def get_bot() -> discord.Client:
    if bot_instance is None:
        raise HTTPException(status_code=503, detail="Bot is not ready yet.")
    return bot_instance

@app.get("/api/status")
async def get_status(bot: discord.Client = Depends(get_bot)):
    return {
        "logged_in": bot.is_ready(),
        "missing_config": getattr(bot, 'missing_config', []),
    }

@app.get("/api/welcome-wagon/new-members")
async def get_new_members(bot: discord.Client = Depends(get_bot)):
    guild = bot.get_guild(config.GUILD_ID)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found.")

    new_in_town_role = guild.get_role(config.WELCOME_NEW_IN_TOWN_ROLE_ID)
    if not new_in_town_role:
        raise HTTPException(status_code=404, detail="'New In Town' role not found.")

    new_members = []
    for member in new_in_town_role.members:
        new_members.append({
            "id": member.id,
            "name": member.name,
            "discriminator": member.discriminator,
            "display_name": member.display_name,
            "avatar_url": str(member.avatar.url) if member.avatar else None,
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        })

    return new_members

def setup_api(bot: discord.Client):
    """Initializes the API with the bot instance."""
    global bot_instance
    bot_instance = bot
