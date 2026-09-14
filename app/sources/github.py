import httpx
from bs4 import BeautifulSoup

from app.sources import SourceFetchError

GITHUB_TRENDING_URL = "https://github.com/trending/python?since=daily"


def parse_github_trending(page: str) -> list[dict[str, object]]:
    """从 GitHub Python Trending 页面提取项目列表。"""
    soup = BeautifulSoup(page, "html.parser")
    items = []

    for rank, article in enumerate(soup.select("article.Box-row"), start=1):
        repo_link = article.select_one("h2 a")

        if not repo_link or not repo_link.get("href"):
            continue

        description = article.select_one("p")
        stars = article.select_one('a[href$="/stargazers"]')
        language = article.select_one('[itemprop="programmingLanguage"]')

        items.append(
            {
                "rank": rank,
                "title": " ".join(repo_link.get_text(" ", strip=True).split()),
                "url": f"https://github.com{repo_link['href']}",
                "hot_score": stars.get_text(" ", strip=True) if stars else "",
                "description": description.get_text(" ", strip=True)
                if description
                else "",
                "author": language.get_text(" ", strip=True) if language else "Python",
            }
        )

    if not items:
        raise SourceFetchError("GitHub Trending 页面结构已变化")

    return items


async def fetch_github_python_trending() -> list[dict[str, object]]:
    """请求 GitHub 的 Python 今日趋势页面。"""
    headers = {
        "User-Agent": "HelonxDailyHot/0.2 (+https://leehelonx.github.io)",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            response = await client.get(GITHUB_TRENDING_URL)
            response.raise_for_status()
    except httpx.HTTPError as error:
        raise SourceFetchError("GitHub Python Trending 暂时无法获取") from error

    return parse_github_trending(response.text)
