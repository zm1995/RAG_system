"""weixinchat：从 Excel/CSV 的 Q&A 扩展为 5问1答。"""

from pathlib import Path

import pandas as pd

from src.config import (
    PROMPT_WEIXIN,
    SOURCE_WEIXIN,
    WEIXIN_ANSWER_COL,
    WEIXIN_QUESTION_COL,
)
from src.llm.deepseek_client import DeepSeekClient, load_prompt
from src.processors.base import BaseProcessor


class WeixinProcessor(BaseProcessor):
    source_name = SOURCE_WEIXIN

    def __init__(self):
        super().__init__()
        self.client = DeepSeekClient()
        self.system_prompt = load_prompt(PROMPT_WEIXIN)

    def list_pending_files(self) -> list[Path]:
        if not self.raw_root.exists():
            return []
        files = []
        for ext in ("*.xlsx", "*.xls", "*.csv"):
            files.extend(self.raw_root.rglob(ext))
        return sorted(files)

    def process_file(self, file_path: Path) -> list[Path]:
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path, encoding="utf-8")
        else:
            df = pd.read_excel(file_path)

        q_col = WEIXIN_QUESTION_COL
        a_col = WEIXIN_ANSWER_COL
        if q_col not in df.columns or a_col not in df.columns:
            raise ValueError(f"缺少列 {q_col}/{a_col}，当前列: {list(df.columns)}")

        exports: list[Path] = []
        stem = file_path.stem

        for idx, row in df.iterrows():
            orig_q = str(row[q_col]).strip()
            orig_a = str(row[a_col]).strip()
            if not orig_q or orig_q == "nan" or not orig_a or orig_a == "nan":
                continue

            user_content = (
                f"原问题：{orig_q}\n\n原答案：{orig_a}\n\n"
                "请生成 5 个相关问题并优化答案。"
            )
            result = self.client.chat_json(self.system_prompt, user_content)

            questions = result.get("questions", [])
            answer = result.get("answer", orig_a)
            if len(questions) < 6:
                raise ValueError(f"行 {idx}: questions 数量不足 ({len(questions)})")

            doc_id = f"{SOURCE_WEIXIN}/{stem}_row_{idx}"
            export_data = {
                "id": doc_id,
                "source": SOURCE_WEIXIN,
                "source_file": str(file_path),
                "questions": questions,
                "answer": answer,
                "metadata": {
                    "original_question": orig_q,
                    "row": int(idx),
                    "sheet": stem,
                },
            }
            out_path = self.export_json_path(f"{stem}_row_{idx}")
            self.write_export(out_path, export_data)
            exports.append(out_path)

        if not exports:
            raise ValueError("文件中没有有效 Q&A 行")

        return exports
