# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A unified RAG system merging two knowledge sources into one Chroma vector store:

- **Personal Obsidian notes** (`brain/MyKnowledge_export/*.md`) — indexed as `source_type="markdown"`
- **AI Teaching Assistant** (Coze docs, WeChat Q&A, video transcripts) — processed through a generation pipeline into export JSONs, then indexed as `source_type="qa"` or `source_type="segment"`

Both are served by a single Streamlit app (`web/app.py`) with dual LLM backend support (Ollama local / DeepSeek API) and per-source-type context formatting.

## Configuration

### `.env` (required)

```ini
DEEPSEEK_API_KEY=sk-...
```

This is the only required env var. DeepSeek is the default LLM backend; Ollama (`llama3.2:3b`) is optional as a local fallback.

### Paths that need editing

`src/config.py` **hardcodes `VAULT_PATH`** to the author's personal machine. Edit it to point at your Obsidian vault before indexing:

```python
VAULT_PATH = r"D:\helen\workspace\repositories\brain\MyKnowledge"  # ← change this
```

`EXPORT_PATH` defaults to `data/raw/ai_assistant/MyKnowledge_Export/` — created on first export, no need to change.

## Commands

All commands require the venv activated: `.\venv\Scripts\activate`

### Unified index

```powershell
# Full rebuild (Obsidian notes + AI assistant)
python src/vector_db/index_unified.py

# Subset rebuilds / incremental
python src/vector_db/index_unified.py --skip-obsidian      # AI assistant only
python src/vector_db/index_unified.py --skip-assistant     # Obsidian only (full rebuild)
python src/vector_db/index_unified.py --obsidian-only      # Incremental: update Obsidian, keep AI vectors
```

### Launch the web app

```powershell
streamlit run web/app.py
```

LLM backend and knowledge source filter are selected in the sidebar — no separate apps needed.

### AI assistant data preparation (when adding new source data)

```powershell
# Stage 1: Generate export JSONs from raw data
python -m src.pipelines.generate_export --source all
python -m src.pipelines.generate_export --source coze_knowledge --limit 1   # debug

# Then rebuild unified index (includes the new export JSONs)
python src/vector_db/index_unified.py
```

### Auto-sync (watchdog)

```powershell
python scripts/auto_sync.py
```

Watches `VAULT_PATH` for `.md` changes via watchdog, auto-exports Obsidian and incrementally updates the vector store on every change.

### Batch launchers

- `scripts/start_rag.bat` — One-click unified launcher with UTF-8 encoding
- `scripts/start_web.bat` — Streamlit app launcher
- `scripts/start_ai_assistant.bat` — Legacy launcher (may not work with current code)

## Architecture

```
Obsidian .md files ──────────┐
AI export JSONs ─────────────┤
                              ▼
              src/vector_db/index_unified.py   (unified index builder)
                              │
                              ▼
                       chroma_db/              (single Chroma collection)
                              │
                              ▼
                       web/app.py              (unified Streamlit UI)
                   · LLM: DeepSeek API / Ollama
                   · Filter: all / markdown / qa+segment
                   · Context: per-source_type formatting
```

### Web app architecture

`web/app.py` uses a **manual RAG loop** (not LangChain chains) to support per-content-type context formatting:

1. User question → MMR retriever with optional `source_type` Chroma filter
2. `format_context()` branches on metadata `source_type`: `"markdown"` → `page_content`, `"qa"` → `metadata.answer`, `"segment"` → `metadata.text`
3. Messages assembled: `[SystemMessage(persona), ...history, HumanMessage(context+question)]`
4. LLM call — `llm.stream()` for DeepSeek (incremental render), `llm.invoke()` for Ollama
5. Conversation memory via `st.session_state.messages` (last 10 rounds sent as history)

