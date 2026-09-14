# Quizeloop MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested Taro WeChat mini-program and FastAPI/MySQL backend that turns text into an AI-generated quiz, scores an anonymous attempt, produces a review report, and restores real history statistics.

**Architecture:** A Taro React client consumes a versioned FastAPI contract. FastAPI separates API, service, repository, and LLM provider responsibilities; MySQL stores facts, while LangChain/LangGraph orchestrate bounded structured-output workflows through CloseAI. Backend behavior is developed test-first with a deterministic fake provider, and real model calls are opt-in smoke tests.

**Tech Stack:** Taro 4, React, TypeScript, Zustand, Vitest; Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic, PyMySQL, LangChain, LangGraph, pytest, testcontainers/MySQL.

---

## File Map

```text
frontend/
  config/{index,dev,prod}.ts                 Taro build configuration
  src/api/{client,quiz,history}.ts           HTTP transport and endpoint wrappers
  src/components/{AppHeader,PageTabs,BottomNav}.tsx
  src/pages/{index,quiz,library,profile,report}/
  src/store/{session,quiz}.ts                Anonymous identity and active run
  src/styles/{tokens,global}.scss            Values extracted from ui/*.html
  src/types/api.ts                           API contract types
backend/
  app/api/v1/routes/{health,sessions,quizzes,reports,history}.py
  app/core/{config,errors,responses}.py
  app/db/{base,session}.py
  app/domain/{enums,scoring}.py
  app/llm/{base,factory,graphs,schemas}.py
  app/models/{session,quiz,attempt,report}.py
  app/prompts/{quiz_v1,report_v1}.py
  app/repositories/{sessions,quizzes,attempts,reports,history}.py
  app/schemas/{common,session,quiz,attempt,report,history}.py
  app/services/{sessions,quiz,attempt,report,history}.py
  alembic/versions/0001_initial.py
  tests/{unit,service,repository,api,smoke}/
```

## Task 1: Verify Official APIs and Lock the Toolchain

**Files:**
- Create: `docs/technical-baseline.md`
- Create: `backend/pyproject.toml`
- Create: `.nvmrc`
- Create: `.python-version`

- [ ] **Step 1: Query primary documentation**

Read the current official Taro React quick start/config/routing/request pages, LangChain `ChatOpenAI` and structured-output pages, LangGraph StateGraph page, FastAPI testing/lifespan pages, Pydantic settings page, and SQLAlchemy asyncio/Alembic pages. Record the URL, access date, selected package version, and the exact API used in `docs/technical-baseline.md`. Context7 is not configured in this environment, so do not rely on secondary tutorials.

- [ ] **Step 2: Verify package compatibility without installing globally**

Run:

```powershell
npm view @tarojs/cli version peerDependencies --json
npm view @tarojs/react version peerDependencies --json
python -m pip index versions fastapi
python -m pip index versions langchain
python -m pip index versions langgraph
python -m pip index versions sqlalchemy
```

Expected: each command exits `0`; selected versions are mutually compatible and are written exactly into the two manifests.

- [ ] **Step 3: Define runtime baselines**

Write Node's selected LTS major into `.nvmrc` and `3.11` into `.python-version`. Add runtime and test dependency groups to `backend/pyproject.toml`. Do not create `frontend/package.json` manually; Task 12 must obtain it from the official Taro scaffold.

- [ ] **Step 4: Commit the baseline**

```powershell
git add docs/technical-baseline.md backend/pyproject.toml .nvmrc .python-version
git commit -m "build: lock Quizeloop MVP toolchain"
```

## Task 2: Scaffold the Backend and Health Contract

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/api/v1/router.py`
- Create: `backend/app/api/v1/routes/health.py`
- Create: `backend/app/schemas/common.py`
- Create: `backend/tests/api/test_health.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write the failing health test**

```python
def test_health_returns_envelope(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["code"] == 0
    assert response.json()["data"]["status"] == "ok"
    assert response.json()["request_id"]
```

- [ ] **Step 2: Prove the test is red**

Run: `cd backend; python -m pytest tests/api/test_health.py -q`

