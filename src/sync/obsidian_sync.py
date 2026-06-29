"""Obsidian 导出与向量库增量同步。"""

import os
import subprocess

from src.config import EXPORT_PATH, VAULT_PATH
from src.vector_db.index_unified import update_obsidian_only


def export_obsidian() -> tuple[bool, str]:
    """将 Obsidian vault 导出为 Markdown 到 EXPORT_PATH。"""
    os.makedirs(EXPORT_PATH, exist_ok=True)
    if not os.path.isdir(VAULT_PATH):
        return False, f"Vault 不存在: {VAULT_PATH}"

    cmd = (
        f'obsidian-export "{VAULT_PATH}" "{EXPORT_PATH}" '
        f"--frontmatter never"
    )
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "obsidian-export 失败").strip()
            if "not found" in err.lower() or "不是内部或外部命令" in err:
                return False, "未找到 obsidian-export，请先安装: https://github.com/zserge/obsidian-export"
            return False, err[-800:]
        return True, "Obsidian 导出完成"
    except subprocess.TimeoutExpired:
        return False, "导出超时（超过 5 分钟）"
    except Exception as e:
        return False, str(e)


def sync_obsidian_vectors(*, skip_export: bool = False) -> tuple[bool, str]:
    """导出 Obsidian 并增量更新 chroma_db 中的 Obsidian 切片。

    若 obsidian-export 因个别笔记 frontmatter 不规范而失败，仍会从 vault 直接索引。
    """
    export_msg = "跳过导出"
    prefer_vault = False
    if not skip_export:
        ok, msg = export_obsidian()
        if ok:
            export_msg = msg
        else:
            prefer_vault = True
            export_msg = (
                "obsidian-export 失败，已从 vault 直接索引"
                "（常见原因：部分笔记 YAML frontmatter 不规范）"
            )
            if "frontmatter" in msg.lower() or "yaml" in msg.lower():
                export_msg += f"。详情: {msg[-300:]}"
            else:
                return False, msg

    ok, msg = update_obsidian_only(prefer_vault=prefer_vault)
    if not ok:
        return False, msg
    return True, f"{export_msg}；{msg}"
