"""从 output/export JSON 构建 Chroma 向量库。"""

import json
import shutil
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    AI_EXPORT_PATH,
    AI_VECTORS_PATH,
    DEFAULT_FETCH_K,
    DEFAULT_K,
    EMBEDDING_CHUNK_OVERLAP,
    EMBEDDING_CHUNK_SIZE,
    OLLAMA_EMBEDDING_MODEL,
    SOURCE_COZE,
    SOURCE_VIDEO,
    SOURCE_WEIXIN,
)


def load_export_documents(export_root: Path) -> list[Document]:
    documents: list[Document] = []
    for json_path in sorted(export_root.rglob("*.json")):
        if "_errors" in json_path.parts:
            continue
        data = json.loads(json_path.read_text(encoding="utf-8"))
        source = data.get("source", "")

        if source in (SOURCE_COZE, SOURCE_WEIXIN):
            questions = data.get("questions", [])
            page_content = "\n".join(questions) if questions else data.get("answer", "")
            metadata = {
                "id": data.get("id", ""),
                "source": source,
                "source_file": data.get("source_file", ""),
                "answer": data.get("answer", ""),
                "content_type": "qa",
            }
        elif source == SOURCE_VIDEO:
            page_content = data.get("text", "")
            metadata = {
                "id": data.get("id", ""),
                "source": source,
                "source_file": data.get("metadata", {}).get("source_file", ""),
                "text": page_content,
                "segment_index": data.get("segment_index", 0),
                "content_type": "segment",
            }
        else:
            continue

        if not page_content.strip():
            continue

        documents.append(Document(page_content=page_content, metadata=metadata))

    return documents


def split_for_embedding(documents: list[Document]) -> list[Document]:
    """将超长文本切分为适合 bge-m3 嵌入的块。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=EMBEDDING_CHUNK_SIZE,
        chunk_overlap=EMBEDDING_CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata.setdefault("parent_id", chunk.metadata.get("id", ""))
        chunk.metadata["chunk_index"] = i
    return chunks


def build_vector_store(rebuild: bool = True) -> tuple[Chroma, int]:
    docs = load_export_documents(AI_EXPORT_PATH)
    if not docs:
        raise FileNotFoundError(f"未找到 export JSON: {AI_EXPORT_PATH}")

    chunks = split_for_embedding(docs)

    if rebuild and AI_VECTORS_PATH.exists():
        shutil.rmtree(AI_VECTORS_PATH)

    AI_VECTORS_PATH.mkdir(parents=True, exist_ok=True)
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBEDDING_MODEL)
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(AI_VECTORS_PATH),
    )
    return vectordb, len(chunks)


def get_retriever(vectordb: Chroma, k: int = DEFAULT_K, fetch_k: int = DEFAULT_FETCH_K):
    return vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": fetch_k},
    )


if __name__ == "__main__":
    db, count = build_vector_store(rebuild=True)
    print(f"向量库已构建: {AI_VECTORS_PATH}")
    print(f"文档块数: {count}")
