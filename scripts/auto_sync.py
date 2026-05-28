"""
自动监听 Obsidian 知识库变化，增量更新向量索引
"""

import time
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 配置路径
VAULT_PATH = r"D:\helen\workspace\repositories\brain\MyKnowledge"
EXPORT_PATH = r"D:\helen\workspace\repositories\MyKnowledge_export"
INDEX_SCRIPT = r"D:\helen\workspace\repositories\RAG_System\index_knowledge.py"

class MarkdownHandler(FileSystemEventHandler):
    """处理 Markdown 文件变化"""
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            print(f"📝 检测到变化: {event.src_path}")
            self.rebuild_index()
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            print(f"✨ 新增文件: {event.src_path}")
            self.rebuild_index()
    
    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            print(f"🗑️ 删除文件: {event.src_path}")
            self.rebuild_index()
    
    def rebuild_index(self):
        """重建索引"""
        print("🔄 正在更新向量索引...")
        try:
            # 先导出 Obsidian 库
            export_cmd = f'obsidian-export "{VAULT_PATH}" "{EXPORT_PATH}" --frontmatter=never'
            subprocess.run(export_cmd, shell=True, check=True)
            print("✅ 导出完成")
            
            # 重建索引
            subprocess.run(["python", INDEX_SCRIPT], check=True)
            print("✅ 索引更新完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ 更新失败: {e}")

if __name__ == "__main__":
    # 确保导出目录存在
    os.makedirs(EXPORT_PATH, exist_ok=True)
    
    print(f"👁️ 开始监听知识库: {VAULT_PATH}")
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
        print("\n👋 停止监听")
    
    observer.join()