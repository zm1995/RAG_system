import os
import re
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
# 配置路径
VAULT_PATH = r"D:\helen\workspace\repositories\brain\MyKnowledge"  # 你的 Obsidian 库路径
EXPORT_PATH = r"D:\helen\workspace\repositories\brain\MyKnowledge_export"  # 导出的纯净版路径（优先使用）
CHROMA_PATH = r"D:\helen\workspace\repositories\RAG_System\chroma_db"  # 向量数据库存储位置


def load_markdown_files(folder_path):
    """递归加载所有 .md 文件"""
    documents = []
    for filepath in Path(folder_path).glob("**/*.md"):
        # 跳过模板文件
        if "90_Templates" in str(filepath):
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单清理 Obsidian 特有语法
            content = re.sub(r'\[\[(.*?)\]\]', r'\1', content)  # 转换双链
            content = re.sub(r'!\[\[.*?\]\]', '', content)      # 移除图片

            # 提取 frontmatter 中的元数据
            metadata = {"source": str(filepath)}
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    # 保留 frontmatter 供后续解析
                    metadata["frontmatter"] = parts[1]
                    content = parts[2]

            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        except Exception as e:
            print(f"读取失败 {filepath}: {e}")
    return documents


def main():
    print("📂 加载 Markdown 文件...")
    # 优先使用导出的纯净版本，否则用原库
    docs_path = EXPORT_PATH if os.path.exists(EXPORT_PATH) else VAULT_PATH
    documents = load_markdown_files(docs_path)
    print(f"✅ 加载了 {len(documents)} 个文档")

    print("✂️ 切分文档块...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✅ 切分为 {len(chunks)} 个块")

    print("🧠 初始化 Ollama 嵌入模型...")
    embeddings = OllamaEmbeddings(model="bge-m3")

    print("💾 创建向量数据库...")
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )
    vectordb.persist()
    print(f"✅ 向量数据库已保存到 {CHROMA_PATH}")


if __name__ == "__main__":
    main()