Expected: FAIL because `backend.app.main` does not exist.

- [ ] **Step 3: Implement the minimum app**

Create `create_app() -> FastAPI`, mount a router at `/api/v1`, add request-ID middleware, and return `ApiResponse[HealthData](code=0, message="ok", data={"status": "ok"}, request_id=...)`.

- [ ] **Step 4: Prove the test is green**

Run: `cd backend; python -m pytest tests/api/test_health.py -q`

Expected: `1 passed`.

- [ ] **Step 5: Commit**

```powershell
git add backend/app backend/tests
git commit -m "feat(backend): add FastAPI health contract"
```

## Task 3: Configuration, Errors, and Database Session

**Files:**
- Create: `.env.example`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/errors.py`
- Create: `backend/app/core/responses.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/tests/unit/test_config.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Write failing configuration tests**

```python
def test_settings_accept_closeai_and_mysql(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+pymysql://app:pass@localhost/quizeloop")
    monkeypatch.setenv("CLOSEAI_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("CLOSEAI_API_KEY", "test-key")
    settings = Settings(_env_file=None)
    assert settings.llm_model == "gpt-5.4"
    assert settings.llm_timeout_seconds == 30
```

Also test that secrets are excluded from `repr(settings)` and that missing model credentials do not prevent health-only startup.

- [ ] **Step 2: Run red test**

Run: `cd backend; python -m pytest tests/unit/test_config.py -q`

Expected: FAIL because `Settings` is undefined.

- [ ] **Step 3: Implement settings and session factory**

Use `BaseSettings` with `env_prefix=""`, `SecretStr` for the API key, explicit `database_url`, `cors_origins`, model, timeout and retry fields. Expose `create_engine_from_settings()` and `get_db()`; no connection is opened at module import time.

- [ ] **Step 4: Run tests and commit**

Run: `cd backend; python -m pytest tests/unit/test_config.py tests/api/test_health.py -q`

Expected: all tests pass.

```powershell
git add .env.example backend/app/core backend/app/db backend/tests
git commit -m "feat(backend): add validated runtime configuration"
```

## Task 4: Model the MySQL Facts and Initial Migration

**Files:**
- Create: `backend/app/domain/enums.py`
- Create: `backend/app/models/session.py`
- Create: `backend/app/models/quiz.py`
- Create: `backend/app/models/attempt.py`
- Create: `backend/app/models/report.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial.py`
- Create: `backend/tests/repository/test_schema.py`

- [ ] **Step 1: Write a failing schema integration test**

```python
def test_reward_business_key_is_unique(db_session, persisted_attempt):
    db_session.add(RewardLedger(attempt_id=persisted_attempt.id, kind="xp", amount=12))
    db_session.commit()
    db_session.add(RewardLedger(attempt_id=persisted_attempt.id, kind="xp", amount=12))
    with pytest.raises(IntegrityError):
        db_session.commit()
```

The repository suite runs against a disposable MySQL database supplied by `TEST_DATABASE_URL` or Testcontainers.

- [ ] **Step 2: Run red test**

Run: `cd backend; python -m pytest tests/repository/test_schema.py -q`

Expected: FAIL because the models and migration do not exist.

- [ ] **Step 3: Implement models and migration**

Create all nine tables from the design spec. Use UUID strings, UTC timestamps, JSON columns only for selected-answer arrays/report list fields, normalized question options, indexed foreign keys, cascade rules, and a unique constraint on `(attempt_id, kind)` in `reward_ledger`.

- [ ] **Step 4: Apply and reverse the migration**

```powershell
cd backend
python -m alembic upgrade head
python -m alembic downgrade base
python -m alembic upgrade head
python -m pytest tests/repository/test_schema.py -q
```

Expected: migration commands exit `0`; schema tests pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/models backend/app/domain backend/alembic.ini backend/alembic backend/tests/repository
git commit -m "feat(backend): add MVP persistence schema"
```

## Task 5: Anonymous Session API

**Files:**
- Create: `backend/app/schemas/session.py`
- Create: `backend/app/repositories/sessions.py`
- Create: `backend/app/services/sessions.py`
- Create: `backend/app/api/v1/routes/sessions.py`
- Create: `backend/tests/api/test_sessions.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Write failing API tests**

