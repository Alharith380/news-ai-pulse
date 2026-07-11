"""
FastAPI REST API for AI News Bot
Serves cached news from JSON file with filtering
"""

import logging
import os
import json
from datetime import datetime

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

CACHE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'news_cache.json')

app = FastAPI(
    title="AI News Bot API",
    description="أخبار الذكاء الاصطناعي والتقنية - API لجلب الأخبار",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_news():
    try:
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Cache read error: {e}")
    return []


@app.get("/")
def root():
    return {
        "status": "ok",
        "bot": "AI News Bot",
        "version": "1.0.0",
        "endpoints": {
            "all_news": "/api/news",
            "latest": "/api/news/latest?limit=5",
            "by_category": "/api/news/category/{category}",
            "search": "/api/news/search?q=keyword",
            "categories": "/api/categories",
            "stats": "/api/stats",
            "docs": "/docs",
        },
    }


@app.get("/api/news")
def get_all_news():
    news = load_news()
    return {"success": True, "count": len(news), "news": news}


@app.get("/api/news/latest")
def get_latest_news(limit: int = Query(default=5, ge=1, le=50)):
    news = load_news()
    return {"success": True, "count": min(limit, len(news)), "news": news[:limit]}


@app.get("/api/news/category/{category}")
def get_news_by_category(category: str):
    news = load_news()
    filtered = [n for n in news if n.get("category", "") == category]
    return {"success": True, "count": len(filtered), "category": category, "news": filtered}


@app.get("/api/news/search")
def search_news(q: str = Query(default="", min_length=1)):
    news = load_news()
    q = q.lower()
    filtered = [
        n for n in news
        if q in n.get("title", "").lower() or q in n.get("desc", "").lower()
    ]
    return {"success": True, "count": len(filtered), "query": q, "news": filtered}


@app.get("/api/categories")
def get_categories():
    news = load_news()
    cats = {}
    for n in news:
        cat = n.get("category", "أخرى")
        if cat not in cats:
            cats[cat] = {"name": cat, "count": 0}
        cats[cat]["count"] += 1
    return {"success": True, "categories": list(cats.values())}


@app.get("/api/stats")
def get_stats():
    news = load_news()
    cats = {}
    for n in news:
        cat = n.get("category", "أخرى")
        cats[cat] = cats.get(cat, 0) + 1
    mtime = None
    if os.path.exists(CACHE_PATH):
        mtime = datetime.fromtimestamp(os.path.getmtime(CACHE_PATH)).isoformat()
    return {
        "success": True,
        "total_news": len(news),
        "categories": cats,
        "last_update": mtime,
    }
