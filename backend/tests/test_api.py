from concurrent.futures import ThreadPoolExecutor


def unwrap(response):
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["code"] == 0
    assert payload["request_id"]
    return payload["data"]


def test_health_contract(client):
    assert unwrap(client.get("/api/v1/health"))["status"] == "ok"


def test_local_h5_origin_is_allowed(client):
    response = client.options(
        "/api/v1/history/stats",
        headers={
            "Origin": "http://127.0.0.1:10086",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-anonymous-id",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:10086"


def test_anonymous_session_creation_is_race_safe(client):
    def create_session(_index: int):
        return client.post(
            "/api/v1/sessions/anonymous",
            json={"anonymous_id": "anon_parallel_001"},
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(create_session, range(8)))

    assert {response.status_code for response in responses} == {200}
    assert len({response.json()["data"]["session_id"] for response in responses}) == 1


def test_complete_anonymous_learning_loop_is_persisted(client):
    first = unwrap(client.post("/api/v1/sessions/anonymous", json={"anonymous_id": "anon_tdd_001"}))
    restored = unwrap(client.post("/api/v1/sessions/anonymous", json={"anonymous_id": "anon_tdd_001"}))
    assert restored["session_id"] == first["session_id"]

    headers = {"X-Anonymous-Id": "anon_tdd_001", "Idempotency-Key": "quiz-one"}
    quiz = unwrap(
        client.post(
            "/api/v1/quizzes/generate",
            headers=headers,
            json={"user_input": "学习 RAG 与传统搜索的区别", "question_count": 5, "difficulty": "mixed"},
        )
    )
    assert len(quiz["questions"]) == 5
    assert {question["type"] for question in quiz["questions"]} == {"single", "multiple", "judge"}

    records = [
        {
            "question_id": question["id"],
            "selected_answers": question["answer"],
            "duration_ms": 1200,
        }
        for question in quiz["questions"]
    ]
    attempt_headers = {**headers, "Idempotency-Key": "attempt-one"}
    attempt = unwrap(
        client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=attempt_headers,
            json={"answer_records": records},
        )
    )
    repeated = unwrap(
        client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers=attempt_headers,
            json={"answer_records": records},
        )
    )
    assert attempt == repeated
    assert attempt["accuracy"] == 100
    assert attempt["xp_earned"] == 60
    assert attempt["coins_earned"] == 25

    report = unwrap(
        client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/report",
            headers={**headers, "Idempotency-Key": "report-one"},
        )
    )
    assert report["accuracy"] == 100
    assert len(report["three_line_summary"]) == 3

    stats = unwrap(client.get("/api/v1/history/stats", headers=headers))
    history = unwrap(client.get("/api/v1/history/quizzes", headers=headers))
    assert stats["completed_questions"] == 5
    assert stats["total_xp"] == 60
    assert history[0]["quiz_id"] == quiz["quiz_id"]


def test_server_recalculates_client_answers(client):
    headers = {"X-Anonymous-Id": "anon_tdd_002", "Idempotency-Key": "quiz-two"}
    unwrap(client.post("/api/v1/sessions/anonymous", json={"anonymous_id": "anon_tdd_002"}))
    quiz = unwrap(
        client.post(
            "/api/v1/quizzes/generate",
            headers=headers,
            json={"user_input": "Python 基础", "question_count": 5, "difficulty": "easy"},
        )
    )
    records = [
        {"question_id": q["id"], "selected_answers": ["Z"], "duration_ms": 100}
        for q in quiz["questions"]
    ]
    result = unwrap(
        client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers={**headers, "Idempotency-Key": "attempt-two"},
            json={"answer_records": records},
        )
    )
    assert result["accuracy"] == 0
    assert result["xp_earned"] == 0


def test_invalid_question_count_uses_unified_error(client):
    response = client.post(
        "/api/v1/quizzes/generate",
        headers={"X-Anonymous-Id": "anon_tdd_003", "Idempotency-Key": "bad"},
        json={"user_input": "主题", "question_count": 4, "difficulty": "mixed"},
    )
    assert response.status_code == 422
    assert response.json()["code"] != 0
    assert response.json()["request_id"]


def test_invalid_anonymous_id_characters_are_rejected(client):
    response = client.post(
        "/api/v1/sessions/anonymous",
        json={"anonymous_id": "anon with spaces"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == 4002


def test_report_provider_failure_uses_stable_business_error(client):
    from app.llm.graphs import ProviderError

    class FailingReportProvider:
        async def generate_report(self, context: str):
            raise ProviderError("private upstream details")

    headers = {"X-Anonymous-Id": "anon_report_failure", "Idempotency-Key": "quiz-report"}
    unwrap(client.post("/api/v1/sessions/anonymous", json={"anonymous_id": "anon_report_failure"}))
    quiz = unwrap(
        client.post(
            "/api/v1/quizzes/generate",
            headers=headers,
            json={"user_input": "事务基础", "question_count": 5, "difficulty": "easy"},
        )
    )
    answers = [
        {"question_id": question["id"], "selected_answers": question["answer"], "duration_ms": 1}
        for question in quiz["questions"]
    ]
    unwrap(
        client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers={**headers, "Idempotency-Key": "attempt-report"},
            json={"answer_records": answers},
        )
    )
    client.app.state.provider = FailingReportProvider()
    response = client.post(
        f"/api/v1/quizzes/{quiz['quiz_id']}/report",
        headers={**headers, "Idempotency-Key": "report-failure"},
    )
    assert response.status_code == 503
    assert response.json()["code"] == 5003
    assert "private upstream details" not in response.text
