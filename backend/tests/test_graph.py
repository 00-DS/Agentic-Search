from langchain_core.messages import HumanMessage

from agentic_search.agents.graph import build_graph


def test_graph_returns_answer():
    """agent 跑完 ReAct 循环后，最后一条消息应是含答案的 AIMessage。"""
    graph = build_graph()
    result = graph.invoke(
        {
            "messages": [HumanMessage(content="TiMem的核心方法是什么？")],
        }
    )

    final = result["messages"][-1]
    assert final.content
