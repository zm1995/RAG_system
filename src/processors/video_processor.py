"""class_video_excel：课程转写文本分段导出。"""

from pathlib import Path

from src.config import PROMPT_VIDEO, SOURCE_VIDEO, VIDEO_TEXT_DIRS
from src.llm.deepseek_client import DeepSeekClient, load_prompt
from src.processors.base import BaseProcessor

# 单次送入模型的最大字符数，避免超长
MAX_CHUNK_INPUT = 12000


class VideoProcessor(BaseProcessor):
    source_name = SOURCE_VIDEO

    def __init__(self):
        super().__init__()
        self.client = DeepSeekClient()
        self.system_prompt = load_prompt(PROMPT_VIDEO)

    def _video_roots(self) -> list[Path]:
        return [self.raw_root / name for name in VIDEO_TEXT_DIRS if (self.raw_root / name).exists()]

    def _root_for(self, file_path: Path) -> Path:
        for root in self._video_roots():
            try:
                file_path.relative_to(root)
                return root
            except ValueError:
                continue
        raise ValueError(f"文件不在转写目录下: {file_path}")

    def list_pending_files(self) -> list[Path]:
        files: list[Path] = []
        for root in self._video_roots():
            files.extend(root.rglob("*.txt"))
        return sorted(set(files))

    def _split_first_segment(self, remaining: str) -> tuple[str, str]:
        """调用 LLM 切出第一段，返回 (segment_text, remaining)。"""
        if len(remaining) <= 500:
            return remaining.strip(), ""

        user_content = (
            "课程内容：\n"
            f"{remaining[:MAX_CHUNK_INPUT]}\n\n"
            "请按提示词要求分割并返回第一段 JSON。"
        )
        result = self.client.chat_json(self.system_prompt, user_content)
        text = result.get("text", "").strip()
        if not text:
            raise ValueError("分段结果 text 为空")

        # 从剩余文本中移除已切出的第一段（按原文匹配）
        pos = remaining.find(text[: min(200, len(text))])
        if pos >= 0:
            new_remaining = (remaining[:pos] + remaining[pos + len(text) :]).strip()
        else:
            count = result.get("count", len(text))
            new_remaining = remaining[count:].strip() if isinstance(count, int) else remaining[len(text) :].strip()

        return text, new_remaining

    def process_file(self, file_path: Path) -> list[Path]:
        full_text = file_path.read_text(encoding="utf-8").strip()
        if not full_text:
            raise ValueError("文件为空")

        video_root = self._root_for(file_path)
        rel = file_path.relative_to(video_root)
        base_id = f"{SOURCE_VIDEO}/{rel.with_suffix('')}".replace("\\", "/")
        stem = base_id.replace("/", "__")

        remaining = full_text
        segments: list[str] = []
        seg_idx = 0
        max_segments = 50

        while remaining and seg_idx < max_segments:
            seg_idx += 1
            if len(remaining) < 300 and segments:
                segments.append(remaining)
                break
            text, remaining = self._split_first_segment(remaining)
            segments.append(text)
            if not remaining or remaining == text:
                break

        if len(segments) < 2 and len(full_text) > 300:
            mid = len(full_text) // 2
            split_at = full_text.find("\n", mid)
            if split_at < 0:
                split_at = mid
            segments = [full_text[:split_at].strip(), full_text[split_at:].strip()]

        exports: list[Path] = []
        total = len(segments)
        for i, seg_text in enumerate(segments, start=1):
            if not seg_text:
                continue
            export_data = {
                "id": f"{base_id}_seg_{i:03d}",
                "source": SOURCE_VIDEO,
                "text": seg_text,
                "count": len(seg_text),
                "segment_index": i,
                "metadata": {
                    "source_file": str(file_path),
                    "total_segments": total,
                },
            }
            out_path = self.export_json_path(f"{stem}_seg_{i:03d}")
            self.write_export(out_path, export_data)
            exports.append(out_path)

        if not exports:
            raise ValueError("未能生成任何分段")

        return exports
