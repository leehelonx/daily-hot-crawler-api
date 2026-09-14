import asyncio
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.sources import SourceFetchError
from app.sources.baidu import fetch_baidu_hot
from app.sources.github import fetch_github_python_trending
from app.sources.v2ex import fetch_v2ex_hot

app = FastAPI(
    title="Helonx Daily Hot API",
    description="A personal hot-list API built with Python.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://leehelonx.github.io",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://172.16.3.8:3000",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)

CACHE_SECONDS = 3600

SOURCES = {
    "baidu": {
        "title": "百度",
        "type": "实时热搜",
        "fetch": fetch_baidu_hot,
    },
    "v2ex": {
        "title": "V2EX",
        "type": "热门话题",
        "fetch": fetch_v2ex_hot,
    },
    "github": {
        "title": "GitHub",
        "type": "Python Trending",
        "fetch": fetch_github_python_trending,
    },
}

_cache = {
    source: {
        "items": [],
        "expires_at": 0.0,
        "fetched_at": None,
    }
    for source in SOURCES
}

_locks = {source: asyncio.Lock() for source in SOURCES}


def now_iso() -> str:
    """返回当前 UTC 时间，写入接口响应。"""
    return datetime.now(timezone.utc).isoformat()


async def get_hot_list(source: str):
    """优先返回缓存；缓存失效后才向来源请求新数据。"""
    cache = _cache[source]
    now = time.monotonic()

    if cache["items"] and now < cache["expires_at"]:
        return cache["items"], True, False, cache["fetched_at"]

    async with _locks[source]:
        now = time.monotonic()

        if cache["items"] and now < cache["expires_at"]:
            return cache["items"], True, False, cache["fetched_at"]

        try:
            items = await SOURCES[source]["fetch"]()
        except SourceFetchError as error:
            if cache["items"]:
                return cache["items"], True, True, cache["fetched_at"]

            raise HTTPException(status_code=502, detail=str(error)) from error

        cache["items"] = items
        cache["expires_at"] = now + CACHE_SECONDS
        cache["fetched_at"] = now_iso()

        return items, False, False, cache["fetched_at"]


@app.get("/")
async def root():
    return {
        "name": "daily-hot-crawler-api",
        "message": "API is running. See /all for available sources.",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/all")
async def all_sources():
    return {
        "code": 200,
        "data": [
            {
                "source": source,
                "title": config["title"],
                "type": config["type"],
                "endpoint": f"/hot/{source}",
            }
            for source, config in SOURCES.items()
        ],
    }


@app.get("/hot/{source}")
async def hot_list(source: str, limit: int = Query(default=20, ge=1, le=50)):
    if source not in SOURCES:
        raise HTTPException(status_code=404, detail="不支持该热榜来源")

    items, cached, stale, fetched_at = await get_hot_list(source)
    config = SOURCES[source]

    return {
        "code": 200,
        "source": source,
        "title": config["title"],
        "type": config["type"],
        "fetched_at": fetched_at,
        "cached": cached,
        "stale": stale,
        "data": items[:limit],
    }