```python
def test_create_then_restore_anonymous_session(client):
    first = client.post("/api/v1/sessions/anonymous", json={"anonymous_id": "anon_test_123"})
    second = client.post("/api/v1/sessions/anonymous", json={"anonymous_id": "anon_test_123"})
    assert first.status_code == second.status_code == 200
    assert first.json()["data"]["session_id"] == second.json()["data"]["session_id"]
```

Also test invalid length/characters and that `last_active_at` advances.

- [ ] **Step 2: Run red, implement, run green**

Run: `cd backend; python -m pytest tests/api/test_sessions.py -q`

Expected before implementation: 404. Implement repository upsert and service validation, then rerun and expect all tests to pass.

- [ ] **Step 3: Commit**

```powershell
git add backend/app backend/tests/api/test_sessions.py
git commit -m "feat(backend): persist anonymous learning sessions"
```

## Task 6: Quiz Schemas, Validation, and Fake Provider

**Files:**
- Create: `backend/app/schemas/quiz.py`
- Create: `backend/app/llm/base.py`
- Create: `backend/app/llm/schemas.py`
- Create: `backend/tests/unit/test_quiz_schema.py`
- Create: `backend/tests/fakes/fake_llm.py`

- [ ] **Step 1: Write failing contract tests**

```python
def test_multiple_choice_answer_must_reference_options():
    with pytest.raises(ValidationError):
        QuestionOutput(
            id="q1", type="multiple", stem="Choose", options=[{"key": "A", "text": "A"}],
            answer=["B"], explanation="Reason", knowledge_point="Point", difficulty="easy"
        )
```

Cover unique question IDs, 5-15 question count, single-answer cardinality, multiple-answer cardinality, judge options, nonempty explanation, and difficulty enum.

- [ ] **Step 2: Run red, implement Pydantic validators, run green**

Run: `cd backend; python -m pytest tests/unit/test_quiz_schema.py -q`

Expected after implementation: all contract tests pass.

- [ ] **Step 3: Add a deterministic provider interface**

Define `LLMProvider.generate_quiz(request) -> QuizOutput` and `generate_report(context) -> ReportOutput` as async protocol methods. Fake provider accepts queued results or exceptions so service tests can assert retries without network access.

- [ ] **Step 4: Commit**

```powershell
git add backend/app/schemas/quiz.py backend/app/llm backend/tests/unit backend/tests/fakes
git commit -m "feat(backend): define structured quiz contract"
```

## Task 7: TDD the Quiz Generation Service and API

**Files:**
- Create: `backend/app/repositories/quizzes.py`
- Create: `backend/app/services/quiz.py`
- Create: `backend/app/api/v1/routes/quizzes.py`
- Create: `backend/tests/service/test_quiz_service.py`
- Create: `backend/tests/api/test_quizzes.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Write failing service tests**

```python
async def test_generate_quiz_retries_one_invalid_result(fake_provider, quiz_service):
    fake_provider.queue_invalid_result()
    fake_provider.queue_valid_quiz(question_count=5)
    quiz = await quiz_service.generate(valid_request)
    assert len(quiz.questions) == 5
    assert fake_provider.generate_quiz_calls == 2
