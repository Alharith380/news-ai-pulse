"""Run bot only (no API) for testing or standalone deployment"""
import asyncio
import logging
import sys

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from src.config import TELEGRAM_BOT_TOKEN, BOT_USERNAME
from src.bot import ChannelBot

import src.sheets_manager

def _sheets_init(self):
    self.creds = None
    self._sheet_id = None
src.sheets_manager.SheetsManager.__init__ = _sheets_init
src.sheets_manager.SheetsManager.append_news = lambda self, items: None
src.sheets_manager.SheetsManager.get_recent_news = lambda self, limit: []

async def main():
    print("=" * 50)
    print("🤖 Bot starting — running in standalone mode")
    print("=" * 50)
    sys.stdout.flush()

    bot = ChannelBot(TELEGRAM_BOT_TOKEN)
    await bot.application.initialize()
    await bot.application.updater.start_polling()
    await bot.application.start()
    print("✅ Bot is online")
    print("📢 Send /start to the bot")
    print("📢 Or use /channel to post news now")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())