"""
统一知识库 RAG 助手 — Obsidian 个人笔记 + AI 助教知识库
LLM: DeepSeek | 嵌入: Ollama bge-m3
"""

import os
import sys
import json
import subprocess
import datetime
from pathlib import Path

if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from src.config import (
    AI_EXPORT_PATH,
    CHROMA_PATH,
    DEEPSEEK_MODEL,
    DEFAULT_FETCH_K,
    DEFAULT_K,
    EXPORT_PATH,
    LAST_BUILD_FILE,
    OLLAMA_EMBEDDING_MODEL,
    VAULT_PATH,
)
from src.llm.factory import get_chat_llm, get_embeddings
from src.sync.obsidian_sync import sync_obsidian_vectors

SYSTEM_PROMPT_OBSIDIAN = """你是我的个人知识库助手。请严格根据以下参考内容回答问题。
规则：
1. 如果参考内容中有答案，直接回答，可以引用原文
2. 如果参考内容中没有答案，明确说「笔记中没有相关信息」
3. 不要编造参考内容之外的信息
4. 回答简洁准确"""

SYSTEM_PROMPT_ASSISTANT_FILE = ROOT / "docs" / "ai_assistant.md"

SYSTEM_PROMPT_ALL = """你是我的统一知识库助手，可以访问个人笔记和 AI 助教知识库。
请根据参考内容回答问题。参考内容可能来自 Obsidian 笔记、Coze 操作文档、微信答疑记录或课程转写。
规则：
1. 如果参考内容中有答案，直接回答，可以引用原文
2. 如果参考内容中没有答案，明确说「知识库中没有相关信息」
3. 不要编造参考内容之外的信息
4. 回答简洁准确"""

USER_PROMPT_TEMPLATE = """参考内容：
{context}

用户问题：{question}

请基于参考内容回答。若无相关内容，明确说「知识库中没有相关信息」。"""


def load_system_prompt(source_filter: str) -> str:
    if source_filter == "AI 助教":
        if SYSTEM_PROMPT_ASSISTANT_FILE.exists():
            return SYSTEM_PROMPT_ASSISTANT_FILE.read_text(encoding="utf-8")
        return SYSTEM_PROMPT_ALL
    elif source_filter == "个人笔记":
        return SYSTEM_PROMPT_OBSIDIAN
    return SYSTEM_PROMPT_ALL


def get_source_filter_dict(source_filter: str) -> dict | None:
    if source_filter == "个人笔记":
        return {"source_type": "markdown"}
    elif source_filter == "AI 助教":
        return {"source_type": {"$in": ["qa", "segment"]}}
    return None


def format_context(docs) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        meta = doc.metadata
        source_label = meta.get("source", "unknown")
        source_type = meta.get("source_type", "")

        if source_type == "qa":
            body = meta.get("answer", doc.page_content)
        elif source_type == "segment":
            body = meta.get("text", doc.page_content)
        else:
            body = doc.page_content

        parts.append(f"[{i}] 来源: {source_label}\n{body[:2000]}")
    return "\n\n---\n\n".join(parts)


def get_last_build_info():
    if LAST_BUILD_FILE.exists():
        try:
            data = json.loads(LAST_BUILD_FILE.read_text(encoding="utf-8"))
            return data.get("timestamp"), data
        except Exception:
            return None, None
    return None, None


def detect_changed_files(source_dirs, since_timestamp):
    if not since_timestamp:
        return []
    try:
        since_dt = datetime.datetime.fromisoformat(since_timestamp)
    except ValueError:
        return []
    changed = []
    for sdir in source_dirs:
        if not os.path.isdir(sdir):
            continue
        for root, _dirs, files in os.walk(sdir):
            for fname in files:
                if fname.endswith((".md", ".json")):
                    fpath = os.path.join(root, fname)
                    try:
                        mtime_dt = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
                        if mtime_dt > since_dt:
                            changed.append(fpath)
                    except OSError:
                        pass
    return changed


