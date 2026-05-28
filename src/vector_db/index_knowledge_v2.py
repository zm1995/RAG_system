"""
增强版索引脚本 - 支持 Markdown、PDF、Word、TXT
"""

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
from loaders import MultiFormatLoader
from config import *

# ========== 配置额外的知识库路径 ==========
# 在这里添加你的 PDF、Word 文件夹路径
ADDITIONAL_PATHS = [
    r"D:\helen\documents\papers",     # PDF 论文
    # 示例：r"D:\helen\documents\books",      # 电子书
    r"D:\helen\documents\docs",       # 其他文档
]


def load_all_documents():
    """加载所有格式的文档"""
    all_documents = []
    loader = MultiFormatLoader(EXPORT_PATH)

    # 1. 加载 Obsidian 知识库（Markdown）
    print("📚 [1/2] 加载 Obsidian 知识库...")
    if os.path.exists(EXPORT_PATH):
        md_docs = loader.load_folder(EXPORT_PATH)
        print(f"   ✅ 加载了 {len(md_docs)} 个 Markdown 文档")
        all_documents.extend(md_docs)
    else:
        print(f"   ⚠️ 路径不存在: {EXPORT_PATH}")

    # 2. 加载其他路径的文档（PDF、Word 等）
    if ADDITIONAL_PATHS:
        print("\n📚 [2/2] 加载外部文档...")
        for path in ADDITIONAL_PATHS:
            if Path(path).exists():
                print(f"   📁 扫描: {path}")
                docs = loader.load_folder(path)
                print(f"   ✅ 加载了 {len(docs)} 个文档")
                all_documents.extend(docs)
            else:
                print(f"   ⚠️ 路径不存在: {path}")
    else:
        print("\n📚 [2/2] 跳过（未配置 ADDITIONAL_PATHS）")

    return all_documents


def clean_obsidian_syntax(content: str) -> str:
    """清理 Obsidian 特有语法"""
    content = re.sub(r'\[\[(.*?)\]\]', r'\1', content)  # 双链转文本
    content = re.sub(r'!\[\[.*?\]\]', '', content)      # 移除图片
    return content


def main():
    print("=" * 50)
    print("🚀 增强版知识库索引构建器")
    print("=" * 50)
    print(f"支持格式: Markdown (.md), PDF (.pdf), Word (.docx), 文本 (.txt)\n")

    # 加载文档
    documents = load_all_documents()

    if not documents:
        print("❌ 没有找到任何文档！请检查路径配置。")
        return

    print(f"\n📊 总计加载了 {len(documents)} 个文档")

    # 按类型统计
    type_stats = {}
    for doc in documents:
        doc_type = doc.metadata.get('source_type', 'unknown')
        type_stats[doc_type] = type_stats.get(doc_type, 0) + 1

    print("\n📈 文档类型分布:")
    for doc_type, count in type_stats.items():
        print(f"   - {doc_type}: {count} 个")

    # 清理内容
    print("\n🧹 清理文档格式...")
    for doc in documents:
        doc.page_content = clean_obsidian_syntax(doc.page_content)

    # 分块
    print("✂️ 切分文档块...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   ✅ 切分为 {len(chunks)} 个块")

    # 创建向量库
    print("🧠 生成向量索引...")
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)

    # 删除旧的向量库（重新构建）
    import shutil
    if os.path.exists(CHROMA_PATH):
        print(f"   🗑️ 删除旧向量库: {CHROMA_PATH}")
        shutil.rmtree(CHROMA_PATH)

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    print(f"\n✅ 索引完成！")
    print(f"📁 向量库保存在: {CHROMA_PATH}")
    print(f"📊 统计: {len(documents)} 个文档 → {len(chunks)} 个文本块")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    main()
