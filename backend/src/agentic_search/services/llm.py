from langchain.chat_models import init_chat_model

from agentic_search.configs.config import settings

llm = init_chat_model(
    model=settings.llm_model,
    model_provider=settings.llm_model_provider,
    base_url=settings.llm_base_url,
    api_key=settings.llm_api_key,
    timeout=settings.llm_timeout,
)


def call_llm(prompt: str) -> str:
    """裸 LLM 调用（无工具绑定），记忆提取/整合用。"""
    return llm.invoke(prompt).content
