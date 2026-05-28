"""DeepSeek API 封装：加载提示词、调用模型、解析 JSON。"""

import json
import re
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TEMPERATURE,
    JSON_RETRY_COUNT,
)


def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_json(text: str) -> dict[str, Any]:
    """从模型输出中提取 JSON 对象。"""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
        raise


class DeepSeekClient:
    def __init__(self, temperature: float | None = None):
        self.llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model=DEEPSEEK_MODEL,
            temperature=temperature if temperature is not None else DEEPSEEK_TEMPERATURE,
        )

    def chat(self, system_prompt: str, user_content: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content),
        ]
        response = self.llm.invoke(messages)
        return response.content or ""

    def chat_json(
        self,
        system_prompt: str,
        user_content: str,
        retries: int | None = None,
    ) -> dict[str, Any]:
        retries = JSON_RETRY_COUNT if retries is None else retries
        last_error: Exception | None = None
        content = user_content
        for attempt in range(retries + 1):
            raw = self.chat(system_prompt, content)
            try:
                return extract_json(raw)
            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                if attempt < retries:
                    content = (
                        f"{user_content}\n\n"
                        "请严格只输出合法 JSON，不要包含 markdown 代码块外的其他文字。"
                    )
        raise ValueError(f"无法解析 JSON: {last_error}") from last_error
