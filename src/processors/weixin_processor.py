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

# 已处理过的 export 格式目录，勿重复 LLM 处理
SKIP_DIR_NAMES = {"问题列表转excel", "问题列表分割"}

# 列名映射：(question_col, answer_col)
COLUMN_ALIASES: list[tuple[str, str]] = [
    (WEIXIN_QUESTION_COL, WEIXIN_ANSWER_COL),
    ("question", "answer"),
]


class WeixinProcessor(BaseProcessor):
    source_name = SOURCE_WEIXIN

    def __init__(self):
        super().__init__()
        self.client = DeepSeekClient()
        self.system_prompt = load_prompt(PROMPT_WEIXIN)

    def list_pending_files(self) -> list[Path]:
        if not self.raw_root.exists():
            return []
        files: list[Path] = []
        for ext in ("*.xlsx", "*.xls", "*.csv"):
            for fp in self.raw_root.rglob(ext):
                if fp.name.startswith("~$"):
                    continue
                if any(part in SKIP_DIR_NAMES for part in fp.parts):
                    continue
                files.append(fp)
        return sorted(files)

    def _resolve_columns(self, df: pd.DataFrame) -> tuple[str, str]:
        for q_col, a_col in COLUMN_ALIASES:
            if q_col in df.columns and a_col in df.columns:
                return q_col, a_col
        raise ValueError(
            f"缺少 Q&A 列，当前列: {list(df.columns)}。"
            f"需要 {WEIXIN_QUESTION_COL}/{WEIXIN_ANSWER_COL} 或 question/answer"
        )

    def _normalize_questions(self, questions: list, orig_q: str) -> list[str]:
        """确保 questions 含 5 个新问 + 原问题（共 6 条）。"""
        items = [str(q).strip() for q in questions if str(q).strip()]
        if orig_q and orig_q not in items:
            items.append(orig_q)
        if len(items) < 5:
            raise ValueError(f"问题数量不足: {len(items)}，需要至少 5 条")
        return items[:6] if len(items) >= 6 else items

    def process_file(self, file_path: Path) -> list[Path]:
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path, encoding="utf-8")
        else:
            df = pd.read_excel(file_path)

        q_col, a_col = self._resolve_columns(df)
        exports: list[Path] = []
        stem = file_path.stem
        row_errors = 0

        for idx, row in df.iterrows():
            orig_q = str(row[q_col]).strip()
            orig_a = str(row[a_col]).strip()
            if not orig_q or orig_q == "nan" or not orig_a or orig_a == "nan":
                continue

            try:
                user_content = (
                    f"原问题：{orig_q}\n\n原答案：{orig_a}\n\n"
                    "请生成 5 个相关问题并优化答案。"
                )
                result = self.client.chat_json(self.system_prompt, user_content)

                questions = self._normalize_questions(result.get("questions", []), orig_q)
                answer = result.get("answer", orig_a) or orig_a

                export_data = {
                    "id": f"{SOURCE_WEIXIN}/{stem}_row_{idx}",
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
            except Exception as e:
                row_errors += 1
                self.log_error(f"{file_path} 行 {idx}: {e}")

        if not exports:
            raise ValueError(
                f"文件中没有成功导出的行（跳过/失败 {row_errors} 行）"
            )
        if row_errors:
            self.log_error(f"{file_path}: 部分行失败 {row_errors} 行，已成功 {len(exports)} 行")

        return exports
