"""Create the MVP learning facts.

Revision ID: 0001_initial
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "anonymous_sessions",
        sa.Column("id", sa.String(45), primary_key=True),
        sa.Column("anonymous_id", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("anonymous_id"),
    )
    op.create_index("ix_anonymous_sessions_anonymous_id", "anonymous_sessions", ["anonymous_id"], unique=True)
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(45), primary_key=True),
        sa.Column("session_id", sa.String(45), sa.ForeignKey("anonymous_sessions.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(30), nullable=False),
        sa.UniqueConstraint("session_id", "idempotency_key"),
    )
    op.create_index("ix_generation_jobs_session_id", "generation_jobs", ["session_id"])
    op.create_table(
        "quizzes",
        sa.Column("id", sa.String(45), primary_key=True),
        sa.Column("session_id", sa.String(45), sa.ForeignKey("anonymous_sessions.id"), nullable=False),
        sa.Column("generation_job_id", sa.String(45), sa.ForeignKey("generation_jobs.id"), nullable=False, unique=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("user_input", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_quizzes_session_id", "quizzes", ["session_id"])
    op.create_table(
        "questions",
        sa.Column("id", sa.String(60), primary_key=True),
        sa.Column("quiz_id", sa.String(45), sa.ForeignKey("quizzes.id"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("answer", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("knowledge_point", sa.String(180), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
    )
    op.create_index("ix_questions_quiz_id", "questions", ["quiz_id"])
    op.create_table(
        "question_options",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("question_id", sa.String(60), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("key", sa.String(8), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("question_id", "key"),
    )
    op.create_index("ix_question_options_question_id", "question_options", ["question_id"])
    op.create_table(
        "attempts",
        sa.Column("id", sa.String(45), primary_key=True),
        sa.Column("quiz_id", sa.String(45), sa.ForeignKey("quizzes.id"), nullable=False),
        sa.Column("session_id", sa.String(45), sa.ForeignKey("anonymous_sessions.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Integer(), nullable=False),
        sa.Column("xp_earned", sa.Integer(), nullable=False),
        sa.Column("coins_earned", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("session_id", "idempotency_key"),
    )
    op.create_index("ix_attempts_quiz_id", "attempts", ["quiz_id"])
    op.create_index("ix_attempts_session_id", "attempts", ["session_id"])
    op.create_table(
        "answer_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("attempt_id", sa.String(45), sa.ForeignKey("attempts.id"), nullable=False),
        sa.Column("question_id", sa.String(60), sa.ForeignKey("questions.id"), nullable=False),
        sa.Column("selected_answers", sa.JSON(), nullable=False),
        sa.Column("is_correct", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.UniqueConstraint("attempt_id", "question_id"),
    )
    op.create_index("ix_answer_records_attempt_id", "answer_records", ["attempt_id"])
    op.create_index("ix_answer_records_question_id", "answer_records", ["question_id"])
    op.create_table(
        "reward_ledger",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("attempt_id", sa.String(45), sa.ForeignKey("attempts.id"), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.UniqueConstraint("attempt_id", "kind"),
    )
    op.create_index("ix_reward_ledger_attempt_id", "reward_ledger", ["attempt_id"])
    op.create_table(
        "reports",
        sa.Column("id", sa.String(45), primary_key=True),
        sa.Column("quiz_id", sa.String(45), sa.ForeignKey("quizzes.id"), nullable=False),
        sa.Column("attempt_id", sa.String(45), sa.ForeignKey("attempts.id"), nullable=False, unique=True),
        sa.Column("session_id", sa.String(45), sa.ForeignKey("anonymous_sessions.id"), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=False),
        sa.Column("accuracy", sa.Integer(), nullable=False),
        sa.Column("mastered_points", sa.JSON(), nullable=False),
        sa.Column("weak_points", sa.JSON(), nullable=False),
        sa.Column("three_line_summary", sa.JSON(), nullable=False),
        sa.Column("advice", sa.JSON(), nullable=False),
        sa.Column("share_quote", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("session_id", "idempotency_key"),
    )
    op.create_index("ix_reports_quiz_id", "reports", ["quiz_id"])
    op.create_index("ix_reports_session_id", "reports", ["session_id"])


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("reward_ledger")
    op.drop_table("answer_records")
    op.drop_table("attempts")
    op.drop_table("question_options")
    op.drop_table("questions")
    op.drop_table("quizzes")
    op.drop_table("generation_jobs")
    op.drop_table("anonymous_sessions")
