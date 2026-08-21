import json
from datetime import UTC, datetime

from agentic_search.configs.prompts import PROMPTS
from agentic_search.memory.db import Memory
from agentic_search.services.llm import call_llm


def extract_l1(
    history: dict, session_id: str, recent_l1: list[Memory] | None = None
) -> list[Memory]:
    if recent_l1 is None:
        recent_l1 = []

    recent_block = "\n".join([f"- {m.content}" for m in recent_l1]) or "（无）"

    prompt = PROMPTS["l1_extract"].format(recent_block=recent_block, **history)

    raw = call_llm(prompt)

    facts = json.loads(raw)
    return [
        Memory(
            level="L1",
            content=fact,
            timestamp=datetime.now(UTC).isoformat(),
            session_id=session_id,
        )
        for fact in facts
    ]


def consolidate_l2(l1_memories: list[Memory]) -> Memory:
    if not l1_memories:
        raise ValueError("暂无 L1 记忆")
    facts = "\n".join(f"- {m.content}" for m in l1_memories)
    prompt = PROMPTS["l2_consolidate"].format(facts=facts)
    summary = call_llm(prompt)
    return Memory(
        level="L2",
        content=summary,
        timestamp=datetime.now(UTC).isoformat(),
        session_id=l1_memories[0].session_id,
    )


def consolidate_profile(
    l2_memories: list[Memory], previous_profile: Memory | None = None
) -> Memory:
    if not l2_memories:
        raise ValueError("暂无 L2 记忆")
    summaries = "\n".join(f"- {m.content}" for m in l2_memories)
    previous_block = (
        previous_profile.content if previous_profile else "（首次生成，尚无画像）"
    )
    prompt = PROMPTS["l5_profile"].format(
        previous_block=previous_block, summaries=summaries
    )
    profile = call_llm(prompt)
    return Memory(
        level="L5",
        content=profile,
        timestamp=datetime.now(UTC).isoformat(),
        session_id=None,
    )
