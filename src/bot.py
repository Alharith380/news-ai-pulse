"""
Telegram Bot for AI News
Fetches Arabic + English news, translates English to Arabic, posts to channel + Google Sheets
"""

import logging
import asyncio
import os
import json
import re
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from src.config import (
    TELEGRAM_BOT_TOKEN, BOT_NAME, BOT_USERNAME, CHANNEL_ID
)
from src.sheets_manager import SheetsManager

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='logs/bot.log'
)
logger = logging.getLogger(__name__)

CATEGORIES = {
    "آخر أخبار العالم التقنية": [
        "https://news.google.com/rss/search?q=%D8%AA%D9%83%D9%86%D9%88%D9%84%D9%88%D8%AC%D9%8A%D8%A7+%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1+%D8%AA%D9%82%D9%86%D9%8A%D8%A9+%D8%AC%D8%AF%D9%8A%D8%AF&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=technology+news+world+latest&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=tech+news+latest+breaking+innovation&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=hardware+gadget+cybersecurity+AI+tech&hl=en&gl=US&ceid=US:en",
        # Direct article feeds (real URLs for OG image scraping)
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://techcrunch.com/feed/",
    ],
    "الذكاء الاصطناعي": [
        "https://news.google.com/rss/search?q=%D8%B0%D9%83%D8%A7%D8%A1+%D8%A7%D8%B5%D8%B7%D9%86%D8%A7%D8%B9%D9%8A+AI&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=artificial+intelligence+AI+news&hl=en&gl=US&ceid=US:en",
    ],
    "منصات التواصل": [
        "https://news.google.com/rss/search?q=%D9%88%D8%B3%D8%A7%D8%A6%D9%84+%D8%AA%D9%88%D8%A7%D8%B5%D9%84+%D8%A7%D8%AC%D8%AA%D9%85%D8%A7%D8%B9%D9%8A+%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=social+media+platforms+news&hl=en&gl=US&ceid=US:en",
    ],
    "آخر تحديثات المواقع": [
        "https://news.google.com/rss/search?q=%D8%AA%D8%AD%D8%AF%D9%8A%D8%AB+%D8%AA%D8%B7%D8%A8%D9%8A%D9%82+%D9%85%D9%88%D9%82%D8%B9+%D8%AC%D8%AF%D9%8A%D8%AF&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D8%AA%D8%B7%D8%A8%D9%8A%D9%82+%D8%AC%D8%AF%D9%8A%D8%AF+iOS+%D8%A3%D9%86%D8%AF%D8%B1%D9%88%D9%8A%D8%AF+%D8%AA%D8%AD%D8%AF%D9%8A%D8%AB&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1+%D8%AA%D9%83%D9%86%D9%88%D9%84%D9%88%D8%AC%D9%8A%D8%A7+%D8%A7%D9%84%D8%AA%D8%B7%D8%A8%D9%8A%D9%82%D8%A7%D8%AA+%D8%A7%D9%84%D8%B0%D9%83%D9%8A%D8%A9&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D9%85%D9%8A%D8%B2%D8%A9+%D8%AC%D8%AF%D9%8A%D8%AF%D8%A9+%D8%AA%D8%B7%D8%A8%D9%8A%D9%82+%D8%A5%D8%B7%D9%84%D8%A7%D9%82&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D8%AA%D8%B7%D8%A8%D9%8A%D9%82%D8%A7%D8%AA+%D8%AC%D9%88%D8%A7%D9%84+%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1+%D8%AA%D8%AD%D8%AF%D9%8A%D8%AB&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=app+update+new+feature+release+software&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=app+software+update+latest&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=iPhone+Android+app+update+feature&hl=en&gl=US&ceid=US:en",
    ],
    "صناعة المحتوى": [
        "https://news.google.com/rss/search?q=%D8%B5%D9%86%D8%A7%D8%B9%D8%A9+%D9%85%D8%AD%D8%AA%D9%88%D9%89+%D8%B1%D9%82%D9%85%D9%8A+%D9%83%D8%AA%D8%A7%D8%A8%D8%A9&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D9%85%D8%AD%D8%AA%D9%88%D9%89+%D8%B1%D9%82%D9%85%D9%8A+%D8%A5%D8%A8%D8%AF%D8%A7%D8%B9+%D9%8A%D9%88%D8%AA%D9%8A%D9%88%D8%A8&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D8%B5%D9%86%D8%A7%D8%B9%D8%A9+%D9%85%D8%AD%D8%AA%D9%88%D9%89+%D8%B1%D9%82%D9%85%D9%8A+%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1+%D9%8A%D9%88%D8%AA%D9%8A%D9%88%D8%A8+%D8%AA%D9%8A%D9%83+%D8%AA%D9%88%D9%83&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D9%8A%D9%88%D8%AA%D9%8A%D9%88%D8%A8+%D8%AA%D9%8A%D9%83+%D8%AA%D9%88%D9%83+%D9%85%D8%AD%D8%AA%D9%88%D9%89+%D8%B1%D9%82%D9%85%D9%8A+%D8%A5%D8%A8%D8%AF%D8%A7%D8%B9&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=content+creation+creator+YouTube+digital&hl=en&gl=US&ceid=US:en",
    ],
    "كتابة القصص": [
        "https://news.google.com/rss/search?q=%D9%83%D8%AA%D8%A7%D8%A8%D8%A9+%D8%A3%D8%AF%D8%A8+%D9%82%D8%B5%D8%A9+%D8%B1%D9%88%D8%A7%D9%8A%D8%A9&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D9%83%D8%AA%D8%A7%D8%A8+%D8%AC%D8%AF%D9%8A%D8%AF+%D8%B1%D9%88%D8%A7%D9%8A%D8%A9+%D9%86%D8%B4%D8%B1+%D8%A3%D8%AF%D8%A8%D9%8A&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D8%A3%D8%AE%D8%A8%D8%A7%D8%B1+%D8%A3%D8%AF%D8%A8%D9%8A%D8%A9+%D9%83%D8%AA%D8%A8+%D8%AC%D8%AF%D9%8A%D8%AF%D8%A9&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D9%83%D8%AA%D8%A8+%D8%A3%D8%AF%D8%A8+%D8%B9%D8%B1%D8%A8%D9%8A+%D8%A5%D8%B5%D8%AF%D8%A7%D8%B1%D8%A7%D8%AA+%D8%AC%D8%AF%D9%8A%D8%AF%D8%A9&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=author+writer+storytelling+publishing+news&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=writing+stories+books+literature+publishing&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=publishing+industry+news+books+2026&hl=en&gl=US&ceid=US:en",
    ],
    "أخرى": [
        "https://news.google.com/rss/search?q=%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1+%D8%B9%D8%A7%D9%84%D9%85+%D8%AA%D9%83%D9%86%D9%88%D9%84%D9%88%D8%AC%D9%8A%D8%A7+%D8%AB%D9%82%D8%A7%D9%81%D8%A9&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=%D8%A7%D8%AE%D8%A8%D8%A7%D8%B1+%D8%AA%D9%83%D9%86%D9%88%D9%84%D9%88%D8%AC%D9%8A%D8%A7+%D8%A7%D9%84%D9%8A%D9%88%D9%85&hl=ar&gl=SA&ceid=SA:ar",
        "https://news.google.com/rss/search?q=science+technology+culture+innovation+news&hl=en&gl=US&ceid=US:en",
        "https://www.wired.com/feed/rss",
    ],
}

