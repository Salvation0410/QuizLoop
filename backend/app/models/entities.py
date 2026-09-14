from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def now() -> datetime:
    return datetime.now(UTC)


class AnonymousSession(Base):
    __tablename__ = "anonymous_sessions"
    id: Mapped[str] = mapped_column(String(45), primary_key=True, default=lambda: uid("session"))
    anonymous_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"
    id: Mapped[str] = mapped_column(String(45), primary_key=True, default=lambda: uid("job"))
    session_id: Mapped[str] = mapped_column(ForeignKey("anonymous_sessions.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str] = mapped_column(String(30), default="quiz_v1")
    __table_args__ = (UniqueConstraint("session_id", "idempotency_key"),)


class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[str] = mapped_column(String(45), primary_key=True, default=lambda: uid("quiz"))
    session_id: Mapped[str] = mapped_column(ForeignKey("anonymous_sessions.id"), index=True)
    generation_job_id: Mapped[str] = mapped_column(ForeignKey("generation_jobs.id"), unique=True)
    title: Mapped[str] = mapped_column(String(180))
    summary: Mapped[str] = mapped_column(Text)
    user_input: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    questions: Mapped[list["Question"]] = relationship(cascade="all, delete-orphan", order_by="Question.position")


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(20))
    stem: Mapped[str] = mapped_column(Text)
    answer: Mapped[list[str]] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)
    knowledge_point: Mapped[str] = mapped_column(String(180))
    difficulty: Mapped[str] = mapped_column(String(20))
    options: Mapped[list["QuestionOption"]] = relationship(cascade="all, delete-orphan", order_by="QuestionOption.position")


class QuestionOption(Base):
    __tablename__ = "question_options"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    key: Mapped[str] = mapped_column(String(8))
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("question_id", "key"),)


class Attempt(Base):
    __tablename__ = "attempts"
    id: Mapped[str] = mapped_column(String(45), primary_key=True, default=lambda: uid("attempt"))
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id"), index=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("anonymous_sessions.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    correct_count: Mapped[int] = mapped_column(Integer)
    total_questions: Mapped[int] = mapped_column(Integer)
    accuracy: Mapped[int] = mapped_column(Integer)
    xp_earned: Mapped[int] = mapped_column(Integer)
    coins_earned: Mapped[int] = mapped_column(Integer)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    answers: Mapped[list["AnswerRecord"]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("session_id", "idempotency_key"),)


class AnswerRecord(Base):
    __tablename__ = "answer_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    selected_answers: Mapped[list[str]] = mapped_column(JSON)
    is_correct: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("attempt_id", "question_id"),)


class RewardLedger(Base):
    __tablename__ = "reward_ledger"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    amount: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint("attempt_id", "kind"),)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(45), primary_key=True, default=lambda: uid("report"))
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id"), index=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id"), unique=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("anonymous_sessions.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    accuracy: Mapped[int] = mapped_column(Integer)
    mastered_points: Mapped[list[str]] = mapped_column(JSON)
    weak_points: Mapped[list[str]] = mapped_column(JSON)
    three_line_summary: Mapped[list[str]] = mapped_column(JSON)
    advice: Mapped[list[str]] = mapped_column(JSON)
    share_quote: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (UniqueConstraint("session_id", "idempotency_key"),)
