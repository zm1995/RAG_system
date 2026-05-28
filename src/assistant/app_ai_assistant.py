"""
AI 助教知识库问答助手 - DeepSeek + Chroma
"""

import sys
from pathlib import Path

# 确保可从项目根目录导入 src
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI

from src.config import (
    AI_VECTORS_PATH,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEFAULT_FETCH_K,
    DEFAULT_K,
    OLLAMA_EMBEDDING_MODEL,
    PROMPT_ASSISTANT,
)
from src.llm.deepseek_client import load_prompt

st.set_page_config(page_title="AI 助教知识库助手", page_icon="🎓", layout="wide")

USER_PROMPT = """参考内容：
{context}

用户问题：{question}

请基于参考内容回答。若无相关内容，明确说「笔记中没有相关信息」。"""


def format_context(docs) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        source = meta.get("source", "")
        if meta.get("content_type") == "qa":
            body = meta.get("answer", doc.page_content)
        else:
            body = meta.get("text", doc.page_content)
        parts.append(f"[{i}] 来源: {source}\n{body[:2000]}")
    return "\n\n---\n\n".join(parts)


@st.cache_resource
def load_assistant(k_value: int, fetch_k_value: int):
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
    vectordb = Chroma(
        persist_directory=str(AI_VECTORS_PATH),
        embedding_function=embeddings,
    )
    retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k_value, "fetch_k": fetch_k_value},
    )
    llm = ChatOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        model=DEEPSEEK_MODEL,
        temperature=0.1,
        streaming=True,
    )
    system_prompt = load_prompt(PROMPT_ASSISTANT)
    return retriever, llm, system_prompt


def main():
    st.markdown('<div style="text-align:center;font-size:2rem;">🎓 AI 助教知识库助手</div>', unsafe_allow_html=True)
    st.caption("基于 Coze 文档 / 微信答疑 / 课程转写 · DeepSeek API")

    if not AI_VECTORS_PATH.exists():
        st.error(f"向量库不存在，请先运行: python -m src.pipelines.build_vectors")
        st.stop()

    with st.sidebar:
        k_value = st.slider("检索条数 (k)", 1, 10, DEFAULT_K)
        fetch_k_value = st.slider("MMR 候选池", k_value, 20, max(DEFAULT_FETCH_K, k_value + 2))
        if st.button("清除对话"):
            st.session_state.messages = []
            st.rerun()

    retriever, llm, system_prompt = load_assistant(k_value, fetch_k_value)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander("参考来源"):
                    for s in msg["sources"]:
                        st.markdown(f"- `{s}`")

    if prompt := st.chat_input("问 AI 助教..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("检索中..."):
                docs = retriever.invoke(prompt)
                context = format_context(docs)
                user_msg = USER_PROMPT.format(context=context, question=prompt)
                from langchain_core.messages import HumanMessage, SystemMessage

                response = llm.invoke([
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_msg),
                ])
                answer = response.content or ""
                st.markdown(answer)

                sources = [
                    d.metadata.get("id", d.metadata.get("source_file", "unknown"))
                    for d in docs
                ]
                if sources:
                    with st.expander(f"参考来源 ({len(sources)})"):
                        for s in sources[:5]:
                            st.markdown(f"- `{s}`")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources,
                })


main()
