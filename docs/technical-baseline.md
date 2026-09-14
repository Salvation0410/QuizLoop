# Quizeloop MVP 技术基线

核验日期：2026-09-14。Context7 在当前环境不可用，以下用法均直接核对官方文档；链接在核验时均返回 HTTP 200。

| 范围 | 锁定版本 | 官方文档 | 项目采用的 API |
| --- | --- | --- | --- |
| Taro | 4.2.1 | https://docs.taro.zone/docs/GETTING-STARTED | `npx @tarojs/cli@4.2.1 init`、React/TypeScript/Sass、`taro build --type weapp/h5` |
| Taro React | 4.2.1 + React 18 | https://docs.taro.zone/docs/react-overall | `@tarojs/components`、页面配置、`Taro.request`、`navigateTo/redirectTo` |
| FastAPI | 0.141.1 | https://fastapi.tiangolo.com/tutorial/testing/ | `FastAPI`、lifespan、依赖注入、`TestClient`、异常处理器 |
| Pydantic Settings | 2.x | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ | `BaseSettings`、`SettingsConfigDict`、`SecretStr` |
| SQLAlchemy | 2.0.52 | https://docs.sqlalchemy.org/en/20/orm/quickstart.html | 2.0 typed declarative、`Mapped`、`mapped_column`、`select` |
| Alembic | 1.20.0 | https://alembic.sqlalchemy.org/en/latest/tutorial.html | `upgrade head`、`downgrade base`、SQLAlchemy metadata |
| LangChain | 1.4.0 | https://docs.langchain.com/oss/python/integrations/chat/openai | `ChatOpenAI`、`ChatPromptTemplate`、`with_structured_output()` |
| LangGraph | 1.2.11 | https://docs.langchain.com/oss/python/langgraph/graph-api | `StateGraph`、`START/END`、条件边、有界重试状态 |

运行时基线为 Node.js 22 LTS、npm 11、Python 3.13。`@tarojs/react@4.2.1` 的官方 peer dependency 为 React `^18`，本项目保持该组合。

CloseAI 只通过环境变量注入 `base_url`、API Key 与模型名。代码和日志不得包含密钥；默认 `LLM_MODE=auto` 在无密钥时使用确定性 Demo Provider，自动化测试不访问外部网络。
