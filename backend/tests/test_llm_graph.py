import pytest

from app.llm.graphs import ProviderError, StructuredOutputGraph
from app.llm.provider import ReportOutput


@pytest.mark.asyncio
async def test_graph_retries_invalid_structured_output() -> None:
    calls = 0

    async def invoke(_: dict[str, str]) -> dict:
        nonlocal calls
        calls += 1
        if calls == 1:
            return {"mastered_points": []}
        return {
            "mastered_points": ["概念"],
            "weak_points": [],
            "three_line_summary": ["一", "二", "三"],
            "advice": ["复习"],
            "share_quote": "继续学",
        }

    graph = StructuredOutputGraph(invoke, ReportOutput, max_retries=2)
    result = await graph.ainvoke({"context": "事实"})

    assert result.share_quote == "继续学"
    assert calls == 2


@pytest.mark.asyncio
async def test_graph_stops_after_retry_budget_without_leaking_error_text() -> None:
    calls = 0

    async def invoke(_: dict[str, str]) -> dict:
        nonlocal calls
        calls += 1
        raise ValueError("secret-api-key")

    graph = StructuredOutputGraph(invoke, ReportOutput, max_retries=2)

    with pytest.raises(ProviderError) as caught:
        await graph.ainvoke({"context": "事实"})

    assert calls == 3
    assert "secret-api-key" not in str(caught.value)
