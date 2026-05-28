"""
个人知识库 RAG 智能助手 - DeepSeek API 版本
更快、更准、支持多轮对话
"""

import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_core.prompts import PromptTemplate
import os

# 导入配置
from config import *

# ========== 页面配置 ==========
st.set_page_config(
    page_title="个人知识库助手 (DeepSeek)",
    page_icon="🚀",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        color: #4CAF50;
        text-align: center;
    }
    .badge {
        background-color: #4CAF50;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ========== 加载 RAG 链 ==========


@st.cache_resource
def load_rag_chain(k_value, fetch_k_value):
    """加载 DeepSeek 版本的 RAG 链"""

    with st.spinner("🔌 加载向量数据库..."):
        embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
        vectordb = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings
        )

    with st.spinner("🔍 创建检索器..."):
        retriever = vectordb.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k_value, "fetch_k": fetch_k_value}
        )

    with st.spinner("🤖 连接 DeepSeek API..."):
        llm = ChatOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model=DEEPSEEK_MODEL,
            temperature=0.1,      # 降低随机性，提高准确性
            streaming=True        # 流式输出
        )

    # 优化的 Prompt
    prompt_template = """你是我的个人知识库助手。根据以下笔记内容回答问题。

【对话历史】
{chat_history}

【用户问题】
{question}

【笔记内容】
{context}

规则：
1. 结合对话历史理解问题
2. 只根据笔记内容回答，不要编造
3. 如果笔记中没有答案，说"笔记中没有相关信息"
4. 回答简洁准确，可以用中文

回答："""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["chat_history", "question", "context"]
    )

    # 对话记忆
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    # 创建对话链
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": PROMPT},
        return_source_documents=True,
        verbose=False
    )

    return qa_chain


# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown("## ⚙️ 设置")

    k_value = st.slider("检索文档数 (k)", 1, 10, DEFAULT_K)
    fetch_k_value = st.slider("MMR 候选池", k_value, 20,
                              max(DEFAULT_FETCH_K, k_value + 2))

    st.markdown("---")
    st.markdown("### 📊 系统状态")
    st.markdown(f"- **后端**: 🚀 DeepSeek API")
    st.markdown(f"- **模型**: `{DEEPSEEK_MODEL}`")
    st.markdown(f"- **嵌入**: `{OLLAMA_EMBEDDING_MODEL}`")
    st.markdown(f"- **检索**: MMR (k={k_value})")

    st.markdown("---")

    if st.button("🗑️ 清除对话", use_container_width=True):
        st.session_state.messages = []
        st.cache_resource.clear()
        st.rerun()

    st.markdown("---")
    st.caption("💡 DeepSeek API 速度快、质量高")
    st.caption("💰 价格: ¥1 ≈ 100万 token")

    # 在侧边栏添加按钮
    if st.button("💾 导出今日对话", use_container_width=True):
        from datetime import datetime
        export_content = f"# RAG 对话记录 - {datetime.now()}\n\n"
        for msg in st.session_state.messages:
            role = "用户" if msg["role"] == "user" else "助手"
            export_content += f"## {role}\n{msg['content']}\n\n"

        export_path = f"D:\\RAG_Exports\\chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(export_content)
        st.success(f"已保存到 {export_path}")

    st.markdown("---")
    st.markdown("### 📊 知识库统计")

    if st.button("🔍 查看统计", use_container_width=True):
        # 统计文档数量
        import sqlite3
        try:
            # Chroma 统计
            collection = vectordb._collection
            count = collection.count()
            st.metric("文档块数", count)
        except:
            st.info("无法获取统计信息")


# ========== 主界面 ==========
st.markdown('<div class="main-header">🚀 个人知识库助手 <span class="badge">DeepSeek 版</span></div>',
            unsafe_allow_html=True)
st.caption("基于你的 Obsidian 笔记 + DeepSeek API")

# 加载链
qa_chain = load_rag_chain(k_value, fetch_k_value)

# 会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and "sources" in msg:
            with st.expander("📚 参考来源"):
                for src in msg["sources"]:
                    short = src.split(
                        "MyKnowledge_export")[-1].split("MyKnowledge")[-1]
                    st.markdown(f"- `{short}`")

# 输入处理
if prompt := st.chat_input("问你的知识库..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("🔍 检索中..."):
            try:
                result = qa_chain.invoke({"question": prompt})
                answer = result["answer"]
                sources = [doc.metadata["source"]
                           for doc in result["source_documents"]]

                st.markdown(answer)

                if sources:
                    with st.expander(f"📚 参考来源 ({len(sources)})"):
                        for src in sources[:5]:
                            short = src.split(
                                "MyKnowledge_export")[-1].split("MyKnowledge")[-1]
                            st.markdown(f"- `{short}`")

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })
            except Exception as e:
                st.error(f"❌ 错误: {e}")

# 在 app_deepseek.py 底部添加
with st.expander("🔧 高级功能"):
    uploaded_file = st.file_uploader("批量提问（上传 txt 文件，每行一个问题）", type=["txt"])
    if uploaded_file:
        questions = uploaded_file.read().decode().splitlines()
        if st.button("运行批量测试"):
            results = []
            for q in questions:
                if q.strip():
                    result = qa_chain.invoke({"question": q})
                    results.append(f"Q: {q}\nA: {result['answer']}\n")
            st.download_button("下载结果", "\n\n".join(
                results), "batch_results.txt")
