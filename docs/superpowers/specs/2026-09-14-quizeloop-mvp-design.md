# Quizeloop MVP 全栈设计规格

## 1. 目标与范围

本期交付一个可运行的微信小程序 MVP，打通以下核心闭环：

1. 匿名用户输入一句话、一段文本或一个学习主题。
2. Python 后端通过 CloseAI 的 OpenAI 兼容接口调用 `gpt-5.4`，生成 5-15 道结构化题目。
3. 小程序支持单选、多选、判断题，提交后立即展示答案和讲解。
4. 完成全部题目后，后端持久化作答、XP 和金币，并生成结构化复盘报告。
5. 学习库和“我的”页面展示当前匿名会话的真实历史统计。

本期不实现微信登录、分享海报、好友 PK、排行榜、联网搜索、网页/视频/文档解析、RAG、多模态和支付。学习库原型中的好友 PK 保留视觉区域，但显示为未开放状态，不提供虚假交互。

## 2. 技术基线

- 前端：Taro 4、React、TypeScript、Taro API、自定义组件与样式。
- 后端：Python 3.11+、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic、MySQL。
- AI 编排：LangChain、`langchain-openai`、LangGraph。
- 测试：pytest、FastAPI TestClient/httpx、数据库隔离、Fake LLM Provider。

开发开始前通过 Context7 查询依赖用法；当前环境未提供 Context7 MCP 资源，因此回退到各项目官方文档。实际安装版本写入锁定文件，密钥和连接串仅通过环境变量注入。

## 3. 代码组织

```text
frontend/
  config/
  src/
    api/
    components/
    pages/index/
    pages/quiz/
    pages/library/
    pages/profile/
    pages/report/
    store/
    styles/
    types/
backend/
  app/
    api/v1/routes/
    core/
    db/
    llm/
    models/
    prompts/
    repositories/
    schemas/
    services/
    main.py
  alembic/
  tests/
ui/
docs/
```

前端只依赖 HTTP 契约，不直接了解 LLM 或数据库。API 层只做校验和错误映射，Service 编排业务，Repository 管理持久化，LLM Provider 隔离 CloseAI/LangChain 细节。

## 4. 前端页面与原型映射

| Taro 页面 | 原型来源 | 实际功能 |
| --- | --- | --- |
| `pages/index/index` | `ui/mobile-home.html` | 文本输入、题量/难度默认值、生成状态、历史未完成关卡 |
| `pages/quiz/index` | `ui/core-flow.html` | 三类题型、进度、即时反馈、讲解、XP/金币 |
| `pages/library/index` | `ui/feature-extensions.html` | 历史题库、错题、掌握度和报告入口；PK 标记未开放 |
| `pages/profile/index` | `ui/profile.html` | 匿名学习档案、累计数据、连续学习和勋章 |
| `pages/report/index` | 延续同一视觉系统 | 正确率、掌握点、薄弱点、三句总结和复习建议 |

颜色、粗描边、硬阴影、圆角、布局密度、顶部 Tag 和底部四栏导航均以 HTML 原型为准。浏览器状态栏和手机外框不复制到真实小程序页面。报告页只补足原型缺失的业务页面，不引入新的视觉语言。

## 5. 核心数据流

### 5.1 匿名会话

首次启动时前端生成并持久化一个随机 `anonymous_id`，每次请求通过请求头传递。后端将其映射到匿名会话。该标识不是认证凭证，不包含个人信息。

### 5.2 生成题库

前端提交文本、题量和难度。后端完成清洗、长度校验和敏感词检查，创建生成任务，通过 LangGraph 执行“构造 Prompt -> 调用模型 -> 结构校验 -> 必要时修复重试 -> 持久化”流程，然后返回题库。

### 5.3 作答

前端根据题库答案本地即时判题并展示讲解，同时记录选择项和用时。全部答完后一次提交整轮记录。后端重新计算正确性，不信任前端传入的 `is_correct`，并以数据库答案为准计算 XP、金币和掌握度。

### 5.4 报告

评分结果先由确定性代码计算正确率、掌握点候选和薄弱点候选，再传入报告链生成总结与建议。报告通过 Schema 校验后持久化并返回；LLM 失败时保留作答事实，允许单独重试报告生成。

## 6. HTTP API

