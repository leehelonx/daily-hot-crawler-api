import json
import re

import httpx

from app.sources import SourceFetchError

BAIDU_HOT_URL = "https://top.baidu.com/board?tab=realtime"


def parse_baidu_hot(page: str) -> list[dict[str, object]]:
    """把百度网页内容解析为统一的热榜数据。"""
    match = re.search(r"<!--s-data:(\{.*?\})-->", page, re.S)

    if not match:
        raise SourceFetchError("百度热搜页面结构已变化")

    try:
        payload = json.loads(match.group(1))
        cards = payload["data"]["cards"]
        content = next(
            card["content"] for card in cards if card.get("component") == "hotList"
        )
    except (KeyError, StopIteration, json.JSONDecodeError) as error:
        raise SourceFetchError("百度热搜数据解析失败") from error

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


async def fetch_baidu_hot() -> list[dict[str, object]]:
    """请求公开百度热搜页面，并返回整理后的榜单。"""
    headers = {
        "User-Agent": "HelonxDailyHot/0.2 (+https://leehelonx.github.io)",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            response = await client.get(BAIDU_HOT_URL)
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise SourceFetchError("百度热搜暂时无法获取") from error

    return parse_baidu_hot(response.text)
