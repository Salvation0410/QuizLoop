from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Option(BaseModel):
    key: str = Field(min_length=1, max_length=8)
    text: str = Field(min_length=1)


class QuestionOutput(BaseModel):
    id: str
    type: Literal["single", "multiple", "judge"]
    stem: str = Field(min_length=1)
    options: list[Option] = Field(min_length=2)
    answer: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=1)
    knowledge_point: str = Field(min_length=1)
    difficulty: Literal["easy", "medium", "hard"]

    @model_validator(mode="after")
    def validate_answer(self):
        keys = [item.key for item in self.options]
        if len(keys) != len(set(keys)) or not set(self.answer).issubset(keys):
            raise ValueError("answer must reference unique option keys")
        if self.type in {"single", "judge"} and len(self.answer) != 1:
            raise ValueError("single and judge questions require one answer")
        if self.type == "multiple" and len(self.answer) < 2:
            raise ValueError("multiple questions require at least two answers")
        return self


class QuizOutput(BaseModel):
    title: str
    summary: str
    questions: list[QuestionOutput] = Field(min_length=5, max_length=15)

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [question.id for question in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("question ids must be unique")
        return self


class QuizGenerateRequest(BaseModel):
    user_input: str = Field(min_length=2, max_length=10000)
    question_count: int = Field(default=10, ge=5, le=15)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"


class AnswerInput(BaseModel):
    question_id: str
    selected_answers: list[str]
    duration_ms: int = Field(ge=0, le=3_600_000)


class AttemptRequest(BaseModel):
    answer_records: list[AnswerInput] = Field(min_length=1)