```

Test input cleaning, sensitive-rule rejection, max two retries, persisted failed job, successful quiz persistence, and identical idempotency key returning the same quiz.

- [ ] **Step 2: Run red, implement service/repository, run green**

Run: `cd backend; python -m pytest tests/service/test_quiz_service.py -q`

Expected after implementation: all service tests pass without network access.

- [ ] **Step 3: Write and satisfy API tests**

Assert `POST /api/v1/quizzes/generate` returns the envelope, 422 for invalid counts, a stable business error for blocked input/model failure, and the same `quiz_id` on an idempotent retry.

Run: `cd backend; python -m pytest tests/api/test_quizzes.py -q`

Expected: all API tests pass.

- [ ] **Step 4: Commit**

```powershell
git add backend/app backend/tests/service/test_quiz_service.py backend/tests/api/test_quizzes.py
git commit -m "feat(backend): generate and persist quiz sets"
```

## Task 8: TDD Scoring, Attempts, and Rewards

**Files:**
- Create: `backend/app/schemas/attempt.py`
- Create: `backend/app/domain/scoring.py`
- Create: `backend/app/repositories/attempts.py`
- Create: `backend/app/services/attempt.py`
- Create: `backend/tests/unit/test_scoring.py`
- Create: `backend/tests/service/test_attempt_service.py`
- Modify: `backend/app/api/v1/routes/quizzes.py`

- [ ] **Step 1: Write failing scoring tests**

```python
@pytest.mark.parametrize(
    ("correct", "selected", "expected"),
    [(["A"], ["A"], True), (["A", "C"], ["C", "A"], True), (["A", "C"], ["A"], False)],
)
def test_answers_are_scored_as_sets(correct, selected, expected):
    assert is_correct_answer(correct, selected) is expected
```

Also test duplicate selections, unknown keys, judge questions, duration bounds, XP/coin totals, and zero reward for incorrect answers.

- [ ] **Step 2: Run red, implement scoring, run green**

Run: `cd backend; python -m pytest tests/unit/test_scoring.py -q`

Expected after implementation: all scoring tests pass.

- [ ] **Step 3: Test transactional submission**

Prove the service ignores client correctness, requires every quiz question exactly once, writes attempt/answers/rewards atomically, and returns the existing result for the same idempotency key.

Run: `cd backend; python -m pytest tests/service/test_attempt_service.py -q`

Expected after implementation: all attempt tests pass.

- [ ] **Step 4: Commit**

```powershell
git add backend/app backend/tests/unit/test_scoring.py backend/tests/service/test_attempt_service.py
git commit -m "feat(backend): score attempts and settle rewards"
```

## Task 9: TDD Report Generation

**Files:**
- Create: `backend/app/schemas/report.py`
- Create: `backend/app/repositories/reports.py`
- Create: `backend/app/services/report.py`
- Create: `backend/app/api/v1/routes/reports.py`
- Create: `backend/tests/service/test_report_service.py`
- Create: `backend/tests/api/test_reports.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Write failing report tests**

```python
async def test_report_context_uses_server_scoring(report_service, fake_provider, persisted_attempt):
    report = await report_service.generate(persisted_attempt.quiz_id, persisted_attempt.session_id)
    assert report.accuracy == persisted_attempt.accuracy
    assert fake_provider.last_report_context.weak_points
```

Test report ownership, missing/incomplete attempts, deterministic accuracy, schema failure retry, failed-state persistence, retry after model failure, and idempotency.

- [ ] **Step 2: Run red, implement, run green**

Run: `cd backend; python -m pytest tests/service/test_report_service.py tests/api/test_reports.py -q`

Expected after implementation: all report tests pass.

- [ ] **Step 3: Commit**

```powershell
git add backend/app backend/tests/service/test_report_service.py backend/tests/api/test_reports.py
git commit -m "feat(backend): generate structured review reports"
```

## Task 10: TDD History and Profile Statistics

