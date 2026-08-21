import functools

import httpx
from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agentic_search.agents.tools import (
    extract_abstract,
    list_papers,
    read_paper,
    search_paper,
)
from agentic_search.configs.prompts import PROMPTS
from agentic_search.memory.db import (
    L2_TRIGGER_THRESHOLD,
    get_memories_for_context,
    load_memories,
    save_memory,
    upsert_l2,
)
from agentic_search.memory.memory import consolidate_l2, extract_l1
from agentic_search.services.llm import llm


def retry(max_attempts: int = 3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    print(
                        f"  [retry] {func.__name__} 第 {attempt}/{max_attempts} 次失败：{e}"
                    )
                    last_exc = e
            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


class MemoryState(MessagesState):
    """模块 2 的 MessagesState 扩展会话 ID——retrieve_memory/store_memory 读写。"""

    session_id: str


def build_graph():

    tools = [list_papers, read_paper, search_paper, extract_abstract]

    llm_with_tools = llm.bind_tools(tools)

    @retry(max_attempts=3)
    def llm_call(state):
        messages = [SystemMessage(content=PROMPTS["persona"])] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: MessagesState):
        last = state["messages"][-1]
        return "tool_node" if getattr(last, "tool_calls", None) else "store_memory"

    @retry(max_attempts=3)
    def retrieve_memory(state):
        memories = get_memories_for_context(state["session_id"])
        profiles = [m for m in memories if m.level == "L5"]
        session_mems = [m for m in memories if m.level != "L5"]
        if not profiles and not session_mems:
            return {"messages": []}
        sections = []
        if profiles:
            sections.append(
                "用户画像（跨会话长期记忆）：\n"
                + "\n".join(f"- {m.content}" for m in profiles)
            )
        if session_mems:
            sections.append(
                "本会话历史记忆：\n"
                + "\n".join(f"- [{m.level}] {m.content}" for m in session_mems)
            )
        memory_msg = SystemMessage(
            content="以下是记忆背景，回答时作为参考：\n\n" + "\n\n".join(sections)
        )
        return {"messages": [memory_msg]}

    @retry(max_attempts=3)
    def store_memory(state):
        """提取 L1 落库 + L2 自动触发（新增 L1 达阈值则重整合）。"""
        session_id = state["session_id"]
        history = {  # 取最后一对 user/agent 消息（人设与记忆 SystemMessage 不参与提取）
            "user": next(
                m.content for m in reversed(state["messages"]) if m.type == "human"
            ),
            "agent": next(
                m.content for m in reversed(state["messages"]) if m.type == "ai"
            ),
        }
        recent_l1 = load_memories(session_id, level="L1", limit=10)  # 历史去重窗口
        for m in extract_l1(history, session_id, recent_l1):
            save_memory(m)

        # —— L2 自动触发：新增 L1（timestamp 晚于现有 L2）达阈值则重整合 ——
        l1s = load_memories(session_id, level="L1")
        l2s = load_memories(session_id, level="L2")
        new_l1 = l1s if not l2s else [m for m in l1s if m.timestamp > l2s[0].timestamp]
        if len(new_l1) >= L2_TRIGGER_THRESHOLD:
            upsert_l2(consolidate_l2(l1s))  # 全部 L1 重整合，幂等更新同一条
        return {"messages": []}

    builder = StateGraph(MemoryState)
    builder.add_node("llm_call", llm_call)
    builder.add_node("tool_node", ToolNode(tools))
    builder.add_node("retrieve_memory", retrieve_memory)
    builder.add_node("store_memory", store_memory)
    builder.add_edge(START, "retrieve_memory")
    builder.add_edge("retrieve_memory", "llm_call")
    builder.add_conditional_edges(
        "llm_call", should_continue, ["tool_node", "store_memory"]
    )
    builder.add_edge("tool_node", "llm_call")
    builder.add_edge("store_memory", END)
    return builder.compile()
