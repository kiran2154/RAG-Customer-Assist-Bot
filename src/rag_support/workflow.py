from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph

from .config import Settings
from .hitl import HumanResponder, default_human_responder
from .prompts import SUPPORT_SYSTEM_PROMPT
from .retrieval import KnowledgeRetriever
from .routing import decide_route, detect_intent
from .schemas import SupportState


class SupportAssistant:
    def __init__(
        self,
        settings: Settings,
        retriever: KnowledgeRetriever,
        human_responder: HumanResponder | None = None,
    ) -> None:
        self.settings = settings
        self.retriever = retriever
        self.human_responder = human_responder or default_human_responder
        self.llm = None
        self.graph = self._build_graph()

    def _get_llm(self) -> ChatGroq:
        if self.llm is not None:
            return self.llm

        if not self.settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is missing. Configure it before querying.")

        self.llm = ChatGroq(
            api_key=self.settings.groq_api_key,
            model=self.settings.groq_model,
            temperature=0.1,
        )
        return self.llm

    def _build_graph(self):
        builder = StateGraph(SupportState)
        builder.add_node("process", self._process_node)
        builder.add_node("output", self._output_node)

        builder.add_edge(START, "process")
        builder.add_conditional_edges(
            "process",
            self._route_after_process,
            {
                "answer": "output",
                "escalate": "output",
            },
        )
        builder.add_edge("output", END)
        return builder.compile()

    def _route_after_process(self, state: SupportState) -> Literal["answer", "escalate"]:
        return "escalate" if state.get("route") == "escalate" else "answer"

    def _process_node(self, state: SupportState) -> SupportState:
        query = state["query"]
        intent = detect_intent(query)
        retrieval = self.retriever.retrieve(query)

        route, escalation_reason = decide_route(
            query=query,
            intent=intent,
            has_context=len(retrieval.chunks) > 0,
            top_score=retrieval.top_score,
            confidence_threshold=self.settings.confidence_threshold,
        )

        sources = [f"page={chunk['page']} chunk={chunk['chunk_id']}" for chunk in retrieval.chunks]

        return {
            **state,
            "intent": intent,
            "route": route,
            "escalation_reason": escalation_reason,
            "confidence": retrieval.top_score,
            "retrieved_chunks": retrieval.chunks,
            "context": retrieval.context,
            "sources": sources,
        }

    def _output_node(self, state: SupportState) -> SupportState:
        if state.get("route") == "escalate":
            human_response = self.human_responder(
                state.get("query", ""),
                state.get("escalation_reason", "no_reason_provided"),
            )
            answer = (
                "Escalated to human support.\n"
                f"Human response: {human_response}"
            )
            return {
                **state,
                "human_response": human_response,
                "answer": answer,
            }

        context = state.get("context", "")
        query = state.get("query", "")
        system_prompt = SUPPORT_SYSTEM_PROMPT.format(context=context)

        llm = self._get_llm()
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query),
            ]
        )

        answer_text = response.content if isinstance(response.content, str) else str(response.content)
        return {
            **state,
            "answer": answer_text,
        }

    def run(self, query: str) -> SupportState:
        state: SupportState = {"query": query}
        return self.graph.invoke(state)