**Files:**
- Create: `backend/app/schemas/history.py`
- Create: `backend/app/repositories/history.py`
- Create: `backend/app/services/history.py`
- Create: `backend/app/api/v1/routes/history.py`
- Create: `backend/tests/api/test_history.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Write failing aggregate tests**

Seed two completed attempts and one unfinished quiz. Assert history order, completion status, total questions, average accuracy, XP, coins, streak dates, knowledge-point mastery, weak questions, and report links.

- [ ] **Step 2: Run red, implement queries, run green**

Run: `cd backend; python -m pytest tests/api/test_history.py -q`

Expected after implementation: all history tests pass and no aggregate value is hard-coded.

- [ ] **Step 3: Run the complete backend suite**

Run: `cd backend; python -m pytest -q`

Expected: all tests pass with no external network calls.

- [ ] **Step 4: Commit**

```powershell
git add backend/app backend/tests/api/test_history.py
git commit -m "feat(backend): expose anonymous learning history"
```

## Task 11: Implement the Official LangChain/LangGraph Provider

**Files:**
- Create: `backend/app/llm/factory.py`
- Create: `backend/app/llm/graphs.py`
- Create: `backend/app/prompts/quiz_v1.py`
- Create: `backend/app/prompts/report_v1.py`
- Create: `backend/tests/unit/test_prompt_contracts.py`
- Create: `backend/tests/smoke/test_closeai.py`

- [ ] **Step 1: Write prompt and graph contract tests**

Assert prompts contain every input variable, graph results are validated Pydantic objects, retries stop after the configured count, and no API key appears in serialized graph state or exception messages.

- [ ] **Step 2: Implement from the recorded official APIs**

Create `ChatOpenAI(model=settings.llm_model, base_url=settings.closeai_base_url, api_key=settings.closeai_api_key, timeout=settings.llm_timeout_seconds, max_retries=0)`. Bind `with_structured_output(QuizOutput)` and `with_structured_output(ReportOutput)`. Build bounded StateGraphs with call, validate, retry, persist-result/error terminal states.

- [ ] **Step 3: Run offline tests**

Run: `cd backend; python -m pytest tests/unit/test_prompt_contracts.py tests/service -q`

Expected: all pass without CloseAI credentials.

- [ ] **Step 4: Run opt-in smoke tests when credentials exist**

Run: `cd backend; python -m pytest tests/smoke/test_closeai.py -m live_llm -q`

Expected: one 5-question quiz and one report validate against their schemas. If credentials are absent, the test skips with a clear reason.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/llm backend/app/prompts backend/tests/unit/test_prompt_contracts.py backend/tests/smoke
git commit -m "feat(backend): connect CloseAI quiz workflows"
```

## Task 12: Generate the Taro Project and Reproduce the Shared Visual System

**Files:**
- Generate with Taro CLI: `frontend/package.json`
- Generate with Taro CLI: `frontend/config/index.ts`
- Generate with Taro CLI: `frontend/src/app.config.ts`
- Generate with Taro CLI: `frontend/src/app.tsx`
- Generate with Taro CLI: `frontend/src/app.scss`
- Modify: `frontend/package.json`
- Create: `frontend/src/styles/tokens.scss`
- Create: `frontend/src/components/AppHeader.tsx`
- Create: `frontend/src/components/PageTabs.tsx`
- Create: `frontend/src/components/BottomNav.tsx`
- Create: `frontend/src/components/navigation.scss`
- Create: `frontend/src/components/__tests__/navigation.test.tsx`

- [ ] **Step 1: Generate the initial code with the official Taro scaffold**

Run the version selected in Task 1 without installing a global CLI:

```powershell
$taroCliVersion = (npm view @tarojs/cli version).Trim()
npx "@tarojs/cli@$taroCliVersion" init frontend
```

Before running `init`, verify that `$taroCliVersion` equals the version recorded in `docs/technical-baseline.md`. At the official interactive prompts select: npm package manager, React framework, TypeScript, Sass, the default application template, and WeChat mini-program support. Keep the scaffold-generated `config/`, `src/app.*`, Babel/TypeScript configuration, project configuration and Taro dependency versions.

Run:

```powershell
cd frontend
npm install
npm run build:weapp
```

Expected: dependencies install successfully and the untouched scaffold builds a WeChat mini-program once before customization.

- [ ] **Step 2: Add the frontend quality scripts**

Add compatible test dependencies and scripts `dev:weapp`, `dev:h5`, `build:weapp`, `build:h5`, `typecheck`, `lint`, and `test` to the scaffold-generated manifest. Preserve the Taro package versions selected by the scaffold.

- [ ] **Step 3: Write failing navigation tests**

Render each route and assert exactly four labels (`首页`, `闯关`, `学习库`, `我的`), one active item, and Taro navigation calls targeting the correct pages.

- [ ] **Step 4: Run red test**

Run: `cd frontend; npm test -- navigation.test.tsx`

