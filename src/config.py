"""
Bot configuration - all credentials from environment variables
"""
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_NAME = os.getenv("BOT_NAME", "بوت أخبار الذكاء الاصطناعي")
BOT_USERNAME = os.getenv("BOT_USERNAME", "Creator_Pro11560_bot")
SHEET_NAME = os.getenv("SHEET_NAME", "AI News Bot - أخبار الذكاء الاصطناعي")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-100"))

# Google Sheets service account - from env var (JSON string) or None
_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
SERVICE_ACCOUNT_INFO = None
if _SERVICE_ACCOUNT_JSON:
    import json
    try:
        SERVICE_ACCOUNT_INFO = json.loads(_SERVICE_ACCOUNT_JSON)
    except json.JSONDecodeError:
        pass
