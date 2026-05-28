"""
个人知识库 RAG 智能助手 - Streamlit Web 界面
基于 Obsidian 知识库 + Ollama + LangChain
"""

import streamlit as st
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
import os

# ============================================================
# 配置区域（请根据你的实际路径修改）
# ============================================================

CHROMA_PATH = r"D:\helen\workspace\repositories\RAG_System\chroma_db"

# 模型配置
EMBEDDING_MODEL = "bge-m3"      # 嵌入模型
LLM_MODEL = "llama3.2:3b"        # 对话模型

# 检索配置
DEFAULT_K = 4                    # 默认检索文档数
DEFAULT_FETCH_K = 8              # MMR 候选池大小

# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="个人知识库助手",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS（美化界面）
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4CAF50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .source-item {
        font-size: 0.8rem;
        color: #666;
        padding: 4px;
        border-left: 3px solid #4CAF50;
        margin: 4px 0;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 加载 RAG 链（使用缓存，只加载一次）
# ============================================================


@st.cache_resource
def load_rag_chain(k_value, fetch_k_value):
    """加载向量数据库和问答链"""

    # 检查向量库是否存在
    if not os.path.exists(CHROMA_PATH):
        st.error(f"❌ 向量数据库不存在: {CHROMA_PATH}\n请先运行 index_knowledge.py 构建索引")
        return None

    with st.spinner("🔌 加载向量数据库..."):
        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        vectordb = Chroma(
            persist_directory=CHROMA_PATH,
            embedding_function=embeddings
        )

    with st.spinner("🔍 创建检索器..."):
        retriever = vectordb.as_retriever(
            search_type="mmr",
            search_kwargs={"k": k_value, "fetch_k": fetch_k_value}
        )

    with st.spinner("🤖 加载语言模型..."):
        llm = OllamaLLM(model=LLM_MODEL)

    # 优化的 Prompt 模板
    prompt_template = """你是我的个人知识库助手。请严格根据以下笔记内容回答问题。

【笔记内容】
{context}

【用户问题】
{question}

【回答规则】
1. 如果笔记中有答案，直接回答，可以引用原文
2. 如果笔记中没有答案，只说"笔记中没有相关信息"
3. 不要编造笔记外的内容
4. 回答要简洁、准确

【回答】"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    with st.spinner("⛓️ 创建问答链..."):
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )

    return qa_chain

# ============================================================
# 侧边栏配置
# ============================================================


with st.sidebar:
    st.markdown("## ⚙️ 设置")

    # 检索参数调整
    k_value = st.slider(
        "检索文档数 (k)",
        min_value=1,
        max_value=10,
        value=DEFAULT_K,
        help="值越大，检索到的文档越多，但回答可能变慢"
    )

    fetch_k_value = st.slider(
        "MMR 候选池 (fetch_k)",
        min_value=k_value,
        max_value=20,
        value=max(DEFAULT_FETCH_K, k_value + 2),
        help="MMR 从中选 k 个最不重复的文档"
    )

    st.markdown("---")
    st.markdown("### 📊 系统状态")

    # 显示模型信息
    st.markdown(f"- **嵌入模型**: `{EMBEDDING_MODEL}`")
    st.markdown(f"- **LLM 模型**: `{LLM_MODEL}`")
    st.markdown(f"- **检索模式**: MMR")

    st.markdown("---")

    # 清除历史按钮
    if st.button("🗑️ 清除对话历史", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()

    st.markdown("---")
    st.caption("💡 提示：知识库需要手动更新时，运行 `python index_knowledge.py`")

# ============================================================
# 主界面
# ============================================================

st.markdown('<div class="main-header">📚 个人知识库智能助手</div>',
            unsafe_allow_html=True)
st.markdown("基于你的 Obsidian 笔记，回答任何问题")

# 加载 RAG 链
qa_chain = load_rag_chain(k_value, fetch_k_value)

if qa_chain is None:
    st.stop()

# ============================================================
# 会话状态初始化
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

# ============================================================
# 显示历史消息
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # 如果是助手回复且有来源，显示来源
        if message["role"] == "assistant" and "sources" in message:
            with st.expander("📚 参考来源"):
                for i, source in enumerate(message["sources"], 1):
                    # 简化路径显示
                    short_path = source.split(
                        "MyKnowledge_export")[-1].split("MyKnowledge")[-1]
                    st.markdown(f'{i}. `{short_path}`')

# ============================================================
# 聊天输入处理
# ============================================================

if prompt := st.chat_input("问你的知识库..."):
    # 显示用户消息
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 调用 RAG
    with st.chat_message("assistant"):
        with st.spinner("🔍 检索知识库..."):
            try:
                result = qa_chain.invoke({"query": prompt})
                answer = result["result"]
                sources = [doc.metadata["source"]
                           for doc in result["source_documents"]]

                # 显示回答
                st.markdown(answer)

                # 显示来源（可折叠）
                if sources:
                    with st.expander(f"📚 参考来源 ({len(sources)} 个)"):
                        for i, src in enumerate(sources, 1):
                            short_path = src.split(
                                "MyKnowledge_export")[-1].split("MyKnowledge")[-1]
                            st.markdown(f'{i}. `{short_path}`')

                # 保存到会话历史
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            except Exception as e:
                st.error(f"❌ 出错: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"抱歉，发生了错误: {e}"
                })

# ============================================================
# 页脚
# ============================================================

st.markdown("---")
st.caption(
    f"📝 知识库已就绪 | 检索参数: k={k_value}, fetch_k={fetch_k_value} | 模型: {LLM_MODEL}")

# ============================================================
# 新增：对话记忆管理
# ============================================================

from langchain_classic.memory import ConversationBufferMemory
from langchain_classic.chains import ConversationalRetrievalChain

# 在 load_rag_chain 函数中，替换原来的 RetrievalQA
def load_conversational_chain(k_value, fetch_k_value):
    """加载支持多轮对话的链"""
    
    embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
    vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
    
    retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k_value, "fetch_k": fetch_k_value}
    )
    
    llm = OllamaLLM(model=LLM_MODEL)
    
    # 自定义 prompt（支持历史对话）
    prompt_template = """你是我的个人知识库助手。根据以下对话历史和笔记内容回答问题。

【对话历史】
{chat_history}

【新问题】
{question}

【笔记内容】
{context}

【回答规则】
1. 结合对话历史理解问题（如"它"、"上面说的"等指代）
2. 如果笔记中有答案，直接回答
3. 如果笔记中没有，说"笔记中没有相关信息"
4. 回答简洁准确

【回答】"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["chat_history", "question", "context"]
    )
    
    # 创建记忆
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # 创建对话检索链
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": PROMPT},
        return_source_documents=True,
        verbose=False
    )
    
    return qa_chain

# 在侧边栏添加"清除记忆"按钮
with st.sidebar:
    # ... 原有代码 ...
    
    if st.button("🧠 清除对话记忆", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        # 重新加载链（重置 memory）
        st.cache_resource.clear()
        st.rerun()

# 加载支持多轮对话的链
qa_chain = load_conversational_chain(k_value, fetch_k_value)