from typing import Any

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.models import Quiz, Report
from app.schemas.quiz import AttemptRequest, QuizGenerateRequest
from app.services.learning import LearningService, get_or_create_session

router = APIRouter()


def envelope(request: Request, data: Any):
    return {"code": 0, "message": "ok", "data": data, "request_id": request.state.request_id}


def db_session(request: Request):
    with request.app.state.session_factory() as db:
        yield db


def anonymous(x_anonymous_id: str = Header(..., alias="X-Anonymous-Id")) -> str:
    return x_anonymous_id


def quiz_data(quiz: Quiz) -> dict:
    return {
        "quiz_id": quiz.id, "title": quiz.title, "summary": quiz.summary, "status": quiz.status,
        "questions": [{
            "id": q.id, "type": q.type, "stem": q.stem,
            "options": [{"key": o.key, "text": o.text} for o in q.options], "answer": q.answer,
            "explanation": q.explanation, "knowledge_point": q.knowledge_point, "difficulty": q.difficulty,
        } for q in quiz.questions],
    }


def report_data(report: Report) -> dict:
    return {
        "report_id": report.id, "quiz_id": report.quiz_id, "accuracy": report.accuracy,
        "mastered_points": report.mastered_points, "weak_points": report.weak_points,
        "three_line_summary": report.three_line_summary, "advice": report.advice, "share_quote": report.share_quote,
    }


@router.get("/health")
def health(request: Request):
    return envelope(request, {"status": "ok"})


@router.post("/sessions/anonymous")
def session(request: Request, payload: dict, db: Session = Depends(db_session)):
    item = get_or_create_session(db, payload.get("anonymous_id", ""))
    return envelope(request, {"session_id": item.id, "anonymous_id": item.anonymous_id})


@router.post("/quizzes/generate")
async def generate(request: Request, payload: QuizGenerateRequest, anonymous_id: str = Depends(anonymous), idempotency_key: str = Header(..., alias="Idempotency-Key"), db: Session = Depends(db_session)):
    session_item = get_or_create_session(db, anonymous_id)
    quiz = await LearningService(db, request.app.state.provider).generate_quiz(session_item, payload, idempotency_key)
    return envelope(request, quiz_data(quiz))


@router.get("/quizzes/{quiz_id}")
def get_quiz(request: Request, quiz_id: str, anonymous_id: str = Depends(anonymous), db: Session = Depends(db_session)):
    session_item = get_or_create_session(db, anonymous_id)
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id, Quiz.session_id == session_item.id))
    if not quiz:
        raise BusinessError(4041, "题库不存在", 404)
    return envelope(request, quiz_data(quiz))


@router.post("/quizzes/{quiz_id}/attempts")
def attempt(request: Request, quiz_id: str, payload: AttemptRequest, anonymous_id: str = Depends(anonymous), idempotency_key: str = Header(..., alias="Idempotency-Key"), db: Session = Depends(db_session)):
    session_item = get_or_create_session(db, anonymous_id)
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id))
    if not quiz:
        raise BusinessError(4041, "题库不存在", 404)
    result = LearningService(db, request.app.state.provider).submit_attempt(session_item, quiz, payload, idempotency_key)
    return envelope(request, {"attempt_id": result.id, "correct_count": result.correct_count, "total_questions": result.total_questions, "accuracy": result.accuracy, "xp_earned": result.xp_earned, "coins_earned": result.coins_earned})


@router.post("/quizzes/{quiz_id}/report")
async def generate_report(request: Request, quiz_id: str, anonymous_id: str = Depends(anonymous), idempotency_key: str = Header(..., alias="Idempotency-Key"), db: Session = Depends(db_session)):
    session_item = get_or_create_session(db, anonymous_id)
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id, Quiz.session_id == session_item.id))
    if not quiz:
        raise BusinessError(4041, "题库不存在", 404)
    result = await LearningService(db, request.app.state.provider).generate_report(session_item, quiz, idempotency_key)
    return envelope(request, report_data(result))


@router.get("/reports/{report_id}")
def get_report(request: Request, report_id: str, anonymous_id: str = Depends(anonymous), db: Session = Depends(db_session)):
    session_item = get_or_create_session(db, anonymous_id)
    report = db.scalar(select(Report).where(Report.id == report_id, Report.session_id == session_item.id))
    if not report:
        raise BusinessError(4042, "报告不存在", 404)
    return envelope(request, report_data(report))


@router.get("/history/stats")
def stats(request: Request, anonymous_id: str = Depends(anonymous), db: Session = Depends(db_session)):
    session_item = get_or_create_session(db, anonymous_id)
    return envelope(request, LearningService(db, request.app.state.provider).stats(session_item))


@router.get("/history/quizzes")
def history(request: Request, anonymous_id: str = Depends(anonymous), db: Session = Depends(db_session)):
    session_item = get_or_create_session(db, anonymous_id)
    return envelope(request, LearningService(db, request.app.state.provider).history(session_item))