def run_rebuild_index():
    index_script = ROOT / "src" / "vector_db" / "index_unified.py"
    try:
        result = subprocess.run(
            [sys.executable, str(index_script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if result.returncode == 0:
            return True, "全部索引重建成功"
        return False, result.stderr[-500:] if result.stderr else "未知错误"
    except subprocess.TimeoutExpired:
        return False, "重建超时（超过10分钟）"
    except Exception as e:
        return False, str(e)


st.set_page_config(
    page_title="统一知识库助手",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; color: #4CAF50; text-align: center; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_vectordb():
    if not os.path.exists(CHROMA_PATH):
        return None
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embeddings(),
    )


@st.cache_resource
def load_llm():
    return get_chat_llm(streaming=True)


with st.sidebar:
    st.markdown("## ⚙️ 设置")

    source_filter = st.radio(
        "📚 知识库",
        ["全部", "个人笔记", "AI 助教"],
        horizontal=True,
        help="选择检索范围",
    )

    st.markdown("---")
    k_value = st.slider("检索条数 (k)", 1, 10, DEFAULT_K)
    fetch_k_value = st.slider("MMR 候选池", k_value, 20, max(DEFAULT_FETCH_K, k_value + 2))

    st.markdown("---")
    st.markdown("### 📊 系统状态")
    st.markdown(f"- **LLM**: `{DEEPSEEK_MODEL}` (DeepSeek)")
    st.markdown(f"- **嵌入**: `{OLLAMA_EMBEDDING_MODEL}` (Ollama)")
    st.markdown(f"- **向量库**: `{CHROMA_PATH}`")
    st.markdown(f"- **检索范围**: {source_filter}")

    last_ts, last_info = get_last_build_info()
    if last_ts:
        try:
            dt = datetime.datetime.fromisoformat(last_ts)
            delta = datetime.datetime.now() - dt
            if delta.days > 0:
                age_str = f"{delta.days} 天前"
            elif delta.seconds > 3600:
                age_str = f"{delta.seconds // 3600} 小时前"
            else:
                age_str = f"{delta.seconds // 60} 分钟前"
            st.caption(f"📅 索引更新: {age_str}")
            if last_info:
                tc = last_info.get("type_counts", {})
                if tc:
                    parts = [f"{k}:{v}" for k, v in tc.items()]
                    st.caption(f"📊 类型: {', '.join(parts)}")
        except Exception:
            st.caption("📅 索引更新时间: 未知")
    else:
        st.caption("⚠️ 尚未构建索引")

    source_dirs = [d for d in (EXPORT_PATH, VAULT_PATH, str(AI_EXPORT_PATH)) if os.path.isdir(d)]
    changed = detect_changed_files(source_dirs, last_ts)
    if changed:
        st.warning(f"🔄 {len(changed)} 个文件已变更")

    if st.button("📥 同步 Obsidian", use_container_width=True):
        with st.spinner("导出 Obsidian 并更新向量..."):
            ok, msg = sync_obsidian_vectors()
        if ok:
            st.success(msg)
            st.cache_resource.clear()
            st.rerun()
        else:
            st.error(f"同步失败: {msg}")

    if st.button("🔄 重建全部索引", use_container_width=True):
        with st.spinner("正在全量重建（Obsidian + AI 助教）..."):
            ok, msg = run_rebuild_index()
        if ok:
            st.success(msg)
            st.cache_resource.clear()
            st.rerun()
        else:
            st.error(f"重建失败: {msg}")

    st.markdown("---")
    if st.button("🗑️ 清除对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    if st.button("📊 知识库统计", use_container_width=True):
        vectordb = load_vectordb()
        if vectordb:
            try:
                st.metric("总文档块数", vectordb._collection.count())
            except Exception as e:
                st.info(f"无法获取统计: {e}")
        else:
            st.info("向量库不存在")

    if st.button("💾 导出对话", use_container_width=True):
        export_content = f"# 知识库对话记录 - {datetime.datetime.now()}\n\n"
        for msg in st.session_state.get("messages", []):
            role = "用户" if msg["role"] == "user" else "助手"
            export_content += f"## {role}\n{msg['content']}\n\n"
        export_path = f"D:\\RAG_Exports\\chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(export_content)
        st.success(f"已保存到 {export_path}")

    st.caption("💡 AI 助教数据更新后请点「重建全部索引」")

st.markdown(
    '<div class="main-header">🧠 统一知识库助手</div>',
    unsafe_allow_html=True,
)
st.caption("Obsidian 笔记 + AI 助教 · DeepSeek 问答")

vectordb = load_vectordb()
if vectordb is None:
    st.error(
        f"向量库不存在: `{CHROMA_PATH}`\n\n"
        "请先运行 `python src/vector_db/index_unified.py` 或侧边栏「重建全部索引」"
    )
    st.stop()

llm = load_llm()
system_prompt = load_system_prompt(source_filter)
filter_dict = get_source_filter_dict(source_filter)

search_kwargs = {"k": k_value, "fetch_k": fetch_k_value}
if filter_dict:
    search_kwargs["filter"] = filter_dict
retriever = vectordb.as_retriever(search_type="mmr", search_kwargs=search_kwargs)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📚 参考来源"):
                for src in msg["sources"]:
                    st.markdown(f"- `{src}`")

if prompt := st.chat_input("问你的知识库..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🔍 检索中..."):
            docs = retriever.invoke(prompt)
            context = format_context(docs)

            messages = [SystemMessage(content=system_prompt)]
            history = st.session_state.messages[:-1]
            for h in history[-20:]:
                if h["role"] == "user":
                    messages.append(HumanMessage(content=h["content"]))
                else:
                    messages.append(AIMessage(content=h["content"]))

            user_msg = USER_PROMPT_TEMPLATE.format(context=context, question=prompt)
            messages.append(HumanMessage(content=user_msg))

            response_placeholder = st.empty()
            full_response = ""
            for chunk in llm.stream(messages):
                if chunk.content:
                    full_response += chunk.content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)

            sources = [
                d.metadata.get("id", d.metadata.get("source_file", "unknown"))
                for d in docs
            ]
            if sources:
                with st.expander(f"📚 参考来源 ({len(sources)})"):
                    for src in sources[:8]:
                        st.markdown(f"- `{src}`")

            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "sources": sources,
            })

with st.expander("🔧 批量提问"):
    uploaded_file = st.file_uploader("上传 txt 文件（每行一个问题）", type=["txt"])
    if uploaded_file:
        questions = [q.strip() for q in uploaded_file.read().decode().splitlines() if q.strip()]
        if st.button(f"运行批量测试 ({len(questions)} 个问题)"):
            results = []
            progress = st.progress(0, text="处理中...")
            for i, q in enumerate(questions):
                try:
                    docs = retriever.invoke(q)
                    ctx = format_context(docs)
                    msg = USER_PROMPT_TEMPLATE.format(context=ctx, question=q)
                    response = llm.invoke([
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=msg),
                    ])
                    ans = response.content if hasattr(response, "content") else str(response)
                    results.append(f"Q: {q}\nA: {ans}\n")
                except Exception as e:
                    results.append(f"Q: {q}\nA: [错误] {e}\n")
                progress.progress((i + 1) / len(questions), text=f"处理中... ({i + 1}/{len(questions)})")
            progress.empty()
            st.download_button("下载结果", "\n\n".join(results), "batch_results.txt")

st.markdown("---")
st.caption(f"DeepSeek · {source_filter} · k={k_value}, fetch_k={fetch_k_value}")
