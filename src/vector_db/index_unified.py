"""
统一索引构建器 — 将 Obsidian 笔记和 AI 助教知识库合并到一个 Chroma 向量库。

用法:
    python src/vector_db/index_unified.py              # 全量重建
    python src/vector_db/index_unified.py --obsidian-only  # 仅增量更新 Obsidian
    python src/vector_db/index_unified.py --skip-obsidian
    python src/vector_db/index_unified.py --skip-assistant
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import (
    AI_EXPORT_PATH,
    CHROMA_DIR,
    EMBEDDING_CHUNK_OVERLAP,
    EMBEDDING_CHUNK_SIZE,
    EMBED_BATCH_SIZE,
    EMBED_RETRY_COUNT,
    EMBED_RETRY_DELAY_SEC,
    EXPORT_PATH,
    LAST_BUILD_FILE,
    SOURCE_COZE,
    SOURCE_NAME_ASSISTANT,
    SOURCE_NAME_OBSIDIAN,
    SOURCE_VIDEO,
    SOURCE_WEIXIN,
    VAULT_PATH,
)
from src.llm.factory import get_embeddings


def clean_obsidian_syntax(content: str) -> str:
    content = re.sub(r"!\[\[.*?\]\]", "", content)
    content = re.sub(r"\[\[(.*?)\]\]", r"\1", content)
    return content


def load_obsidian_documents(*, prefer_vault: bool = False) -> list[Document]:
    if prefer_vault and os.path.exists(VAULT_PATH):
        docs_path = VAULT_PATH
    else:
        docs_path = EXPORT_PATH if os.path.exists(EXPORT_PATH) else VAULT_PATH
    if not os.path.exists(docs_path):
        print(f"  ⚠️ Obsidian 路径不存在: {docs_path}")
        return []

    documents: list[Document] = []
    for filepath in Path(docs_path).rglob("*.md"):
        if "90_Templates" in str(filepath):
            continue
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  ❌ 读取失败 {filepath}: {e}")
            continue

        metadata: dict = {
            "source": str(filepath),
            "source_type": "markdown",
            "source_name": SOURCE_NAME_OBSIDIAN,
        }
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                metadata["frontmatter"] = parts[1]
                content = parts[2]

        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        content = clean_obsidian_syntax(content)
        if not content.strip():
            continue

        rel_path = filepath.relative_to(Path(docs_path))
        metadata["id"] = f"obsidian/{rel_path.with_suffix('')}".replace("\\", "/")
        documents.append(Document(page_content=content, metadata=metadata))

    return documents


def load_assistant_documents() -> list[Document]:
    if not AI_EXPORT_PATH.exists():
        print(f"  ⚠️ AI 助教导出路径不存在: {AI_EXPORT_PATH}")
        return []

    documents: list[Document] = []
    for json_path in sorted(AI_EXPORT_PATH.rglob("*.json")):
        if "_errors" in json_path.parts:
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  ❌ JSON 解析失败 {json_path}: {e}")
            continue

        source = data.get("source", "")

        if source in (SOURCE_COZE, SOURCE_WEIXIN):
            questions = data.get("questions", [])
            page_content = "\n".join(questions) if questions else data.get("answer", "")
            metadata = {
                "id": data.get("id", ""),
                "source": source,
                "source_name": SOURCE_NAME_ASSISTANT,
                "source_type": "qa",
                "source_file": data.get("source_file", ""),
                "answer": data.get("answer", ""),
            }
            inner = data.get("metadata", {})
            if inner.get("title"):
                metadata["title"] = inner["title"]
            if inner.get("original_question"):
                metadata["original_question"] = inner["original_question"]
        elif source == SOURCE_VIDEO:
            page_content = data.get("text", "")
            metadata = {
                "id": data.get("id", ""),
                "source": source,
                "source_name": SOURCE_NAME_ASSISTANT,
                "source_type": "segment",
                "source_file": data.get("metadata", {}).get("source_file", ""),
                "text": page_content,
                "segment_index": data.get("segment_index", 0),
            }
        else:
            continue

        if not page_content.strip():
            continue
        documents.append(Document(page_content=page_content, metadata=metadata))

    return documents


def split_documents(documents: list[Document]) -> list[Document]:
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


def _count_type(docs: list[Document]) -> dict:
    counts: dict = {}
    for doc in docs:
        st = doc.metadata.get("source_type", "unknown")
        counts[st] = counts.get(st, 0) + 1
    return counts


def _read_build_info() -> dict:
    if LAST_BUILD_FILE.exists():
        try:
            return json.loads(LAST_BUILD_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _chroma_has_data() -> bool:
    if not CHROMA_DIR.exists():
        return False
    return any(CHROMA_DIR.iterdir())


def _is_retryable_embed_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(k in text for k in ("503", "502", "504", "timeout", "connection", "context length"))


def add_documents_batched(vectordb: Chroma, documents: list[Document]) -> None:
    """分批写入向量库，Ollama 503 时自动重试。"""
    if not documents:
        return
    total = len(documents)
    for start in range(0, total, EMBED_BATCH_SIZE):
        batch = documents[start : start + EMBED_BATCH_SIZE]
        batch_no = start // EMBED_BATCH_SIZE + 1
        total_batches = (total + EMBED_BATCH_SIZE - 1) // EMBED_BATCH_SIZE
        for attempt in range(EMBED_RETRY_COUNT):
            try:
                vectordb.add_documents(batch)
                print(f"   嵌入批次 {batch_no}/{total_batches} ({len(batch)} 块)")
                break
            except Exception as e:
                if attempt < EMBED_RETRY_COUNT - 1 and _is_retryable_embed_error(e):
                    wait = EMBED_RETRY_DELAY_SEC * (attempt + 1)
                    print(f"   ⚠️ 嵌入失败，{wait}s 后重试 ({attempt + 1}/{EMBED_RETRY_COUNT}): {e}")
                    time.sleep(wait)
                    continue
                raise RuntimeError(
                    f"嵌入失败（批次 {batch_no}/{total_batches}）。"
                    f"请确认 Ollama 已运行且已 pull bge-m3。原始错误: {e}"
                ) from e


def update_obsidian_only(*, prefer_vault: bool = False) -> tuple[bool, str]:
    """增量更新 Obsidian 切片，保留 AI 助教向量。"""
    docs = load_obsidian_documents(prefer_vault=prefer_vault)
    if not docs:
        return False, "未找到 Obsidian 文档，请先同步 export 目录"

    chunks = split_documents(docs)
    type_counts = _count_type(docs)
    sync_ts = datetime.now().isoformat(timespec="seconds")
    for chunk in chunks:
        chunk.metadata["sync_ts"] = sync_ts

    embeddings = get_embeddings()
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if _chroma_has_data():
            vectordb = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=embeddings,
            )
            if chunks:
                # 先写入新切片，成功后再删旧 Obsidian，避免 delete 后 add 失败导致库空
                add_documents_batched(vectordb, chunks)
                try:
                    vectordb._collection.delete(
                        where={
                            "$and": [
                                {"source_name": SOURCE_NAME_OBSIDIAN},
                                {"sync_ts": {"$ne": sync_ts}},
                            ]
                        }
                    )
                except Exception as e:
                    print(f"   ⚠️ 清理旧 Obsidian 切片失败（或存在无 sync_ts 的旧数据）: {e}")
        else:
            vectordb = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=embeddings,
            )
            add_documents_batched(vectordb, chunks)
    except Exception as e:
        return False, str(e)

    prev = _read_build_info()
    assistant_chunks = prev.get("assistant_chunks", 0)
    merged_type_counts = dict(prev.get("type_counts", {}))
    for k in list(merged_type_counts):
        if k == "markdown":
            del merged_type_counts[k]
    merged_type_counts.update(type_counts)

    info = {
        "timestamp": datetime.now().isoformat(),
        "mode": "obsidian_only",
        "total_documents": len(docs) + prev.get("assistant_documents", 0),
        "total_chunks": len(chunks) + assistant_chunks,
        "type_counts": merged_type_counts,
        "obsidian_chunks": len(chunks),
        "assistant_chunks": assistant_chunks,
        "obsidian_documents": len(docs),
        "assistant_documents": prev.get("assistant_documents", 0),
    }
    LAST_BUILD_FILE.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    return True, f"Obsidian 同步完成：{len(docs)} 篇文档 → {len(chunks)} 个块"


def build_unified_store(
    rebuild: bool = True,
    skip_obsidian: bool = False,
    skip_assistant: bool = False,
) -> tuple[Chroma, int]:
    all_docs: list[Document] = []

    if not skip_obsidian:
        print("📚 [1/2] 加载 Obsidian 笔记...")
        obsidian_docs = load_obsidian_documents()
        print(f"   ✅ {len(obsidian_docs)} 个文档")
        all_docs.extend(obsidian_docs)

    if not skip_assistant:
        print("🎓 [2/2] 加载 AI 助教知识库...")
        assistant_docs = load_assistant_documents()
        print(f"   ✅ {len(assistant_docs)} 个文档")
        all_docs.extend(assistant_docs)

    if not all_docs:
        raise FileNotFoundError("没有找到任何文档，请检查数据路径配置。")

    type_counts = _count_type(all_docs)
    print(f"\n📊 文档类型分布: {type_counts}")

    print("✂️ 分块中...")
    chunks = split_documents(all_docs)
    print(f"   ✅ {len(chunks)} 个块")

    if rebuild and CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
        print(f"   🗑️ 已删除旧向量库: {CHROMA_DIR}")

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    print("🧠 生成向量索引...")
    embeddings = get_embeddings()
    vectordb = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )
    add_documents_batched(vectordb, chunks)

    obsidian_docs_count = sum(1 for d in all_docs if d.metadata.get("source_name") == SOURCE_NAME_OBSIDIAN)
    assistant_docs_count = len(all_docs) - obsidian_docs_count
    obsidian_chunks = sum(1 for c in chunks if c.metadata.get("source_name") == SOURCE_NAME_OBSIDIAN)
    assistant_chunks = len(chunks) - obsidian_chunks

    info = {
        "timestamp": datetime.now().isoformat(),
        "mode": "full",
        "total_documents": len(all_docs),
        "total_chunks": len(chunks),
        "type_counts": type_counts,
        "obsidian_chunks": obsidian_chunks,
        "assistant_chunks": assistant_chunks,
        "obsidian_documents": obsidian_docs_count,
        "assistant_documents": assistant_docs_count,
    }
    LAST_BUILD_FILE.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n✅ 统一向量库构建完成！")
    print(f"📁 路径: {CHROMA_DIR}")
    print(f"📊 统计: {len(all_docs)} 个文档 → {len(chunks)} 个块")

    return vectordb, len(chunks)


def main():
    parser = argparse.ArgumentParser(description="构建统一 RAG 向量库")
    parser.add_argument("--obsidian-only", action="store_true", help="仅增量更新 Obsidian")
    parser.add_argument("--skip-obsidian", action="store_true", help="跳过 Obsidian 笔记")
    parser.add_argument("--skip-assistant", action="store_true", help="跳过 AI 助教知识库")
    args = parser.parse_args()

    print("=" * 50)
    print("🚀 统一知识库索引构建器")
    print("=" * 50)

    if args.obsidian_only:
        ok, msg = update_obsidian_only()
        print(msg)
        if not ok:
            sys.exit(1)
        return

    print(
        f"数据源: {'Obsidian' if not args.skip_obsidian else ''}"
        f"{' + ' if not args.skip_obsidian and not args.skip_assistant else ''}"
        f"{'AI 助教' if not args.skip_assistant else ''}"
    )
    print()

    db, count = build_unified_store(
        rebuild=True,
        skip_obsidian=args.skip_obsidian,
        skip_assistant=args.skip_assistant,
    )
    _ = db
    print(f"\n🎉 完成！共 {count} 个块。运行 streamlit run web/app.py 启动助手。")


if __name__ == "__main__":
    main()
