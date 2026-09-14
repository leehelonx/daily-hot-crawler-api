import html

import httpx

from app.sources import SourceFetchError

V2EX_HOT_URL = "https://www.v2ex.com/api/topics/hot.json"


def normalize_v2ex_topics(topics: list[dict[str, object]]) -> list[dict[str, object]]:
    """把 V2EX 数据整理成和百度相同的榜单结构。"""
    items = []

    for rank, topic in enumerate(topics, start=1):
        member = topic.get("member") or {}

        items.append(
            {
                "rank": rank,
                "title": topic.get("title", "未命名话题"),
                "url": topic.get("url", "https://www.v2ex.com/"),
                "hot_score": topic.get("replies", 0),
                "description": html.unescape(topic.get("content", "") or ""),
                "author": member.get("username", ""),
            }
        )

    return items


async def fetch_v2ex_hot() -> list[dict[str, object]]:
    """请求 V2EX 公开热门话题接口。"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(V2EX_HOT_URL)
            response.raise_for_status()
            topics = response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise SourceFetchError("V2EX 热门话题暂时无法获取") from error

    if not isinstance(topics, list):
        raise SourceFetchError("V2EX 返回的数据格式异常")

    return normalize_v2ex_topics(topics)
