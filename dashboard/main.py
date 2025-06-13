import logging
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from discord.ext import commands

from config import GUILD_ID, WELCOME_NEW_IN_TOWN_ROLE_ID
from utils.database import get_or_create_activity, add_to_graduation_queue

logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="dashboard/templates")

def create_app(bot: commands.Bot) -> FastAPI:
    app = FastAPI()

    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        """Serves the Welcome Wagon dashboard page."""
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            return templates.TemplateResponse("error.html", {"request": request, "error": "Bot is not in the configured guild."}, status_code=500)

        new_in_town_role = guild.get_role(WELCOME_NEW_IN_TOWN_ROLE_ID)
        if not new_in_town_role:
            return templates.TemplateResponse("error.html", {"request": request, "error": "'New In Town' role not found."}, status_code=500)

        new_members = [m for m in guild.members if new_in_town_role in m.roles]
        
        member_data = []
        for member in new_members:
            activity = get_or_create_activity(member.id)
            member_data.append({
                "id": member.id,
                "name": member.display_name,
                "avatar_url": member.display_avatar.url,
                "message_count": activity.message_count
            })

        return templates.TemplateResponse("welcome_wagon.html", {"request": request, "members": member_data})

    @app.post("/graduate/{user_id}")
    async def graduate_user(user_id: int):
        """Adds a user to the graduation queue."""
        logger.info(f"Received web request to graduate user {user_id}")
        add_to_graduation_queue(user_id)
        return RedirectResponse(url="/", status_code=303)

    return app