所有接口使用 `/api/v1` 前缀，并返回 `{ code, message, data, request_id }`。

- `GET /health`：服务和数据库健康状态。
- `POST /sessions/anonymous`：创建或恢复匿名会话。
- `POST /quizzes/generate`：生成并保存题库。
- `GET /quizzes/{quiz_id}`：读取题库和进度。
- `POST /quizzes/{quiz_id}/attempts`：提交整轮答案并评分。
- `POST /quizzes/{quiz_id}/report`：生成或重试复盘报告。
- `GET /reports/{report_id}`：读取报告。
- `GET /history/quizzes`：读取历史题库和完成状态。
- `GET /history/stats`：读取学习库和“我的”所需聚合统计。

生成、提交和报告接口接受幂等键，防止网络重试导致重复题库、重复奖励或重复报告。

## 7. 数据模型

MySQL 首版包含以下表：

- `anonymous_sessions`：匿名标识、首次和最后活跃时间。
- `generation_jobs`：任务状态、错误信息、Prompt 版本和模型配置摘要。
- `quizzes`：主题、摘要、原始输入、状态和题量。
- `questions`：题型、题干、答案、讲解、知识点和难度。
- `question_options`：选项键、文本和顺序。
- `attempts`：一次完整闯关及其统计结果。
- `answer_records`：每题选择、用时和后端判定结果。
- `reward_ledger`：XP/金币增减事实和唯一业务键。
- `reports`：结构化报告、生成状态和 Prompt 版本。

外键、唯一约束和事务用于保证一次作答只结算一次奖励。历史统计从事实表聚合，不存储难以校正的重复总数。

## 8. AI 层

`LLMProvider` 暴露生成题库和生成报告两个稳定接口。正式实现使用 `ChatOpenAI(base_url, api_key, model)`、`ChatPromptTemplate` 和 `with_structured_output()`；测试实现使用确定性的 Fake Provider。

LangGraph 只编排有限状态流程，不承载数据库模型或 HTTP 逻辑。题库校验包括题量、ID 唯一、题型、选项数、答案属于选项、判断题格式、讲解非空和难度枚举。失败最多重试两次，之后返回可识别的业务错误。

## 9. 错误与安全

- 输入为空、过长或命中敏感规则时返回明确的 4xx 业务错误。
- 模型超时、限流、空响应和结构异常映射为可重试错误，不回传供应商细节。
- 数据库异常回滚事务，并通过 `request_id` 关联结构化日志。
- CORS 仅在本地开发开放明确来源；生产配置不使用通配符。
- 日志不记录 API Key、完整连接串或超长用户原文。
- 正确答案仍会下发以支持即时判题，这是 MVP 的明确取舍；后端结算时必须独立复算。

## 10. TDD 与验证

后端每个能力按“失败测试 -> 最小实现 -> 重构”推进。测试分层如下：

1. 单元测试：文本清洗、题库 Schema、评分、奖励、统计和 Prompt 契约。
2. Service 测试：Fake Provider 下的生成、重试、报告和异常路径。
3. Repository 测试：MySQL 测试库中的约束、事务和聚合查询。
4. API 测试：成功、校验失败、幂等、越权式 ID 访问和服务异常。
5. 真实模型冒烟：仅在显式提供 CloseAI 环境变量时运行，不计入默认单元测试。

前端执行 TypeScript 检查、Lint、构建和关键状态逻辑测试。最终通过微信小程序构建与 H5 手机视口逐页对照原型，检查中文、溢出、导航、加载、空态和错误态。

## 11. 实施顺序与完成标准

1. 锁定官方文档和依赖版本，初始化工程。
2. 先写测试并完成配置、数据库、迁移和健康检查。
3. 以 Fake Provider 完成出题、评分、奖励、报告和历史接口。
4. 接入 CloseAI 的 LangChain/LangGraph 正式 Provider。
5. 按原型实现五个 Taro 页面和共享组件。
6. 完成真实 API 联调和异常态。
7. 运行完整后端测试、前端检查、微信构建和视觉验收。

完成标准：核心闭环可从首页连续操作到报告页；刷新后匿名历史仍可恢复；三种题型均正确评分；奖励不重复；四个原型页面展示真实数据；默认测试不依赖外网且全部通过；缺少密钥时应用给出清晰配置错误而不是启动崩溃。
