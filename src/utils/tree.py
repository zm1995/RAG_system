from pathlib import Path
from typing import List, Optional


class TreeViewer:
    """支持自定义过滤规则的目录树查看器"""

    def __init__(self, filter_patterns: Optional[List[str]] = None):
        """
        初始化树查看器

        Args:
            filter_patterns: 自定义过滤规则列表
        """
        self.default_filters = [
            "__pycache__",
            "chroma_db",
            "chromadb",
            "AI助教",
            "ai-助教",
            "ai_assistant",
            "ai_teaching",
            "AI-teaching",
            ".pytest_cache",
            ".mypy_cache",
            ".ipynb_checkpoints",
            "node_modules",  # 添加常见需要过滤的
            ".git",
            ".idea",
            ".vscode",
        ]

        # 合并默认过滤和自定义过滤
        self.filter_patterns = self.default_filters.copy()
        if filter_patterns:
            self.filter_patterns.extend(filter_patterns)

    def should_filter(self, name: str) -> bool:
        """判断是否需要过滤"""
        name_lower = name.lower()
        for pattern in self.filter_patterns:
            pattern_lower = pattern.lower()
            # 支持部分匹配和完全匹配
            if pattern_lower in name_lower or name_lower == pattern_lower:
                return True
        return False

    def print_tree(self, directory=".", prefix="", ignore_hidden=True,
                   max_depth=None, current_depth=0, show_size=True):
        """
        打印目录树结构

        Args:
            directory: 要显示的目录路径
            prefix: 前缀字符串（用于递归时的缩进）
            ignore_hidden: 是否忽略隐藏文件（以.开头）
            max_depth: 最大深度限制
            current_depth: 当前深度（内部使用）
            show_size: 是否显示文件大小
        """
        if max_depth is not None and current_depth > max_depth:
            return

        path = Path(directory)

        try:
            items = sorted(path.iterdir(), key=lambda x: (
                not x.is_dir(), x.name.lower()))
        except PermissionError:
            print(f"{prefix}[权限不足]")
            return

        # 过滤条目
        filtered_items = []
        for item in items:
            if ignore_hidden and item.name.startswith('.'):
                continue
            if self.should_filter(item.name):
                continue
            filtered_items.append(item)

        for i, item in enumerate(filtered_items):
            is_last = (i == len(filtered_items) - 1)
            current_prefix = "└── " if is_last else "├── "

            if item.is_dir():
                # 统计子目录信息
                try:
                    sub_items = list(item.iterdir())
                    file_count = sum(1 for x in sub_items if x.is_file(
                    ) and not self.should_filter(x.name))
                    dir_count = sum(1 for x in sub_items if x.is_dir()
                                    and not self.should_filter(x.name))
                    info = f" (📄{file_count} 📁{dir_count})" if (
                        file_count + dir_count) > 0 else ""
                except:
                    info = ""

                print(f"{prefix}{current_prefix}{item.name}/{info}")
                extension = "    " if is_last else "│   "
                self.print_tree(item, prefix + extension, ignore_hidden,
                                max_depth, current_depth + 1, show_size)
            else:
                if show_size:
                    size = item.stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"
                    print(f"{prefix}{current_prefix}{item.name} ({size_str})")
                else:
                    print(f"{prefix}{current_prefix}{item.name}")

    def get_filtered_list(self) -> List[str]:
        """获取当前的过滤规则列表"""
        return self.filter_patterns.copy()

    def add_filter(self, pattern: str):
        """添加新的过滤规则"""
        if pattern not in self.filter_patterns:
            self.filter_patterns.append(pattern)

    def remove_filter(self, pattern: str):
        """移除过滤规则"""
        if pattern in self.filter_patterns:
            self.filter_patterns.remove(pattern)


# 使用示例
if __name__ == "__main__":
    # 创建查看器（使用默认过滤）
    viewer = TreeViewer()

    print("=== 当前过滤规则 ===")
    print(viewer.get_filtered_list())

    print("\n=== 目录树（带文件大小）===")
    # viewer.print_tree(show_size=True)

    print("\n=== 目录树（不显示文件大小，限制深度为2）===")
    viewer.print_tree(max_depth=2, show_size=False)

    # 添加额外的过滤规则
    print("\n=== 添加自定义过滤规则 ===")
    viewer.add_filter("temp")
    viewer.add_filter("backup")
    viewer.add_filter("chroma_db")
    viewer.add_filter("AI助教相关数据")
    viewer.add_filter("_pychache_")
    viewer.add_filter("venv")
    print(f"新增过滤后: {viewer.get_filtered_list()}")

    viewer.print_tree(max_depth=2, show_size=False)
