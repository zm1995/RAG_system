"""coze_knowledge：从 txt 生成 5 问 + 原文 answer。"""

from pathlib import Path

from src.config import PROMPT_COZE, SOURCE_COZE
from src.llm.deepseek_client import DeepSeekClient, load_prompt
from src.processors.base import BaseProcessor


class CozeProcessor(BaseProcessor):
    source_name = SOURCE_COZE

    def __init__(self):
        super().__init__()
        self.client = DeepSeekClient()
        self.system_prompt = load_prompt(PROMPT_COZE)

    def list_pending_files(self) -> list[Path]:
        if not self.raw_root.exists():
            return []
        return sorted(self.raw_root.rglob("*.txt"))

    def process_file(self, file_path: Path) -> list[Path]:
        content = file_path.read_text(encoding="utf-8")
        rel = file_path.relative_to(self.raw_root)
        doc_id = f"{SOURCE_COZE}/{rel.with_suffix('')}".replace("\\", "/")

        result = self.client.chat_json(
            self.system_prompt,
            f"请根据以下 coze 操作文档内容生成 5 个相关问题：\n\n{content}",
        )
        questions = result.get("questions", [])
        if len(questions) < 5:
            raise ValueError(f"问题数量不足: {len(questions)}")

        parts = rel.parts
        if len(parts) >= 3 and parts[0] == "txt":
            category = parts[1]
            title = file_path.stem
        else:
            category = parts[0] if len(parts) > 1 else ""
            title = file_path.stem

        export_data = {
            "id": doc_id,
            "source": SOURCE_COZE,
            "source_file": str(file_path),
            "questions": questions[:5],
            "answer": content,
            "metadata": {"title": title, "category": category},
        }

        out_path = self.export_json_path(doc_id.replace("/", "__"))
        self.write_export(out_path, export_data)
        return [out_path]
