import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import Attempt, RewardLedger


def unwrap(response):
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_reward_kind_is_unique_per_attempt(client) -> None:
    anonymous_id = "anon_reward_constraint"
    headers = {"X-Anonymous-Id": anonymous_id, "Idempotency-Key": "quiz-reward"}
    unwrap(client.post("/api/v1/sessions/anonymous", json={"anonymous_id": anonymous_id}))
    quiz = unwrap(
        client.post(
            "/api/v1/quizzes/generate",
            headers=headers,
            json={"user_input": "数据库约束", "question_count": 5, "difficulty": "easy"},
        )
    )
    answers = [
        {"question_id": item["id"], "selected_answers": item["answer"], "duration_ms": 1}
        for item in quiz["questions"]
    ]
    unwrap(
        client.post(
            f"/api/v1/quizzes/{quiz['quiz_id']}/attempts",
            headers={**headers, "Idempotency-Key": "attempt-reward"},
            json={"answer_records": answers},
        )
    )

    with client.app.state.session_factory() as db:
        attempt = db.scalar(select(Attempt).where(Attempt.quiz_id == quiz["quiz_id"]))
        assert attempt is not None
        db.add(RewardLedger(attempt_id=attempt.id, kind="xp", amount=999))
        with pytest.raises(IntegrityError):
            db.commit()
