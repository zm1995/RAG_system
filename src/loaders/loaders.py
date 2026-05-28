"""
多格式文档加载器
支持：Markdown、PDF、Word、TXT、网页URL
"""

import os
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    WebBaseLoader,
)
from langchain_core.documents import Document


class MultiFormatLoader:
    """多格式文档加载器"""

    def __init__(self, knowledge_base_path: str):
        self.kb_path = Path(knowledge_base_path)
        self.supported_extensions = {
            '.md': self.load_markdown,
            '.txt': self.load_text,
            '.pdf': self.load_pdf,
            '.docx': self.load_word,
            '.doc': self.load_word,
        }

    def load_markdown(self, filepath: Path) -> List[Document]:
        """加载 Markdown 文件"""
        from langchain_community.document_loaders import TextLoader
        loader = TextLoader(str(filepath), encoding='utf-8')
        return loader.load()

    def load_text(self, filepath: Path) -> List[Document]:
        """加载纯文本文件"""
        loader = TextLoader(str(filepath), encoding='utf-8')
        return loader.load()

    def load_pdf(self, filepath: Path) -> List[Document]:
        """加载 PDF 文件"""
        loader = PyPDFLoader(str(filepath))
        return loader.load()

    def load_word(self, filepath: Path) -> List[Document]:
        """加载 Word 文档"""
        loader = UnstructuredWordDocumentLoader(str(filepath))
        return loader.load()

    def load_from_url(self, url: str, title: Optional[str] = None) -> List[Document]:
        """从网页加载内容"""
        loader = WebBaseLoader(url)
        docs = loader.load()

        # 添加元数据
        for doc in docs:
            doc.metadata['source_url'] = url
            doc.metadata['source_type'] = 'web'
            if title:
                doc.metadata['title'] = title

        return docs

    def load_folder(self, folder_path: str, recursive: bool = True) -> List[Document]:
        """加载文件夹中的所有支持格式"""
        all_docs = []
        folder = Path(folder_path)

        for ext, loader_func in self.supported_extensions.items():
            pattern = f"**/*{ext}" if recursive else f"*{ext}"
            for filepath in folder.glob(pattern):
                try:
                    print(f"📄 加载: {filepath}")
                    docs = loader_func(filepath)
                    for doc in docs:
                        doc.metadata['source'] = str(filepath)
                        doc.metadata['source_type'] = ext[1:]  # 去掉点
                    all_docs.extend(docs)
                except Exception as e:
                    print(f"❌ 加载失败 {filepath}: {e}")

        return all_docs
