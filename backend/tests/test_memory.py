# tests/test_memory.py —— 教学示例：记忆层零 LLM 部分的行为测试

from uuid import uuid4

from fastapi.testclient import TestClient

from agentic_search.configs.prompts import PROMPTS
from agentic_search.main import app
from agentic_search.memory.db import (
    L2_TRIGGER_THRESHOLD,
    Memory,
    get_memories_for_context,
    load_memories,
    save_memory,
    upsert_l2,
    upsert_profile,
)

client = TestClient(app)


def _l1(session_id: str, content: str, ts: str) -> Memory:
    return Memory(level="L1", content=content, timestamp=ts, session_id=session_id)


def test_memory_dataclass_fields():
    """Memory 四字段齐备；L5 的 session_id 为 None（画像属于用户而非会话）。"""
    m = Memory(
        level="L1",
        content="用户在研究注意力机制",
        timestamp="2026-01-01T00:00:00+00:00",
        session_id="s1",
    )
    assert m.level == "L1"
    assert m.content == "用户在研究注意力机制"
    assert m.timestamp == "2026-01-01T00:00:00+00:00"
    assert m.session_id == "s1"

    profile = Memory(
        level="L5", content="画像", timestamp="2026-01-01T00:00:00+00:00", session_id=None
    )
    assert profile.session_id is None


def test_save_load_roundtrip():
    """save_memory 落库 → load_memories 读回，字段逐项一致（真 MongoDB 往返）。"""
    sid = f"test-rt-{uuid4()}"
    original = _l1(sid, "往返测试事实", "2026-01-02T00:00:00+00:00")
    save_memory(original)

    loaded = load_memories(session_id=sid, level="L1")
    assert len(loaded) == 1
    assert loaded[0] == original  # dataclass 按字段相等比较


def test_get_memories_for_context():
    """注入组合：L5 画像在前 + 本会话记忆时间倒序 + 其他会话被隔离 + limit 生效。"""
    sid = f"test-ctx-{uuid4()}"
    other = f"test-other-{uuid4()}"

    # 时间戳手工递增——排序断言才有确定结果（ISO 字符串按字典序即时间序）
    save_memory(_l1(sid, "事实-1", "2026-01-01T00:00:01+00:00"))
    save_memory(_l1(sid, "事实-2", "2026-01-01T00:00:02+00:00"))
    save_memory(_l1(sid, "事实-3", "2026-01-01T00:00:03+00:00"))
    save_memory(
        Memory(level="L2", content="会话摘要", timestamp="2026-01-01T00:00:04+00:00", session_id=sid)
    )
    save_memory(_l1(other, "别家会话的事实", "2026-01-01T00:00:05+00:00"))

    # L5 全局唯一——先备份库中现有画像，测完恢复（经公开 API，绕开私有集合）
    before = load_memories(level="L5")
    backup = before[0] if before else None
    upsert_profile(
        Memory(level="L5", content="测试画像", timestamp="2026-01-01T00:00:06+00:00", session_id=None)
    )
    try:
        mems = get_memories_for_context(sid)
        assert mems[0].level == "L5"  # 画像恒在注入窗口最前
        session_part = [m for m in mems if m.level != "L5"]
        assert [m.content for m in session_part] == ["会话摘要", "事实-3", "事实-2", "事实-1"]  # 时间倒序
        assert all(m.session_id == sid for m in session_part)  # 其他会话被隔离
        assert "别家会话的事实" not in [m.content for m in mems]

        limited = get_memories_for_context(sid, limit=2)
        assert [m.content for m in limited if m.level != "L5"] == ["会话摘要", "事实-3"]  # limit 生效
    finally:
        if backup is not None:
            upsert_profile(backup)  # 恢复原有画像内容


def test_injection_window_default():
    """缺省注入窗口 = 2×L2_TRIGGER_THRESHOLD 联动派生（行为级断言，零 LLM）。"""
    sid = f"test-win-{uuid4()}"
    for i in range(2 * L2_TRIGGER_THRESHOLD + 5):  # 故意多攒 5 条
        save_memory(_l1(sid, f"事实-{i}", f"2026-01-01T00:{i // 60:02d}:{i % 60:02d}+00:00"))

    mems = get_memories_for_context(sid)
    session_part = [m for m in mems if m.session_id == sid]
    assert len(session_part) == 2 * L2_TRIGGER_THRESHOLD  # 恰好 20 条，L2 永不被淹


def test_upsert_l2_idempotent():
    """同一会话二次 upsert：更新同一条而非新增，返回同一 _id。"""
    sid = f"test-l2-{uuid4()}"
    id1 = upsert_l2(
        Memory(level="L2", content="第一版摘要", timestamp="2026-01-01T00:00:00+00:00", session_id=sid)
    )
    id2 = upsert_l2(
        Memory(level="L2", content="第二版摘要", timestamp="2026-01-01T00:00:01+00:00", session_id=sid)
    )
    assert id1 == id2
    l2s = load_memories(session_id=sid, level="L2")
    assert len(l2s) == 1
    assert l2s[0].content == "第二版摘要"


def test_upsert_profile_idempotent():
    """画像幂等键是 level="L5" 全局一条：二次 upsert 更新，全库仍只有一条 L5。"""
    before = load_memories(level="L5")
    backup = before[0] if before else None
    try:
        id1 = upsert_profile(
            Memory(level="L5", content="测试画像A", timestamp="2026-01-01T00:00:00+00:00", session_id=None)
        )
        id2 = upsert_profile(
            Memory(level="L5", content="测试画像B", timestamp="2026-01-01T00:00:01+00:00", session_id=None)
        )
        assert id1 == id2
        l5s = load_memories(level="L5")
        assert len(l5s) == 1  # 全库恰一条
        assert l5s[0].content == "测试画像B"
    finally:
        if backup is not None:
            upsert_profile(backup)


def test_consolidate_endpoint_guard():
    """空输入守卫：无 L1 的会话请求整合 → 422（进入 LLM 之前就被拦下）。"""
    sid = f"test-empty-{uuid4()}"
    resp = client.post("/api/consolidate", json={"session_id": sid})
    assert resp.status_code == 422


def test_prompts_keys_and_format():
    """PROMPTS 四键就位，且占位符与调用点传参集匹配（.format 静态验证，零 LLM）。"""
    assert set(PROMPTS) == {"persona", "l1_extract", "l2_consolidate", "l5_profile"}
    assert "{" not in PROMPTS["persona"].format()  # 人设无占位符
    assert "问题" in PROMPTS["l1_extract"].format(
        recent_block="（无）", user="我的问题", agent="回答"
    )
    assert "要点" in PROMPTS["l2_consolidate"].format(facts="- 要点1\n- 要点2")
    assert "背景" in PROMPTS["l5_profile"].format(
        previous_block="（无）", summaries="- 用户背景是研究员"
    )