Expected: FAIL because components do not exist.

- [ ] **Step 5: Implement shared shell from the HTML prototypes**

Extract the exact palette (`#24232c`, `#fff8e8`, `#ff725c`, `#ffd447`, `#9bdcff`, `#c7f36b`, `#ffb6d9`), border widths, hard shadows, type sizes, spacing, and active-tab rotation. Use Taro `View`, `Text`, `Button` and navigation APIs; do not reproduce the browser phone frame/status bar.

- [ ] **Step 6: Run tests/build and commit**

```powershell
cd frontend
npm run typecheck
npm test -- navigation.test.tsx
npm run build:weapp
git add frontend
git commit -m "feat(frontend): add Taro mini-program shell"
```

Expected: all commands exit `0`.

## Task 13: API Client, Anonymous Session, and Quiz Store

**Files:**
- Create: `frontend/src/types/api.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/quiz.ts`
- Create: `frontend/src/api/history.ts`
- Create: `frontend/src/store/session.ts`
- Create: `frontend/src/store/quiz.ts`
- Create: `frontend/src/api/__tests__/client.test.ts`

- [ ] **Step 1: Write failing client tests**

Mock `Taro.request` and `Taro.getStorageSync`. Assert base URL configuration, anonymous header, request ID handling, envelope unwrapping, timeout message, business error preservation, and no automatic retry of non-idempotent requests without an idempotency key.

- [ ] **Step 2: Run red, implement, run green**

Run: `cd frontend; npm test -- client.test.ts`

Expected after implementation: all client tests pass.

- [ ] **Step 3: Commit**

```powershell
git add frontend/src/api frontend/src/store frontend/src/types
git commit -m "feat(frontend): add typed API and anonymous session"
```

## Task 14: Build the Home Page from `ui/mobile-home.html`

**Files:**
- Create: `frontend/src/pages/index/index.config.ts`
- Create: `frontend/src/pages/index/index.tsx`
- Create: `frontend/src/pages/index/index.scss`
- Create: `frontend/src/pages/index/__tests__/index.test.tsx`

- [ ] **Step 1: Write failing behavior tests**

Assert empty input is rejected, valid input disables the button and shows `AI 正在整理知识点…`, success stores the quiz and navigates to `/pages/quiz/index`, failure exposes retry, and unfinished history cards use API data.

- [ ] **Step 2: Run red, implement page, run green**

Run: `cd frontend; npm test -- pages/index`

Implement the exact hero, input card, coral action button, unfinished-course rows, progress circles, top tabs and bottom navigation from the prototype.

- [ ] **Step 3: Commit**

```powershell
git add frontend/src/pages/index
git commit -m "feat(frontend): build AI quiz home page"
```

## Task 15: Build the Complete Quiz Flow from `ui/core-flow.html`

**Files:**
- Create: `frontend/src/pages/quiz/index.config.ts`
- Create: `frontend/src/pages/quiz/index.tsx`
- Create: `frontend/src/pages/quiz/index.scss`
- Create: `frontend/src/pages/quiz/scoring.ts`
- Create: `frontend/src/pages/quiz/__tests__/quiz.test.tsx`

- [ ] **Step 1: Write failing interaction tests**

Cover single select replacing selection, multiple select toggling, judge selection, submission with no answer, immediate correct/incorrect explanation, disabled edits after submit, next-question progress, duration recording, final attempt submission, reward display, and report navigation.

- [ ] **Step 2: Run red, implement all three question types, run green**

Run: `cd frontend; npm test -- pages/quiz`

Match the prototype's heading, progress line, speech card, answer borders, feedback panel, reward strip and actions. Keep the explanation collapsible after it has first appeared.

- [ ] **Step 3: Commit**

```powershell
git add frontend/src/pages/quiz
git commit -m "feat(frontend): implement interactive quiz flow"
```

## Task 16: Build the Report Page

**Files:**
- Create: `frontend/src/pages/report/index.config.ts`
- Create: `frontend/src/pages/report/index.tsx`
- Create: `frontend/src/pages/report/index.scss`
- Create: `frontend/src/pages/report/__tests__/report.test.tsx`

