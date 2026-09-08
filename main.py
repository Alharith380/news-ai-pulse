#!/usr/bin/env python3
"""
Telegram AI News Bot - Main Entry Point
Runs bot + daily scheduler + REST API concurrently
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

load_dotenv()
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

import uvicorn
from src.bot import run_bot_with_api

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def serve_api():
    """Start FastAPI server"""
    config = uvicorn.Config(
        "api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    print("=" * 50)
    print("🤖 بوت أخبار الذكاء الاصطناعي + API")
    print("=" * 50)
    print("🚀 جاري تشغيل البوت و API معاً...")
    print("=" * 50)
    sys.stdout.flush()

    await asyncio.gather(
        run_bot_with_api(),
        serve_api(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop" in str(e).lower():
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
