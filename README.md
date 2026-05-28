# AI 助教知识库 RAG 系统

基于 Obsidian 笔记与个人知识库的 RAG 之外，本仓库新增 **AI 助教知识库** 三阶段流水线：多源原始数据 → 结构化 JSON → 向量库 → DeepSeek 问答助手。

## 架构概览

```
data/raw/ai_assistant/          # 原始数据
    ├── coze_knowledge/txt/     # Coze 操作文档
    ├── weixinchat/             # 微信答疑 Excel/CSV
    └── class_video_excel/video_to_text/  # 课程转写
         ↓  DeepSeek 生成
output/export/                  # 结构化 JSON
         ↓  Ollama bge-m3 嵌入
output/vectors/                 # Chroma 向量库
         ↓  DeepSeek 问答
src/assistant/app_ai_assistant.py
```

处理完成后，原始文件会移动到 `data/processed/ai_assistant/<source>/`。

## 环境准备

1. **Python 3.11+** 与虚拟环境：

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements\base.txt
```

**重要**：后续命令必须在激活 venv 后运行，或使用 `.\venv\Scripts\python.exe`。直接用系统 `python` 会报 `No module named 'langchain_openai'`。

2. **Ollama**（嵌入模型 `bge-m3`）：

```powershell
ollama pull bge-m3
```

若 `ollama` 不在 PATH，使用完整路径或：

```powershell
$env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
```

3. **DeepSeek API**：在项目根目录创建 `.env`：

```
DEEPSEEK_API_KEY=sk-...
```

## 阶段一：生成 export JSON

```powershell
# 全部数据源
python -m src.pipelines.generate_export --source all

# 单独处理
python -m src.pipelines.generate_export --source coze_knowledge
python -m src.pipelines.generate_export --source weixinchat
python -m src.pipelines.generate_export --source class_video_excel

# 调试（每源最多 1 个文件）
python -m src.pipelines.generate_export --source coze_knowledge --limit 1
```

### 数据源说明

| 数据源 | 输入格式 | 输出 JSON |
|--------|----------|-----------|
| `coze_knowledge` | `txt/**/*.txt` | 5 个问题 + 原文作 `answer` |
| `weixinchat` | Excel/CSV，列 `question`/`answer` | 6 个问题 + 优化后 `answer` |
| `class_video_excel` | `video_to_text/**/*.txt` | 分段 `text` + `count`（无问答对） |

提示词见 `docs/coze_gen.md`、`docs/questions_gen.md`、`docs/video_process.md`。

失败日志：`output/export/_errors/<source>.log`

## 阶段二：构建向量库

```powershell
python -m src.pipelines.build_vectors
```

向量库路径：`output/vectors/`（与 Obsidian 用的 `chroma_db/` 分离）。

## 阶段三：启动问答助手

```powershell
streamlit run src/assistant/app_ai_assistant.py
```

或使用 `scripts\start_ai_assistant.bat`。

人设与回答规则见 `docs/ai_assistant.md`。

## 目录结构

```
RAG_System/
├── data/raw/ai_assistant/       # 待处理原始数据
├── data/processed/ai_assistant/   # 已处理归档
├── output/export/               # 阶段一输出
├── output/vectors/              # 阶段二向量库
├── docs/                        # 提示词与人设
├── src/
│   ├── config.py
│   ├── llm/deepseek_client.py
│   ├── processors/
│   ├── pipelines/
│   ├── vector_db/index_qa_json.py
│   └── assistant/app_ai_assistant.py
├── web/                         # Obsidian 个人笔记 RAG（独立）
└── chroma_db/                  # Obsidian 向量库（独立）
```

## 与 Obsidian RAG 的关系

- **Obsidian RAG**：`web/app.py`、`web/app_deepseek.py`，索引 `brain/MyKnowledge_export`
- **AI 助教 RAG**：`src/assistant/app_ai_assistant.py`，索引 `output/export` → `output/vectors`

两套系统互不混用向量库路径。

## 故障排查

| 问题 | 处理 |
|------|------|
| `ModuleNotFoundError: langchain.chains` | 使用 LangChain 1.x：`langchain_classic.chains` |
| `ollama: command not found` | 加入 PATH 或使用 `ollama.exe` 完整路径 |
| JSON 解析失败 | 查看 `_errors/*.log`，可 `--limit 1` 重试 |
| 向量库不存在 | 先运行 `build_vectors` |
| `input length exceeds the context length` | 已自动分块；若仍报错，在 `config.py` 调小 `EMBEDDING_CHUNK_SIZE` |
| weixinchat 无数据 | 将 Excel 放入 `data/raw/ai_assistant/weixinchat/` |

## 维护（Obsidian 笔记 RAG）

每周：检查 Inbox、补充 aliases、手动索引同步。  
每月：清理过时笔记、备份 `MyKnowledge` 与 `chroma_db`、更新 `bge-m3`。