- [ ] **Step 1: Write failing report tests**

Assert loading, retryable generation failure, accuracy, mastered/weak sections, three-line summary, advice, quote, and returning to history. Assert there is no active share-poster action in MVP.

- [ ] **Step 2: Run red, implement in the approved visual language, run green**

Run: `cd frontend; npm test -- pages/report`

Use the same cream background, white outlined panels, candy accents and compact typography as the four prototypes. Do not add marketing copy, gradients, nested cards, or a new navigation pattern.

- [ ] **Step 3: Commit**

```powershell
git add frontend/src/pages/report
git commit -m "feat(frontend): render AI review reports"
```

## Task 17: Build Learning Library and Profile from Their Prototypes

**Files:**
- Create: `frontend/src/pages/library/index.config.ts`
- Create: `frontend/src/pages/library/index.tsx`
- Create: `frontend/src/pages/library/index.scss`
- Create: `frontend/src/pages/profile/index.config.ts`
- Create: `frontend/src/pages/profile/index.tsx`
- Create: `frontend/src/pages/profile/index.scss`
- Create: `frontend/src/pages/library/__tests__/library.test.tsx`
- Create: `frontend/src/pages/profile/__tests__/profile.test.tsx`

- [ ] **Step 1: Write failing data tests**

Assert history filters and report links use API data; mastery bars reflect returned percentages; profile totals, streak, XP, coins and earned medals are not hard-coded. Assert the PK panel is visibly disabled and labeled `暂未开放`.

- [ ] **Step 2: Run red, implement both pages, run green**

Run: `cd frontend; npm test -- pages/library pages/profile`

Preserve each prototype's order, colors, panels, badges and navigation. Hide settings that have no MVP behavior rather than showing a fake success toast.

- [ ] **Step 3: Commit**

```powershell
git add frontend/src/pages/library frontend/src/pages/profile
git commit -m "feat(frontend): add real history and profile views"
```

## Task 18: End-to-End Integration and Release Verification

**Files:**
- Create: `docker-compose.yml`
- Create: `README.md`
- Create: `scripts/dev.ps1`
- Create: `backend/tests/e2e/test_learning_loop.py`
- Modify: `frontend/src/app.config.ts`
- Modify: `.env.example`

- [ ] **Step 1: Write a failing backend end-to-end test**

Using Fake Provider and the real test database, create a session, generate five questions, submit answers, generate a report, then fetch history. Assert IDs connect across responses, accuracy and rewards match server scoring, and history contains the completed quiz.

- [ ] **Step 2: Run red, connect missing route wiring, run green**

Run: `cd backend; python -m pytest tests/e2e/test_learning_loop.py -q`

Expected after integration: `1 passed`.

- [ ] **Step 3: Verify every automated gate**

```powershell
cd backend
python -m pytest -q
python -m ruff check .
python -m mypy app
cd ..\frontend
npm test -- --run
npm run typecheck
npm run lint
npm run build:weapp
npm run build:h5
```

Expected: zero test failures, zero lint/type errors, and both builds exit `0`.

- [ ] **Step 4: Visually verify the built app**

Start FastAPI and the H5 build. Use phone viewports `320x568`, `375x812`, `390x844`, and `430x932`. Capture every page and compare against the corresponding `ui/*.html`: verify exact palette, hierarchy, borders, shadows, no horizontal overflow, no text collision, four consistent tabs, loading/error/empty states, and real data updates after one complete run.

- [ ] **Step 5: Verify WeChat output and document operation**

Open `frontend/dist` in WeChat Developer Tools, confirm the five routes render and API domain configuration is documented. In `README.md`, document MySQL startup/migration, backend/frontend commands, CloseAI environment variables, test commands, live-smoke opt-in, and MVP exclusions.

- [ ] **Step 6: Final commit**

```powershell
git add docker-compose.yml README.md scripts backend/tests/e2e frontend/src/app.config.ts .env.example
git commit -m "test: verify Quizeloop MVP learning loop"
```
