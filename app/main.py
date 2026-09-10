import asyncio
import json
import re
import time
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Daily Hot Crawler API",
    description="A personal hot-list API built with Python.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://leehelonx.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

BAIDU_HOT_URL = "https://top.baidu.com/board?tab=realtime"
CACHE_SECONDS = 600
_cache: dict[str, object] = {"items": [], "expires_at": 0.0, "fetched_at": None}
_cache_lock = asyncio.Lock()


async def fetch_baidu_hot() -> list[dict[str, object]]:
    """Fetch and normalize public items from Baidu's realtime hot board."""
    headers = {
        "User-Agent": "HelonxDailyHot/0.1 (+https://leehelonx.github.io)",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            response = await client.get(BAIDU_HOT_URL)
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise HTTPException(status_code=502, detail="百度热搜暂时无法获取") from error

    match = re.search(r"<!--s-data:(\{.*?\})-->", response.text, re.S)
    if not match:
        raise HTTPException(status_code=502, detail="百度热搜页面结构已变化")

    try:
        payload = json.loads(match.group(1))
        cards = payload["data"]["cards"]
        content = next(card["content"] for card in cards if card.get("component") == "hotList")
    except (KeyError, StopIteration, json.JSONDecodeError) as error:
        raise HTTPException(status_code=502, detail="百度热搜数据解析失败") from error

    return [
        {
            "rank": rank,
            "title": item["word"],
            "url": item["url"],
            "hot_score": item.get("hotScore"),
            "description": item.get("desc", ""),
        }
        for rank, item in enumerate(content, start=1)
    ]


async def get_baidu_hot() -> tuple[list[dict[str, object]], bool, str]:
    now = time.monotonic()
    cached_items = _cache["items"]
    if cached_items and now < float(_cache["expires_at"]):
        return cached_items, True, str(_cache["fetched_at"])

    async with _cache_lock:
        now = time.monotonic()
        cached_items = _cache["items"]
        if cached_items and now < float(_cache["expires_at"]):
            return cached_items, True, str(_cache["fetched_at"])

        items = await fetch_baidu_hot()
        _cache["items"] = items
        _cache["expires_at"] = now + CACHE_SECONDS
        _cache["fetched_at"] = datetime.now(timezone.utc).isoformat()
        return items, False, str(_cache["fetched_at"])


@app.get("/")
async def root():
    return {
        "name": "daily-hot-crawler-api",
        "message": "API is running. Baidu hot search is available at /hot/baidu.",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/hot/baidu")
async def baidu_hot(limit: int = Query(default=20, ge=1, le=50)):
    """Return a cached subset of Baidu realtime hot-search items."""
    items, cached, fetched_at = await get_baidu_hot()
    return {
        "source": "baidu",
        "fetched_at": fetched_at,
        "cached": cached,
        "data": items[:limit],
    }
