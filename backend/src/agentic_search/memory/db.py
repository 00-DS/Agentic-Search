from dataclasses import asdict, dataclass

from pymongo import MongoClient

from agentic_search.configs.config import settings

_client = MongoClient(settings.mongo_url)
_db = _client[settings.mongo_db]
_memories_collection = _db["memories"]


@dataclass
class Memory:
    """memories 集合文档的 Python 形态。"""

    level: str  # "L1"、"L2" 或 "L5"，标识记忆层级
    content: str  # 记忆的实际内容（L1 一条事实，L2 一段摘要，L5 一段画像）
    timestamp: str  # ISO 8601 时间戳，记录记忆生成时刻
    session_id: str  # 所属会话 ID；L5 为 None——画像属于用户而非任何一次会话


def save_memory(memory: Memory):
    _memories_collection.insert_one(asdict(memory))


def load_memories(
    session_id: str | None = None, level: str | None = None, limit: int | None = None
) -> list[Memory]:
    query = {}
    if session_id is not None:
        query["session_id"] = session_id
    if level is not None:
        query["level"] = level
    docs = _memories_collection.find(query).sort("timestamp", -1)
    if limit is not None:
        docs = docs.limit(limit)
    memories = []
    for doc in docs:
        doc.pop("_id", None)
        memories.append(Memory(**doc))
    return memories


def upsert_l2(l2: Memory) -> str:

    existing = _memories_collection.find_one(
        {"session_id": l2.session_id, "level": "L2"}
    )

    if existing is None:
        return str(_memories_collection.insert_one(asdict(l2)).inserted_id)
    else:
        _memories_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {"content": l2.content, "timestamp": l2.timestamp}},
        )
        return str(existing["_id"])


def upsert_profile(profile: Memory) -> str:

    existing = _memories_collection.find_one({"level": "L5"})
    if existing is None:
        return str(_memories_collection.insert_one(asdict(profile)).inserted_id)
    _memories_collection.update_one(
        {"_id": existing["_id"]},
        {"$set": {"content": profile.content, "timestamp": profile.timestamp}},
    )
    return str(existing["_id"])


L2_TRIGGER_THRESHOLD = 10


def get_memories_for_context(
    session_id: str, limit: int = 2 * L2_TRIGGER_THRESHOLD
) -> list[Memory]:
    memories = load_memories(level="L5")  # 全局至多一条画像
    memories += load_memories(
        session_id=session_id, limit=limit
    )  # 本会话 L1+L2，时间倒序取前 N
    return memories