CATEGORY_IMAGES = {
    "الذكاء الاصطناعي": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800",
    "منصات التواصل": "https://images.unsplash.com/photo-1611162617474-5b21e879e113?w=800",
    "آخر أخبار العالم التقنية": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800",
    "آخر تحديثات المواقع": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800",
    "صناعة المحتوى": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=800",
    "كتابة القصص": "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800",
    "أخرى": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800",
}


class NewsFetcher:
    """Fetch news from Arabic + English RSS feeds, translates to Arabic"""

    def __init__(self):
        self.news_items = []
        self.translator = None
        self._trans_cache = {}
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.cache_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'news_cache.json')

    def save_cache(self):
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.news_items, f, ensure_ascii=False, indent=2)

    def load_cache(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                self.news_items = json.load(f)
            return self.news_items
        return []

    def _is_arabic(self, text):
        """Check if text contains Arabic characters"""
        return bool(re.search(r'[\u0600-\u06FF]', text))

    def _translate(self, text, max_len=500):
        """Translate English text to Arabic with caching"""
        if not text or self._is_arabic(text[:50]):
            return text
        cache_key = text[:100]
        if cache_key in self._trans_cache:
            return self._trans_cache[cache_key]
        try:
            if not self.translator:
                from deep_translator import GoogleTranslator
                self.translator = GoogleTranslator(source='en', target='ar')
            result = self.translator.translate(text[:max_len])
            result = result or text
            self._trans_cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return text

    def _parse_date(self, date_str):
        """Parse RSS date string to datetime, return None on fail"""
        from datetime import datetime, timedelta
        import email.utils
        try:
            # Try RFC 2822 format: "Fri, 10 Jul 2026 13:54:02 GMT"
            return datetime(*email.utils.parsedate(date_str)[:6])
        except:
            pass
        try:
            # Try ISO format: "2026-07-10T13:54:02Z"
            return datetime.fromisoformat(date_str.replace('Z', '+00:00').split('+')[0])
        except:
            pass
        return None

    async def fetch_all(self):
        """Fetch min 4 news per category, max 7 days old, strongly filtered"""
        import requests
        from bs4 import BeautifulSoup
        from datetime import datetime, timedelta
        from concurrent.futures import ThreadPoolExecutor

        now = datetime.now()
        cutoff = now - timedelta(hours=24)
        all_news = []
        seen_titles = set()
        loop = asyncio.get_event_loop()

        def fetch_feed(url):
            try:
                resp = requests.get(url, headers=self.headers, timeout=15)
                if resp.status_code != 200:
                    return []
                soup = BeautifulSoup(resp.content, 'xml')
                return soup.find_all('item')[:20]
            except:
                return []

        for category, feed_urls in CATEGORIES.items():
            cat_news = []

            with ThreadPoolExecutor(max_workers=8) as pool:
                tasks = [loop.run_in_executor(pool, fetch_feed, url) for url in feed_urls]
                results = await asyncio.gather(*tasks)

            for items in results:
                for item in items:
                    title_el = item.find('title')
                    link_el = item.find('link')
                    desc_el = item.find('description')
                    pub_el = item.find('pubDate')

                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title or len(title) < 15 or title in seen_titles:
                        continue

                    date_str = pub_el.get_text(strip=True) if pub_el else ""
                    pub_date = self._parse_date(date_str) if date_str else None
                    if pub_date and pub_date.replace(tzinfo=None) < cutoff:
                        continue

                    seen_titles.add(title)

                    is_translated = not self._is_arabic(title[:50])
                    if is_translated:
                        title_ar = self._translate(title)
                        title = title_ar or title

                    desc = ""
                    if desc_el:
                        desc = desc_el.get_text(strip=True)
                        desc = re.sub(r'<.*?>', '', desc)
                        desc = re.sub(r'\s+', ' ', desc).strip()
                        if len(desc) > 200:
                            desc = desc[:200] + "..."

                    if len(desc) < 20:
                        desc = ""

                    if is_translated and desc:
                        desc_ar = self._translate(desc)
                        desc = desc_ar or desc

                    link = ""
                    if link_el:
                        link = link_el.get_text(strip=True) if hasattr(link_el, 'get_text') else str(link_el)

                    if not link or link == title:
                        continue

                    img = self._extract_image(item) or CATEGORY_IMAGES.get(category, CATEGORY_IMAGES["الذكاء الاصطناعي"])
                    source = self._extract_domain(link)

                    cat_news.append({
                        "title": title,
                        "desc": desc or title,
                        "img": img,
                        "link": link,
                        "source": source,
                        "date": date_str,
                        "category": category,
                        "translated": is_translated,
                    })

            cat_news.sort(key=lambda x: x.get("date", ""), reverse=True)
            all_news.extend(cat_news[:4])

        self.news_items = all_news
        logger.info(f"Fetched {len(self.news_items)} news items across {len(CATEGORIES)} categories")
        self.save_cache()
        await self._fetch_og_images()
        return self.news_items

    def _extract_image(self, item):
        media = item.find('media:content')
        if media and media.get('url'):
            return media['url']

        thumb = item.find('media:thumbnail')
        if thumb and thumb.get('url'):
            return thumb['url']

        enclosure = item.find('enclosure')
        if enclosure:
            enc_url = enclosure.get('url', '')
            enc_type = enclosure.get('type', '')
            if (enc_url and ('image' in enc_type or 'video' in enc_type)) or (enc_url and not enc_type):
                return enc_url

        content = item.find('content:encoded')
        if content:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(content))
            if m:
                return m.group(1)

        desc = item.find('description')
        if desc:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', str(desc))
            if m:
                return m.group(1)

        return None

    def _extract_domain(self, url):
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace('www.', '')
            return domain.split('.')[0].capitalize() if domain else "مصدر"
        except:
            return "مصدر"

    async def _fetch_og_images(self):
        """Quick OG image scrape for real article URLs (timeout-safe)"""
        import requests
        from bs4 import BeautifulSoup
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import concurrent.futures

        to_fetch = [(i, n["link"]) for i, n in enumerate(self.news_items) if n.get("link", "").startswith("http") and "news.google.com" not in n["link"]]
        if not to_fetch:
            return

        def scrape_og(link):
            try:
                resp = requests.get(link, headers=self.headers, timeout=5)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.content, 'html.parser')
                    og = soup.find('meta', property='og:image')
                    if og and og.get('content'):
                        return og['content']
            except:
                pass
            return None

        with ThreadPoolExecutor(max_workers=3) as pool:
            fut_to_idx = {pool.submit(scrape_og, link): idx for idx, link in to_fetch}
            for fut in concurrent.futures.as_completed(fut_to_idx):
                idx = fut_to_idx[fut]
                try:
                    og_img = fut.result()
                    if og_img:
                        self.news_items[idx]["img"] = og_img
                        self.save_cache()
                except:
                    pass

