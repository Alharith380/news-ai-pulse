"""Post news to channel immediately with category grouping"""
import asyncio, logging
from telegram import Bot

logging.basicConfig(level=logging.INFO)
import src.sheets_manager
src.sheets_manager.SheetsManager.__init__ = lambda self: (setattr(self, 'creds', None), setattr(self, '_sheet_id', None))
src.sheets_manager.SheetsManager.append_news = lambda self, items: None
src.sheets_manager.SheetsManager.get_recent_news = lambda self, limit: []

from src.bot import NewsFetcher, CATEGORY_IMAGES
from src.config import TELEGRAM_BOT_TOKEN

CHANNEL_ID = -1004371664882

async def main():
    print("=== جلب الأخبار... ===")
    fetcher = NewsFetcher()
    news = await fetcher.fetch_all()
    print(f"تم جلب {len(news)} خبر")

    grouped = {}
    for n in news:
        cat = n.get("category", "أخرى")
        grouped.setdefault(cat, []).append(n)

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    total = 0

    for category, items in grouped.items():
        header = f"📂 *{category}*"
        await bot.send_message(chat_id=CHANNEL_ID, text=header, parse_mode='Markdown')
        await asyncio.sleep(1.5)

        for n in items:
            link_line = f"[🔗 {n['source']}]({n['link']})" if n['link'] else f"🔗 {n['source']}"
            prefix = "🌐 " if n.get("translated") else ""
            caption = f"*{prefix}{n['title']}*\n\n{n['desc']}\n{link_line}"

            img = n.get('img', '')
            if not img or not img.startswith('http'):
                img = CATEGORY_IMAGES.get(n.get('category', ''), CATEGORY_IMAGES["الذكاء الاصطناعي"])

            try:
                await bot.send_photo(chat_id=CHANNEL_ID, photo=img, caption=caption, parse_mode='Markdown')
                print(f"  ✅ {category}: {n['title'][:40]}...")
            except:
                try:
                    cat_img = CATEGORY_IMAGES.get(n.get('category', ''), CATEGORY_IMAGES["الذكاء الاصطناعي"])
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=cat_img, caption=caption, parse_mode='Markdown')
                    print(f"  🖼️ {category}: {n['title'][:40]}... (category img)")
                except:
                    try:
                        await bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode='Markdown')
                        print(f"  📝 {category}: {n['title'][:40]}... (no img)")
                    except:
                        print(f"  ❌ {category}: فشل")

            total += 1
            await asyncio.sleep(3)

    print(f"\n✅ تم نشر {total} خبر في @creatorpr0")

asyncio.run(main())
