"""
Google Sheets integration for AI News Bot
Publishes news to a Google Sheet automatically
Uses Sheets API only (no Drive API needed)
"""

import json
import logging
import os
from datetime import datetime

import requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.service_account import Credentials

from src.config import SERVICE_ACCOUNT_INFO, SHEET_NAME

logger = logging.getLogger(__name__)

SHEET_ID_FILE = "data/sheet_id.json"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = [
    "التاريخ",
    "العنوان",
    "الوصف",
    "المصدر",
    "الرابط",
    "صورة",
]


class SheetsManager:
    """Manages Google Sheets operations using Sheets API v4 directly"""

    def __init__(self):
        self.creds = None
        self._sheet_id = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google using service account"""
        if not SERVICE_ACCOUNT_INFO:
            logger.warning("⚠️ No Google service account configured, sheets disabled")
            return
        try:
            self.creds = Credentials.from_service_account_info(
                SERVICE_ACCOUNT_INFO, scopes=SCOPES
            )
            logger.info("✅ Google Sheets authenticated successfully")
        except Exception as e:
            logger.error(f"❌ Google Sheets auth failed: {e}")

    def _ensure_token(self):
        """Get or refresh access token"""
        if not self.creds:
            return
        if not self.creds.token or not self.creds.valid:
            self.creds.refresh(GoogleAuthRequest())

    def _request(self, method, url_suffix, body=None, params=None):
        """Make an authenticated request to Sheets API v4"""
        if not self.creds:
            return None
        self._ensure_token()
        headers = {
            "Authorization": f"Bearer {self.creds.token}",
            "Content-Type": "application/json",
        }
        url = f"https://sheets.googleapis.com/v4/spreadsheets{url_suffix}"
        resp = requests.request(method, url, headers=headers, json=body, params=params)
        if resp.status_code not in (200, 201, 204):
            logger.error(f"Sheets API error {resp.status_code}: {resp.text[:200]}")
            return None
        return resp.json() if resp.text else {}

    def _get_or_create_sheet(self):
        """Get existing sheet ID or create a new one"""
        if not self.creds:
            return None

        # Check if we already have a sheet ID saved
        if self._sheet_id:
            return self._sheet_id

        # Try to load saved sheet ID
        if os.path.exists(SHEET_ID_FILE):
            try:
                with open(SHEET_ID_FILE) as f:
                    data = json.load(f)
                    self._sheet_id = data.get("sheet_id")
                    if self._sheet_id:
                        logger.info(f"✅ Loaded saved sheet ID: {self._sheet_id}")
                        return self._sheet_id
            except Exception:
                pass

        # Create a new spreadsheet
        self._ensure_token()
        body = {
            "properties": {"title": SHEET_NAME},
            "sheets": [{"properties": {"title": "Sheet1"}}],
        }
        result = self._request("POST", "", body=body)
        if not result:
            return None

        self._sheet_id = result.get("spreadsheetId")
        logger.info(f"✅ Created new sheet: {SHEET_NAME} (ID: {self._sheet_id})")

        # Add header row
        self._request(
            "POST",
            f"/{self._sheet_id}/values/Sheet1!A1:F1:append",
            body={"values": [HEADERS]},
            params={"valueInputOption": "USER_ENTERED"},
        )

        # Save ID for next time
        try:
            os.makedirs("data", exist_ok=True)
            with open(SHEET_ID_FILE, "w") as f:
                json.dump({"sheet_id": self._sheet_id}, f)
        except Exception as e:
            logger.error(f"Failed to save sheet ID: {e}")

        return self._sheet_id

    def append_news(self, news_items: list):
        """Append news items to the Google Sheet"""
        if not self.creds:
            logger.warning("⚠️ Google Sheets not authenticated, skipping")
            return

        if not news_items:
            logger.info("ℹ️ No news items to append")
            return

        sheet_id = self._get_or_create_sheet()
        if not sheet_id:
            return

        self._ensure_token()
        today = datetime.now().strftime("%Y-%m-%d")
        values = []

        for news in news_items:
            values.append([
                today,
                news.get("title", ""),
                news.get("desc", news.get("snippet", "")),
                news.get("source", ""),
                news.get("link", ""),
                news.get("img", ""),
            ])

        result = self._request(
            "POST",
            f"/{sheet_id}/values/Sheet1!A:F:append",
            body={"values": values},
            params={"valueInputOption": "USER_ENTERED"},
        )

        if result:
            count = len(values)
            logger.info(f"✅ Added {count} news items to sheet '{SHEET_NAME}'")

    def get_recent_news(self, limit: int = 10):
        """Get recent news from the sheet"""
        sheet_id = self._get_or_create_sheet()
        if not sheet_id:
            return []

        self._ensure_token()
        result = self._request(
            "GET",
            f"/{sheet_id}/values/Sheet1!A:F",
            params={"majorDimension": "ROWS"},
        )

        if not result:
            return []

        rows = result.get("values", [])
        if len(rows) <= 1:
            return []

        headers = rows[0]
        data = []
        for row in rows[1:]:
            item = {}
            for i, h in enumerate(headers):
                item[h] = row[i] if i < len(row) else ""
            data.append(item)

        return data[-limit:] if data else []
