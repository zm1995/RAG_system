"""阶段二：从 export JSON 构建向量库。"""

import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.vector_db.index_qa_json import build_vector_store


def main():
    vectordb, count = build_vector_store(rebuild=True)
    print(f"向量库构建完成，共索引 {count} 个嵌入块。")
    _ = vectordb


if __name__ == "__main__":
    main()