Sidebar features beyond core Q&A:
- **Index freshness** — compares `.last_build.json` timestamp against source directories; warns when files have changed
- **Sync Obsidian** — runs `obsidian-export` CLI + incremental index update (calls `src/sync/obsidian_sync.py`)
- **Rebuild full index** — runs `index_unified.py` as a subprocess
- **Batch processing** — upload a `.txt` file (one question per line), get all answers back as a downloadable file
- **Conversation export** — saves chat history to markdown in `D:\RAG_Exports\`

### System prompt switching

| Source filter | Prompt |
|---|---|
| 个人笔记 | Neutral knowledge-base assistant |
| AI 助教 | Persona from `docs/ai_assistant.md` (20yo female teaching assistant) |
| 全部 | Combined prompt covering both domains |

### Unified document schema (in Chroma)

All documents in `chroma_db/` share metadata:

| Field | Values |
|---|---|
| `source_type` | `"markdown"` / `"qa"` / `"segment"` — used for retrieval filtering and context formatting |
| `source_name` | `"obsidian"` / `"ai_assistant"` — high-level origin (used when rebuilding specific subsets) |
| `source` | `"coze_knowledge"` / `"weixinchat"` / `"class_video_excel"` — specific AI assistant data source (qa/segment types only) |
| `id` | Unique path-based identifier |
| `answer` | Full answer text (qa type only) |
| `text` | Full transcript text (segment type only) |

### AI assistant data pipeline

```
data/raw/ai_assistant/<source>/  →  processors/*  →  output/export/<source>/*.json  →  data/processed/
```

Each processor (`CozeProcessor`, `WeixinProcessor`, `VideoProcessor`) extends `BaseProcessor` (`src/processors/base.py`). On success, raw files are moved to `data/processed/`; failures are logged to `output/export/_errors/`.

Each processor uses a prompt template from `docs/` and calls DeepSeek via `src/llm/deepseek_client.py` to generate export JSONs:

| Processor | Raw input | Prompt template | Output |
|---|---|---|---|
| `CozeProcessor` | `.txt` files | `docs/coze_gen.md` | 5 generated questions + original text as answer |
| `WeixinProcessor` | `.xlsx` files | `docs/questions_gen.md` | Questions from `文字提问问题` col, answers from `文本解答` col |
| `VideoProcessor` | `.txt` transcripts | `docs/video_process.md` | Segmented transcript with generated summaries |

### Core shared modules

- **`src/config.py`** — All paths, model names, API keys, chunking parameters. Loads `.env` via `python-dotenv`. **Hardcodes `VAULT_PATH`** — must be edited per machine.
- **`src/llm/deepseek_client.py`** — `DeepSeekClient` wrapping `langchain_openai.ChatOpenAI` pointed at `api.deepseek.com`. Provides `chat()` (plain text) and `chat_json()` (structured output with retry + markdown fence stripping). Used by all three processors.
- **`src/llm/factory.py`** — `get_embeddings()` (Ollama `bge-m3`) and `get_chat_llm()` (DeepSeek via ChatOpenAI). Used by the web app and index builder.
- **`src/sync/obsidian_sync.py`** — Two-phase sync: runs `obsidian-export` CLI to convert Obsidian vault to plain `.md`, then calls `update_obsidian_only()` for incremental Chroma update. Exposed in the web app sidebar.
- **`src/loaders/loaders.py`** — `MultiFormatLoader` for markdown, PDF, Word, TXT. Utility loader, not used in the main unified pipeline.
- **`src/utils/tree.py`** — `TreeViewer` utility for printing filtered directory trees. Not used in the core pipeline.

### Key design decisions

- **DeepSeek via LangChain's `ChatOpenAI`** — OpenAI-compatible base URL pattern.
- **MMR retrieval** — Maximal Marginal Relevance to reduce redundancy.
- **Single Chroma collection** — `source_type` metadata enables filtering at query time without separate stores.
- **Manual RAG loop** — Not `ConversationalRetrievalChain`, because the context formatter needs to branch on `source_type` per document.
- **Index freshness** — `.last_build.json` timestamp in `chroma_db/`; sidebar checks both Obsidian dirs and AI export dir for changed files.
- **Processing is destructive** — processors `shutil.move` raw files to `data/processed/` on success.

### Dependencies

Install: `pip install -r requirements/base.txt`

- **Ollama** with `bge-m3` model pulled — required for embeddings.
- **DeepSeek API key** in `.env` — required for LLM generation (optional if using Ollama backend).
- **Ollama `llama3.2:3b`** — required for local LLM backend (optional if using DeepSeek).
- Key packages: `langchain-openai`, `langchain-ollama`, `langchain-classic`, `chromadb`, `langchain-chroma`, `streamlit`, `pandas`, `openpyxl`, `watchdog`.
- External CLI: `obsidian-export` (for Obsidian vault → plain markdown conversion; optional if you export manually).