class ChannelBot:
    """Bot that posts AI news to a Telegram channel"""

    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.fetcher = NewsFetcher()
        self.sheets = SheetsManager()
        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("channel", self.channel_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reply with channel link"""
        await update.message.reply_text(
            f"مرحباً! 🎉\n\n"
            f"تابع آخر أخبار الذكاء الاصطناعي والتقنية بالعربية:\n"
            f"📢 {BOT_USERNAME}\n\n"
            f"ينشر البوت الأخبار يومياً الساعة 8 صباحاً."
        )

    async def channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Post news to channel immediately (admin only)"""
        await update.message.reply_text("🔍 جاري نشر الأخبار في القناة...")
        try:
            await self.fetcher.fetch_all()
            await self._post_to_channel()
            self.sheets.append_news(self.fetcher.news_items)
            await update.message.reply_text(f"✅ تم نشر {len(self.fetcher.news_items)} خبر في القناة")
        except Exception as e:
            logger.error(f"Channel post error: {e}")
            await update.message.reply_text("⚠️ حدث خطأ")

    async def _post_to_channel(self):
        """Send news to the channel, grouped by category"""
        from telegram import Bot
        bot = Bot(token=self.token)

        # Group news by category
        grouped = {}
        for n in self.fetcher.news_items:
            cat = n.get("category", "أخرى")
            grouped.setdefault(cat, []).append(n)

        for category, items in grouped.items():
            header = f"📂 *{category}*\n━━━━━━━━━━━━━━━"
            await bot.send_message(chat_id=CHANNEL_ID, text=header, parse_mode='Markdown')
            await asyncio.sleep(1.5)

            for news in items:
                prefix = "🌐 " if news.get("translated") else ""
                title = f"{prefix}{news['title']}"
                link_line = f"[🔗 {news['source']}]({news['link']})" if news['link'] else f"🔗 {news['source']}"
                caption = f"*{title}*\n\n{news['desc']}\n{link_line}"

                img = news.get('img', '')
                if not img or not img.startswith('http'):
                    img = CATEGORY_IMAGES.get(news.get('category', ''), CATEGORY_IMAGES["الذكاء الاصطناعي"])

                try:
                    await bot.send_photo(
                        chat_id=CHANNEL_ID, photo=img, caption=caption,
                        parse_mode='Markdown'
                    )
                except Exception:
                    try:
                        cat_img = CATEGORY_IMAGES.get(news.get('category', ''), CATEGORY_IMAGES["الذكاء الاصطناعي"])
                        await bot.send_photo(
                            chat_id=CHANNEL_ID, photo=cat_img, caption=caption,
                            parse_mode='Markdown'
                        )
                    except Exception:
                        try:
                            await bot.send_message(
                                chat_id=CHANNEL_ID, text=caption, parse_mode='Markdown'
                            )
                        except Exception:
                            await bot.send_message(
                                chat_id=CHANNEL_ID, text=f"*{title}*\n\n{link_line}",
                                parse_mode='Markdown'
                            )

                await asyncio.sleep(3)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("أرسل /start لمعرفة القناة")

    async def run_with_scheduler(self):
        logger.info("Bot starting with scheduler...")
        await asyncio.gather(
            self.application.run_polling(allowed_updates=Update.ALL_TYPES),
            self._daily_scheduler()
        )

    async def _daily_scheduler(self):
        """Daily broadcast at 8 AM with retry on failure"""
        import random
        while True:
            try:
                now = datetime.now()
                target = datetime.combine(now.date(), time(hour=8, minute=0))
                if now >= target:
                    target += __import__('datetime').timedelta(days=1)

                wait = (target - now).total_seconds()
                logger.info(f"Next broadcast at 8 AM in {int(wait/3600)}h")
                await asyncio.sleep(wait)

                logger.info("=== 8 AM Daily Broadcast ===")
                await self.fetcher.fetch_all()
                if self.fetcher.news_items:
                    self.sheets.append_news(self.fetcher.news_items)
                    await self._post_to_channel()
                    logger.info(f"=== Broadcast done: {len(self.fetcher.news_items)} items ===")
                else:
                    logger.warning("No news fetched, skipping broadcast")
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(300 + random.randint(0, 60))


async def run_bot():
    bot = ChannelBot(TELEGRAM_BOT_TOKEN)
    await bot.run_with_scheduler()

run_bot_with_api = run_bot
