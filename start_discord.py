from src.openclaw.discord_bot import start_discord_bot
from dotenv import load_dotenv
import asyncio
import os

load_dotenv()
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_DB_ID = os.getenv('NOTION_DB_ID')

asyncio.run(start_discord_bot(NOTION_API_KEY, NOTION_DB_ID))
