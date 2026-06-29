"""统一 LLM / 嵌入模型工厂。"""

from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI

from src.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TEMPERATURE,
    OLLAMA_EMBEDDING_MODEL,
)


def get_embeddings() -> OllamaEmbeddings:
    """Ollama bge-m3，仅用于向量嵌入。"""
    return OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)


def get_chat_llm(*, streaming: bool = True) -> ChatOpenAI:
    """DeepSeek Chat，用于问答生成。"""
    return ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=DEEPSEEK_TEMPERATURE,
        streaming=streaming,
    )
