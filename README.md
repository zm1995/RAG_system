# 统一知识库 RAG 系统

**Obsidian 个人笔记 + AI 助教知识库** → 单一向量库 `chroma_db/` → **DeepSeek** 问答助手。

## 架构

```
Obsidian Vault ──obsidian-export──┐
                                  ├── index_unified.py ──► chroma_db/
data/raw/ai_assistant ──generate_export──► output/export ──┘
                                      │
                                      ▼
                              web/app.py (DeepSeek 问答)
                              Ollama bge-m3 (仅嵌入)
```

| 组件 | 技术 |
|------|------|
| 向量库 | 单一 `chroma_db/`（Obsidian + AI 助教合并） |
| 问答 LLM | DeepSeek `deepseek-chat` |
| 向量嵌入 | Ollama `bge-m3`（DeepSeek 无 embedding API） |
| 前端 | `web/app.py`（Streamlit） |

## 环境准备

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements\base.txt
```

1. **DeepSeek API**：根目录 `.env` 中设置 `DEEPSEEK_API_KEY=sk-...`
2. **Ollama 嵌入**：`ollama pull bge-m3` 并保持 Ollama 服务运行
3. **Obsidian 同步**（可选）：安装 [obsidian-export](https://github.com/zserge/obsidian-export)

## 运行步骤

### 1. AI 助教数据（首次或更新 raw 数据后）

```powershell
python -m src.pipelines.generate_export --source all
python -m src.pipelines.generate_export --source coze_knowledge --limit 5  # 调试
```

### 2. 构建/更新向量索引

```powershell
# 全量重建（Obsidian + AI 助教）
python src\vector_db\index_unified.py

# 仅增量更新 Obsidian（保留 AI 助教向量）
python src\vector_db\index_unified.py --obsidian-only
```

### 3. 启动 Web 界面

```powershell
streamlit run web\app.py
# 或 scripts\start_web.bat
```

侧边栏功能：
- **同步 Obsidian**：export + 增量更新 Obsidian 切片
- **重建全部索引**：全量重建 `chroma_db/`
- **知识库筛选**：全部 / 个人笔记 / AI 助教

### 4. Obsidian 自动监听（可选）

```powershell
python scripts\auto_sync.py
```

Vault 内 `.md` 变更时自动 export 并增量更新向量。

## 目录结构

```
RAG_System/
├── chroma_db/                    # 唯一向量库
├── data/raw/ai_assistant/        # AI 助教原始数据
├── data/processed/ai_assistant/  # 已处理归档
├── output/export/                # AI 助教 JSON
├── src/
│   ├── config.py
│   ├── llm/factory.py            # DeepSeek + Ollama embed
│   ├── sync/obsidian_sync.py     # Obsidian 同步
│   ├── vector_db/index_unified.py
│   ├── processors/               # 三源 export 处理器
│   └── pipelines/generate_export.py
├── web/app.py                    # 统一 Web 界面
└── scripts/
    ├── start_web.bat
    ├── start_rag.bat
    └── auto_sync.py
```

## 数据源说明

| 来源 | 输入 | metadata |
|------|------|----------|
| Obsidian | `MyKnowledge_export/*.md` | `source_type=markdown`, `source_name=obsidian` |
| coze/weixin | `output/export/*.json` | `source_type=qa`, `source_name=ai_assistant` |
| 课程转写 | `output/export/*.json` | `source_type=segment`, `source_name=ai_assistant` |

## 故障排查

| 问题 | 处理 |
|------|------|
| `No module named 'langchain_openai'` | 激活 venv 并 `pip install -r requirements/base.txt` |
| `obsidian-export` 未找到 | 安装 CLI 或在前端使用已有 export 目录 |
| `input length exceeds context length` | 索引已自动分块；调小 `EMBEDDING_CHUNK_SIZE` |
| Ollama 连接失败 | 确认 `ollama serve` 运行且已 `ollama pull bge-m3` |
| GBK 解码错误 | 使用 `scripts/start_web.bat`（已设 UTF-8） |

## 维护

- Obsidian 日常更新：Web 侧边栏「同步 Obsidian」或 `auto_sync.py`
- AI 助教数据更新：`generate_export` →「重建全部索引」
- 备份：`chroma_db/` 与 `output/export/`
