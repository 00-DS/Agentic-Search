import functools

import httpx
from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agentic_search.agents.tools import (
    extract_abstract,
    list_papers,
    read_paper,
    search_paper,
)
from agentic_search.configs.config import settings


def retry(max_attempts: int = 3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    print(f"  [retry] {func.__name__} 第 {attempt}/{max_attempts} 次失败：{e}")
                    last_exc = e
            assert last_exc is not None
            raise last_exc
        return wrapper
    return decorator

def build_graph():

    tools = [
        list_papers,
        read_paper,
        search_paper,
        extract_abstract
    ]

    llm = init_chat_model(
        model = settings.llm_model,
        model_provider = settings.llm_model_provider,
        base_url = settings.llm_base_url,
        api_key = settings.llm_api_key,
        timeout = settings.llm_timeout
    )

    llm_with_tools = llm.bind_tools(tools)

    @retry(max_attempts=3)
    def llm_call(state: MessagesState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def should_continue(state: MessagesState):
        last = state["messages"][-1]
        return "tool_node" if getattr(last, "tool_calls", None) else END
    
    builder = StateGraph(MessagesState)
    builder.add_node("llm_call", llm_call)
    builder.add_node("tool_node", ToolNode(tools))
    builder.add_edge(START, "llm_call")
    builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    builder.add_edge("tool_node", "llm_call")
    return builder.compile()