from typing import Protocol

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import Settings
from app.llm.graphs import StructuredOutputGraph
from app.schemas.quiz import Option, QuestionOutput, QuizOutput


class ReportOutput(BaseModel):
    mastered_points: list[str]
    weak_points: list[str]
    three_line_summary: list[str]
    advice: list[str]
    share_quote: str


class LLMProvider(Protocol):
    async def generate_quiz(self, topic: str, count: int, difficulty: str) -> QuizOutput: ...
    async def generate_report(self, context: str) -> ReportOutput: ...


class DemoProvider:
    async def generate_quiz(self, topic: str, count: int, difficulty: str) -> QuizOutput:
        types = ["single", "multiple", "judge"]
        questions = []
        for index in range(count):
            qtype = types[index % 3]
            if qtype == "judge":
                options = [Option(key="A", text="正确"), Option(key="B", text="错误")]
                answer = ["A"]
            else:
                options = [
                    Option(key="A", text=f"{topic} 的核心概念"),
                    Option(key="B", text="与主题无关的说法"),
                    Option(key="C", text=f"{topic} 的常见应用"),
                ]
                answer = ["A", "C"] if qtype == "multiple" else ["A"]
            questions.append(QuestionOutput(
                id=f"q{index + 1}", type=qtype, stem=f"关于“{topic}”的第 {index + 1} 题",
                options=options, answer=answer, explanation=f"这道题帮助理解 {topic} 的核心知识。",
                knowledge_point=topic[:40], difficulty="medium" if difficulty == "mixed" else difficulty,
            ))
        return QuizOutput(title=f"{topic[:30]}闯关", summary=f"围绕 {topic} 生成的学习题库", questions=questions)

    async def generate_report(self, context: str) -> ReportOutput:
        return ReportOutput(
            mastered_points=["已答对的核心知识点"], weak_points=["需要继续巩固的知识点"],
            three_line_summary=["先理解核心概念。", "再分辨常见误区。", "最后通过应用加深记忆。"],
            advice=["复习错题讲解", "明天再次挑战薄弱知识点"], share_quote="把知识做成关卡，记忆会更深。",
        )


class CloseAIProvider:
    def __init__(self, settings: Settings):
        if not settings.closeai_api_key.get_secret_value():
            raise ValueError("CLOSEAI_API_KEY 未配置")
        model = ChatOpenAI(
            model=settings.llm_model, base_url=settings.closeai_base_url,
            api_key=settings.closeai_api_key, timeout=settings.llm_timeout_seconds, max_retries=0,
        )
        quiz_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是学习教练。生成适合移动端的单选、多选、判断题，讲解准确简洁。"),
            ("user", "主题：{topic}\n题量：{count}\n难度：{difficulty}"),
        ])
        report_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是学习复盘教练，只根据给定事实生成简洁建议。"),
            ("user", "{context}"),
        ])
        self.quiz_chain = quiz_prompt | model.with_structured_output(QuizOutput)
        self.report_chain = report_prompt | model.with_structured_output(ReportOutput)
        self.quiz_graph = StructuredOutputGraph(
            self.quiz_chain.ainvoke, QuizOutput, settings.llm_max_retries
        )
        self.report_graph = StructuredOutputGraph(
            self.report_chain.ainvoke, ReportOutput, settings.llm_max_retries
        )

    async def generate_quiz(self, topic: str, count: int, difficulty: str) -> QuizOutput:
        return await self.quiz_graph.ainvoke(
            {"topic": topic, "count": count, "difficulty": difficulty}
        )

    async def generate_report(self, context: str) -> ReportOutput:
        return await self.report_graph.ainvoke({"context": context})


def build_provider(settings: Settings) -> LLMProvider:
    if settings.llm_mode == "demo" or (settings.llm_mode == "auto" and not settings.closeai_api_key.get_secret_value()):
        return DemoProvider()
    return CloseAIProvider(settings)
