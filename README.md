# Daily Hot Crawler API

一个用于学习 Python 爬虫与部署的个人热榜接口项目。

## 当前接口

- `GET /`：确认 API 已启动。
- `GET /health`：健康检查。
- `GET /hot/baidu?limit=20`：百度实时热搜，最多返回 50 条。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后可访问 `http://127.0.0.1:8000/docs` 查看接口文档。

## Vercel 部署

Vercel 会识别 `api/index.py` 导出的 FastAPI 应用，并安装 `requirements.txt` 中的依赖。部署后可通过 `/health` 检查服务状态。

## 数据获取原则

- 当前仅低频读取公开展示的百度热搜页面。
- 服务内存缓存 10 分钟，避免每次调用都请求来源网站。
- 不使用登录态、Cookie、验证码或绕过访问校验。
- 页面结构变化时，接口会明确返回失败信息，等待人工修复解析规则。
