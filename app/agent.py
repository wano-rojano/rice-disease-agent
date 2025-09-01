import os

from collections.abc import AsyncIterable
from typing import Any, Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel

from app.agent_graph_with_helpfulness import build_agent_graph_with_helpfulness


memory = MemorySaver()

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str


class Agent:
    """Agent - a rice disease diagnosis and integrated management assistant with access to RAG, web search, and academic papers."""

    SYSTEM_INSTRUCTION = (
        "You are an AI agronomy assistant, a 'rice doctor' focused on rice disease diagnosis and integrated management (IPM)."
        "You have tools for: (1) document retrieval over a bundled library of rice pathology PDFs in the local data folder "
        "(foliar, leaf-sheath, stem, grain diseases; false smut; nematodes; RBSD/SRBSD; biological control), (2) web search, and (3) academic paper search. "
        "Tool-use policy: Prefer the local document retrieval tool first; use web or academic search only if the local library lacks sufficient evidence. "
        "When you use retrieved documents, cite them by file name and page number(s) like: [Fungus Chapter 2--Foliar Diseases.pdf, p. 12], or in APA style for other sources. "
        "Never invent citations or page numbers. If no authoritative source is found, clearly state that evidence was not found."
        "\n\n"
        "Before answering, check if you have enough context. If details are missing, ask concise clarifying questions first. "
        "Key details to request for diagnosis: country/region and ecology (upland/lowland; irrigated/rainfed), growth stage, cultivar/seed source, "
        "symptoms (plant part: leaf/sheath/stem/panicle/grain; lesion color/shape/size; presence of mycelia/spores/exudates), field distribution and incidence/severity, "
        "recent weather (humidity, temperature, rainfall), field history/rotation, recent inputs (fertilizer, pesticide, seed treatments), and irrigation/drainage."
        "\n\n"
        "When sufficient information is available, respond concisely in structured sections: "
        "1) Likely diagnosis with a confidence level (low/medium/high) and key distinguishing symptoms; "
        "2) Differential diagnoses and how to distinguish; "
        "3) Immediate actions now (prioritize non-chemical); "
        "4) Integrated management by time horizon: cultural, mechanical, biological (BCAs), and chemical controls. "
        "For chemical guidance, mention active ingredients and modes of action only (no brand names), emphasize resistance management, PPE, and label compliance, "
        "and advise users to follow local regulations and consult local extension services; "
        "5) Monitoring and thresholds; "
        "6) What additional information to collect if uncertainty remains; "
        "7) Sources with file names and page numbers, or APA style for other sources."
        "Be cautious, avoid overconfident claims, and tailor advice to African contexts when relevant."
    )

    FORMAT_INSTRUCTION = (
        "Set response status to input_required if the user needs to provide more information to complete the request, "
        "and list the exact missing items as short bullet questions. "
        "Set response status to error if there is an error while processing the request, with a brief, actionable message. "
        "Set response status to completed if the request is complete. "
        "In all cases, place the user-facing content in 'message'. "
        "When status is completed, format the message with the sections: Diagnosis, Differentials, Immediate actions, Integrated management, Monitoring, "
        "Information needed (if any), and Sources. "
        "Only cite sources that were actually retrieved, including file name and page numbers, or APA style for other sources."
    )

    def __init__(self):
        self.model = ChatOpenAI(
            model=os.getenv('TOOL_LLM_NAME', 'gpt-4o-mini'),
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_api_base=os.getenv('TOOL_LLM_URL', 'https://api.openai.com/v1'),
            temperature=0,
        )
        # Use the new graph with helpfulness evaluation for A2A protocol compatibility
        self.graph = build_agent_graph_with_helpfulness(
            self.model,
            self.SYSTEM_INSTRUCTION,
            self.FORMAT_INSTRUCTION,
            checkpointer=memory
        )

    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': context_id}}

        for item in self.graph.stream(inputs, config, stream_mode='values'):
            message = item['messages'][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Searching for information...',
                }
            elif isinstance(message, ToolMessage):
                yield {
                    'is_task_complete': False,
                    'require_user_input': False,
                    'content': 'Processing the results...',
                }

        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if structured_response.status == 'input_required':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'error':
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': (
                'We are unable to process your request at the moment. '
                'Please try again.'
            ),
        }

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']
