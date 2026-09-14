# Quizeloop MVP

Quizeloop 是一个把学习文本转成 AI 闯关题的小程序 MVP。当前实现覆盖匿名会话、题库生成、单选/多选/判断作答、服务端判题、奖励、复盘报告、历史与个人统计。

## 目录

- `frontend/`：Taro 4.2.1、React 18、TypeScript、Sass、Zustand。
- `backend/`：FastAPI、SQLAlchemy 2、Alembic、LangChain/LangGraph。
- `ui/`：已确认的 HTML 视觉原型。
- `docs/technical-baseline.md`：官方文档与锁定版本。

## 环境配置

复制根目录 `.env.example` 为 `.env`，填写开发库连接：

```dotenv
DATABASE_URL=mysql+pymysql://user:password@127.0.0.1:3306/quizeloop_dev?charset=utf8mb4
TEST_DATABASE_URL=mysql+pymysql://user:password@127.0.0.1:3306/quizeloop_test?charset=utf8mb4
CLOSEAI_BASE_URL=https://your-closeai-endpoint.example/v1
CLOSEAI_API_KEY=
LLM_MODEL=gpt-5.4
LLM_MODE=auto
```

开发库和测试库必须分离。不要提交 `.env`。无 CloseAI Key 时 `LLM_MODE=auto` 会使用本地 Demo Provider，便于完成整个产品闭环。

## 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

生产和日常开发都应先运行 Alembic，不依赖应用启动自动建表。API 文档位于 `http://127.0.0.1:8000/docs`。

## 前端

```powershell
cd frontend
npm install
$env:TARO_APP_API_BASE='http://127.0.0.1:8000/api/v1'
npm run dev:weapp
```

微信开发者工具导入 `frontend/`，小程序目录配置为 `dist/`。未提供正式 AppID 时可继续使用脚手架的 `touristappid` 做构建验收。请求合法域名需在微信公众平台后台配置；本地调试可在开发者工具中关闭域名校验。

H5 调试使用 `npm run dev:h5`，生产构建使用 `npm run build:h5`。

## 验证

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m mypy app

cd ..\frontend
npm test
npm run typecheck
npm run lint
npm run build:weapp
npm run build:h5
```

真实 CloseAI 冒烟测试与真实 MySQL 集成测试必须使用显式环境配置执行，不混入默认离线测试。

## MVP 边界

本期不实现微信登录、分享海报、真实好友 PK、排行榜、多源解析、联网搜索、RAG、多模态和支付。学习库中的好友 PK 仅显示“暂未开放”。
