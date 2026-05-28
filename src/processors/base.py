"""处理器基类：扫描 raw、写入 export、移动到 processed。"""

import json
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from src.config import AI_ASSISTANT_PROCESSED, AI_ASSISTANT_RAW, AI_ERRORS_PATH, AI_EXPORT_PATH


class BaseProcessor(ABC):
    source_name: str = ""

    def __init__(self):
        self.raw_root = AI_ASSISTANT_RAW / self.source_name
        self.export_root = AI_EXPORT_PATH / self.source_name
        self.processed_root = AI_ASSISTANT_PROCESSED / self.source_name
        self.export_root.mkdir(parents=True, exist_ok=True)
        self.processed_root.mkdir(parents=True, exist_ok=True)
        AI_ERRORS_PATH.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def list_pending_files(self) -> list[Path]:
        ...

    @abstractmethod
    def process_file(self, file_path: Path) -> list[Path]:
        """处理单个文件，返回生成的 export JSON 路径列表。"""

    def export_json_path(self, stem: str, suffix: str = "") -> Path:
        name = f"{stem}{suffix}.json"
        return self.export_root / name

    def write_export(self, path: Path, data: dict) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def move_to_processed(self, raw_path: Path) -> Path:
        rel = raw_path.relative_to(self.raw_root)
        dest = self.processed_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(raw_path), str(dest))
        return dest

    def log_error(self, message: str) -> None:
        log_file = AI_ERRORS_PATH / f"{self.source_name}.log"
        ts = datetime.now().isoformat(timespec="seconds")
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {message}\n")

    def run(self, limit: int | None = None) -> dict:
        files = self.list_pending_files()
        if limit:
            files = files[:limit]

        stats = {"total": len(files), "ok": 0, "fail": 0, "exports": 0}
        for fp in files:
            try:
                exports = self.process_file(fp)
                self.move_to_processed(fp)
                stats["ok"] += 1
                stats["exports"] += len(exports)
            except Exception as e:
                stats["fail"] += 1
                self.log_error(f"{fp}: {e}")
        return stats
