# بوت أخبار الذكاء الاصطناعي — AI News Bot

بوت تيليجرام يجلب آخر أخبار الذكاء الاصطناعي والتقنية بالعربية والإنجليزية، يترجمها تلقائياً، وينشرها يومياً على قناة تيليجرام مع REST API لعرض الأخبار.

---

## المزايا الرئيسية

- **جلب أخبار من مصادر متعددة**: Google News RSS + TechCrunch + Arstechnica + Wired
- **7 تصنيفات أخبار**: الذكاء الاصطناعي، التقنية العالمية، منصات التواصل، تحديثات التطبيقات، صناعة المحتوى، كتابة القصص، أخرى
- **ترجمة تلقائية**: الأخبار الإنجليزية تُترجم إلى العربية باستخدام Google Translate
- **نشر مجمّع**: الأخبار تُرسل على القناة حسب التصنيف مع صور (أصلي + fallback)
- **جدولة يومية**: البث التلقائي كل يوم الساعة 8 صباحاً مع إعادة المحاولة عند الخطأ
- **REST API**: FastAPI يعرض الأخبار المخزنة مع فلترة حسب التصنيف والبحث والكلمات المفتاحية
- **تخزين مؤقت**: الأخبار تُحفظ في ملف JSON
- **Google Sheets**: تسجيل تلقائي للأخبار في جدول بيانات
- **نسخة Docker**: قابل للنشر على أي سيرفر

---

## البنية المعمارية

```
ai-news-bot/
├── main.py              # نقطة الدخول - تشغيل البوت + API معاً
├── api.py               # FastAPI REST API
├── post_now.py          # نشر يدوي فوري
├── run_bot_only.py      # تشغيل البوت فقط
├── requirements.txt     # المكتبات المطلوبة
├── Dockerfile           # حاوية Docker
├── Procfile             # نشر على Heroku
├── .env.example         # قالب إعدادات البيئة
├── .gitignore
└── src/
    ├── __init__.py
    ├── bot.py           # البوت الرئيسي + جلب الأخبار + النشر
    ├── config.py        # قراءة الإعدادات من متغيرات البيئة
    └── sheets_manager.py # تكامل Google Sheets API
```

### الطبقات

- **Bot Layer** (`bot.py`): جلب الأخبار من RSS، التحقق من التواريخ، استخراج الصور OG، الترجمة، النشر على القناة، الجدولة اليومية
- **API Layer** (`api.py`): FastAPI مع CORS، فلترة حسب التصنيف، بحث نصي، إحصائيات
- **Data Layer** (`sheets_manager.py`): Google Sheets API v4 مع حفظ آني للأخبار

---

## التقنيات المستخدمة

| التقنية | الاستخدام |
|---|---|
| Python 3.11+ | لغة البرمجة |
| python-telegram-bot | واجهة Telegram API |
| FastAPI + Uvicorn | REST API |
| BeautifulSoup4 + lxml | تحليل XML/HTML (RSS + OG images) |
| deep-translator | الترجمة من الإنجليزية إلى العربية |
| Google Sheets API | تسجيل الأخبار في جدول بيانات |
| Google News RSS | مصدر الأخبار الأساسي |

---

## التشغيل

### 1. التثبيت

```bash
git clone https://github.com/Alharith380/ai_news-.git
cd ai_news-
python -m venv venv
source venv/bin/activate      # Linux/Mac
pip install -r requirements.txt
```

### 2. الإعداد

أنشئ ملف `.env` واحذف `.env.example`:

```env
TELEGRAM_BOT_TOKEN=توكن_البوت
CHANNEL_ID=-100xxxxxxxxxx     # رمز القناة
BOT_NAME=بوت أخبار الذكاء الاصطناعي
BOT_USERNAME=اسم_البوت_bot
```

### 3. التشغيل

```bash
# تشغيل البوت + API معاً
python main.py

# تشغيل البوت فقط
python run_bot_only.py

# نشر يدوي فوري
python post_now.py

# Docker
docker build -t ai-news-bot .
docker run --env-file .env ai-news-bot
```

### 4. API Endpoints

| الطريقة | المسار | الوصف |
|---|---|---|
| GET | `/` | معلومات النظام |
| GET | `/api/news` | جميع الأخبار |
| GET | `/api/news/latest?limit=5` | آخر أخبار |
| GET | `/api/news/category/{category}` | أخبار حسب التصنيف |
| GET | `/api/news/search?q=keyword` | بحث في الأخبار |
| GET | `/api/categories` | جميع التصنيفات |
| GET | `/api/stats` | إحصائيات |
| GET | `/docs` | توثيق Swagger |

---

## أوامر البوت

| الأمر | الوصف |
|---|---|
| `/start` | مرحباً + رابط القناة |
| `/channel` | نشر الأخبار في القناة فوراً |

---

## ملاحظات

- يُنصح بتشغيل Bot API منفصل على سيرفر لسرعة الإرسال
- الترجمة تعتمد على Google Translate — قد لا تعمل في بعض الدول مباشرةً
- جدولة البث تبدأ بعد الـ 8 صباحاً التالية uptime بدء التشغيل
- حاول البوت فتح الصورة الأصلية للخبر، وإن تعذّر يستخدم صورة التصنيف الافتراضية
