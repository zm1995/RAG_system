"""
自动监听 Obsidian 知识库变化，防抖后增量更新向量索引。
"""

import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.config import VAULT_PATH
from src.sync.obsidian_sync import sync_obsidian_vectors

# 停止编辑后等待多久再同步（秒）
DEBOUNCE_SECONDS = 60

_sync_lock = threading.Lock()
_sync_timer: threading.Timer | None = None
_sync_pending = False


def _run_sync():
    global _sync_pending
    with _sync_lock:
        _sync_pending = False
    print("🔄 正在同步 Obsidian 到向量库...")
    try:
        ok, msg = sync_obsidian_vectors()
        if ok:
            print(f"✅ {msg}")
        else:
            print(f"❌ 同步失败: {msg}")
    except Exception as e:
        print(f"❌ 同步异常: {e}")
        print("   若 Obsidian 向量缺失，请运行: python src\\vector_db\\index_unified.py")


def schedule_sync():
    """防抖：连续变更只触发一次同步。"""
    global _sync_timer, _sync_pending
    with _sync_lock:
        _sync_pending = True
        if _sync_timer is not None:
            _sync_timer.cancel()
        _sync_timer = threading.Timer(DEBOUNCE_SECONDS, _run_sync)
        _sync_timer.daemon = True
        _sync_timer.start()
    print(f"⏳ 已记录变更，{DEBOUNCE_SECONDS}s 无新变更后将同步...")


class MarkdownHandler(FileSystemEventHandler):
    def _should_ignore(self, path: str) -> bool:
        if not path.endswith(".md"):
            return True
        if "\\.obsidian\\" in path or "/.obsidian/" in path.replace("\\", "/"):
            return True
        if "90_Templates" in path:
            return True
        return False

    def _on_md_change(self, path: str, label: str):
        if self._should_ignore(path):
            return
        print(f"{label}: {path}")
        schedule_sync()

    def on_modified(self, event):
        if not event.is_directory:
            self._on_md_change(event.src_path, "📝 检测到变化")

    def on_created(self, event):
        if not event.is_directory:
            self._on_md_change(event.src_path, "✨ 新增文件")

    def on_deleted(self, event):
        if not event.is_directory:
            self._on_md_change(event.src_path, "🗑️ 删除文件")


if __name__ == "__main__":
    print(f"👁️ 开始监听知识库: {VAULT_PATH}")
    print(f"防抖间隔: {DEBOUNCE_SECONDS}s（避免每次保存都触发 export）")
    print("按 Ctrl+C 停止监听\n")

    event_handler = MarkdownHandler()
    observer = Observer()
    observer.schedule(event_handler, VAULT_PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if _sync_timer is not None:
            _sync_timer.cancel()
        print("\n👋 停止监听")

    observer.join()
