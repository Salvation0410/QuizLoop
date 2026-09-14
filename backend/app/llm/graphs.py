from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypedDict, cast

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


class GraphState(TypedDict, total=False):
    payload: dict[str, Any]
    attempts: int
    result: BaseModel
    error_type: str


class ProviderError(RuntimeError):
    """A retryable failure returned by an LLM provider."""


class StructuredOutputGraph[OutputT: BaseModel]:
    """Bounded LangGraph workflow for validated structured model output."""

    def __init__(
        self,
        invoke: Callable[[dict[str, Any]], Awaitable[Any]],
        schema: type[OutputT],
        max_retries: int,
    ) -> None:
        self._invoke = invoke
        self._schema = schema
        self._max_attempts = max_retries + 1
        builder = StateGraph(GraphState)
        builder.add_node("call_model", self._call_model)
        builder.add_node("failed", self._failed)
        builder.add_edge(START, "call_model")
        builder.add_conditional_edges(
            "call_model",
            self._route,
            {"done": END, "retry": "call_model", "failed": "failed"},
        )
        builder.add_edge("failed", END)
        self._graph = builder.compile()

    async def _call_model(self, state: GraphState) -> GraphState:
        attempts = state.get("attempts", 0) + 1
        try:
            value = self._schema.model_validate(await self._invoke(state["payload"]))
            return {"attempts": attempts, "result": value, "error_type": ""}
        except Exception as exc:  # noqa: BLE001 - sanitizes all external provider failures
            return {"attempts": attempts, "error_type": type(exc).__name__}

    def _route(self, state: GraphState) -> Literal["done", "retry", "failed"]:
        if state.get("result") is not None:
            return "done"
        if state.get("attempts", 0) < self._max_attempts:
            return "retry"
        return "failed"

    @staticmethod
    def _failed(state: GraphState) -> GraphState:
        return state

    async def ainvoke(self, payload: dict[str, Any]) -> OutputT:
        state = await self._graph.ainvoke({"payload": payload, "attempts": 0})
        result = state.get("result")
        if result is None:
            error_type = state.get("error_type", "UnknownProviderError")
            raise ProviderError(
                f"structured output failed after {state['attempts']} attempts ({error_type})"
            )
        return cast(OutputT, result)
