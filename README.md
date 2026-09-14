# Helonx Daily Hot API

一个供个人网站使用的学习型热榜 API，使用 FastAPI 抓取公开页面数据。

## 数据来源

- 百度实时热搜
- V2EX 热门话题
- GitHub Python Trending

只读取无需登录的公开内容；不使用 Cookie、验证码或绕过访问限制。

## 接口

- `GET /`：确认 API 已启动
- `GET /health`：健康检查
- `GET /all`：一次获取全部来源
- `GET /hot/baidu?limit=20`：百度热搜
- `GET /hot/v2ex?limit=20`：V2EX 热门
- `GET /hot/github?limit=20`：GitHub Python Trending

`limit` 可填写 1 到 50，默认 20。

## 本地运行

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload