import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import BusinessError
from app.domain.scoring import is_correct_answer, reward_for
from app.llm.graphs import ProviderError
from app.llm.provider import LLMProvider
from app.models import (
    AnonymousSession,
    AnswerRecord,
    Attempt,
    GenerationJob,
    Question,
    QuestionOption,
    Quiz,
    Report,
    RewardLedger,
)
from app.models.entities import now
from app.schemas.quiz import AttemptRequest, QuizGenerateRequest


def get_or_create_session(db: Session, anonymous_id: str) -> AnonymousSession:
    if not re.fullmatch(r"[A-Za-z0-9_-]{4,80}", anonymous_id):
        raise BusinessError(4002, "匿名标识不合法", 422)
    item = db.scalar(select(AnonymousSession).where(AnonymousSession.anonymous_id == anonymous_id))
    if item:
        item.last_active_at = now()
    else:
        item = AnonymousSession(anonymous_id=anonymous_id)
        db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        item = db.scalar(
            select(AnonymousSession).where(AnonymousSession.anonymous_id == anonymous_id)
        )
        if item is None:
            raise
    return item


class LearningService:
    def __init__(self, db: Session, provider: LLMProvider):
        self.db = db
        self.provider = provider

    async def generate_quiz(self, session: AnonymousSession, request: QuizGenerateRequest, key: str) -> Quiz:
        existing_job = self.db.scalar(select(GenerationJob).where(GenerationJob.session_id == session.id, GenerationJob.idempotency_key == key))
        if existing_job:
            existing_quiz = self.db.scalar(
                select(Quiz).where(Quiz.generation_job_id == existing_job.id)
            )
            if existing_quiz:
                return existing_quiz
            raise BusinessError(5002, "生成任务状态异常，请更换请求标识后重试", 409)
        topic = " ".join(request.user_input.split())
        if any(word in topic for word in ("制毒", "炸弹制作")):
            raise BusinessError(4003, "输入内容无法用于生成题目", 400)
        try:
            output = await self.provider.generate_quiz(
                topic, request.question_count, request.difficulty
            )
        except ProviderError as exc:
            raise BusinessError(5001, "题库生成失败，请稍后重试", 503) from exc
        job = GenerationJob(session_id=session.id, idempotency_key=key)
        self.db.add(job)
        self.db.flush()
        quiz = Quiz(session_id=session.id, generation_job_id=job.id, title=output.title, summary=output.summary, user_input=topic, difficulty=request.difficulty)
        self.db.add(quiz)
        self.db.flush()
        for position, data in enumerate(output.questions):
            question = Question(
                id=f"{quiz.id}_{data.id}", quiz_id=quiz.id, position=position, type=data.type,
                stem=data.stem, answer=data.answer, explanation=data.explanation,
                knowledge_point=data.knowledge_point, difficulty=data.difficulty,
            )
            question.options = [QuestionOption(key=item.key, text=item.text, position=index) for index, item in enumerate(data.options)]
            quiz.questions.append(question)
        self.db.commit()
        return quiz

    def submit_attempt(self, session: AnonymousSession, quiz: Quiz, request: AttemptRequest, key: str) -> Attempt:
        existing = self.db.scalar(select(Attempt).where(Attempt.session_id == session.id, Attempt.idempotency_key == key))
        if existing:
            return existing
        if quiz.session_id != session.id:
            raise BusinessError(4041, "题库不存在", 404)
        by_id = {record.question_id: record for record in request.answer_records}
        if set(by_id) != {question.id for question in quiz.questions}:
            raise BusinessError(4004, "必须完整提交每一道题", 422)
        results = [(question, by_id[question.id], is_correct_answer(question.answer, by_id[question.id].selected_answers)) for question in quiz.questions]
        correct = sum(1 for _, _, ok in results if ok)
        xp, coins = reward_for(correct, len(results))
        attempt = Attempt(
            quiz_id=quiz.id, session_id=session.id, idempotency_key=key, correct_count=correct,
            total_questions=len(results), accuracy=round(correct * 100 / len(results)), xp_earned=xp, coins_earned=coins,
        )
        attempt.answers = [AnswerRecord(question_id=q.id, selected_answers=r.selected_answers, duration_ms=r.duration_ms, is_correct=int(ok)) for q, r, ok in results]
        self.db.add(attempt)
        self.db.flush()
        self.db.add_all([RewardLedger(attempt_id=attempt.id, kind="xp", amount=xp), RewardLedger(attempt_id=attempt.id, kind="coins", amount=coins)])
        quiz.status = "completed"
        self.db.commit()
        return attempt

    async def generate_report(self, session: AnonymousSession, quiz: Quiz, key: str) -> Report:
        existing = self.db.scalar(select(Report).where(Report.session_id == session.id, Report.idempotency_key == key))
        if existing:
            return existing
        attempt = self.db.scalar(select(Attempt).where(Attempt.quiz_id == quiz.id, Attempt.session_id == session.id))
        if not attempt:
            raise BusinessError(4005, "完成闯关后才能生成报告", 409)
        correct_ids = {a.question_id for a in attempt.answers if a.is_correct}
        mastered = [q.knowledge_point for q in quiz.questions if q.id in correct_ids]
        weak = [q.knowledge_point for q in quiz.questions if q.id not in correct_ids]
        try:
            generated = await self.provider.generate_report(
                f"主题：{quiz.title}；正确率：{attempt.accuracy}；掌握：{mastered}；薄弱：{weak}"
            )
        except ProviderError as exc:
            raise BusinessError(5003, "报告生成失败，请稍后重试", 503) from exc
        report = Report(
            quiz_id=quiz.id, attempt_id=attempt.id, session_id=session.id, idempotency_key=key,
            accuracy=attempt.accuracy, mastered_points=list(dict.fromkeys(mastered)) or generated.mastered_points,
            weak_points=list(dict.fromkeys(weak)), three_line_summary=generated.three_line_summary,
            advice=generated.advice, share_quote=generated.share_quote,
        )
        self.db.add(report)
        self.db.commit()
        return report

    def stats(self, session: AnonymousSession) -> dict:
        attempts = list(self.db.scalars(select(Attempt).where(Attempt.session_id == session.id)))
        return {
            "completed_questions": sum(item.total_questions for item in attempts),
            "average_accuracy": round(sum(item.accuracy for item in attempts) / len(attempts)) if attempts else 0,
            "total_xp": sum(item.xp_earned for item in attempts),
            "total_coins": sum(item.coins_earned for item in attempts),
            "streak_days": len({item.completed_at.date().isoformat() for item in attempts}),
            "completed_quizzes": len(attempts),
        }

    def history(self, session: AnonymousSession) -> list[dict]:
        quizzes = self.db.scalars(select(Quiz).where(Quiz.session_id == session.id).order_by(Quiz.created_at.desc())).all()
        return [{"quiz_id": q.id, "title": q.title, "summary": q.summary, "status": q.status, "question_count": len(q.questions), "created_at": q.created_at.isoformat()} for q in quizzes]
