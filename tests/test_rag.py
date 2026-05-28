import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
CHROMA_PATH = r"D:\helen\workspace\repositories\RAG_System\chroma_db"

print("🔌 加载向量数据库...")
embeddings = OllamaEmbeddings(model="bge-m3")
vectordb = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)

print("🔍 创建检索器...")
# retriever = vectordb.as_retriever(search_kwargs={"k": 8})

retriever = vectordb.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 6, "fetch_k": 12}
)

print("🤖 加载语言模型...")
llm = OllamaLLM(model="llama3.2:3b")


# 优化的 Prompt
prompt_template = """你是我的个人知识库助手。你的唯一任务是根据下面提供的笔记内容回答问题。

笔记内容：
{context}

用户问题：{question}

规则：
1. 如果笔记内容里有答案，直接用笔记中的原话或提炼后回答
2. 如果笔记内容里没有答案，只说"笔记中没有相关信息"，不要编造
3. 回答要简洁、准确

回答："""

PROMPT = PromptTemplate(
    template=prompt_template,
    input_variables=["context", "question"]
)


print("⛓️ 创建问答链...")
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": PROMPT},
    verbose=False
)

# 测试问题（基于你的笔记内容）
questions = [
    "什么是 RAG？",
    "如何通过 Obsidian 构建本地 RAG 知识库？",
    "什么是默克尔树？"
]

for question in questions:
    print(f"\n{'='*50}")
    print(f"❓ 问题: {question}")
    result = qa_chain.invoke({"query": question})
    print(f"💡 回答: {result['result']}")
    print(f"\n📚 参考来源:")
    for i, doc in enumerate(result['source_documents'][:3]):
        filename = doc.metadata['source'].split('MyKnowledge_export')[-1]
        print(f"   {i+1}. {filename}")
