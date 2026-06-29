# RAG System — Technical Specification

**Version:** 1.0  
**Last updated:** 2026-06-28  
**Status:** Production (single-user deployment)

---

## 1. System Overview

A unified Retrieval-Augmented Generation (RAG) system that merges two heterogeneous knowledge sources into a single Chroma vector database, served through a Streamlit web interface with dual LLM backend support.

### 1.1 Knowledge Sources

| Source | Format | Volume | Update cadence |
|---|---|---|---|
| Personal Obsidian notes | `.md` (via `obsidian-export` CLI) | Variable | On-demand or watchdog-driven |
| AI Teaching Assistant | `.txt`, `.xlsx` → LLM-generated JSON | ~15 files/source | Manual ingest → `generate_export` → re-index |

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Vector Store | ChromaDB (single collection) | Document storage + similarity search |
| Embeddings | Ollama `bge-m3` | 1024-dim dense vectors |
| LLM (primary) | DeepSeek `deepseek-chat` via LangChain `ChatOpenAI` | Answer generation |
| LLM (fallback) | Ollama `llama3.2:3b` | Local answer generation |
| Retrieval | MMR (Maximal Marginal Relevance) | Diversity-aware document retrieval |
| Chunking | `RecursiveCharacterTextSplitter` | Semantic paragraph splitting |
| UI | Streamlit | Web interface |
| Orchestration | `generate_export` pipeline, `index_unified.py` | Data ingest + indexing |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA INGEST                            │
│                                                             │
│  Obsidian Vault          Raw AI Data                        │
│  (.md, wikilinks)        (.txt, .xlsx, transcripts)         │
│       │                        │                            │
│       ▼                        ▼                            │
│  obsidian-export      generate_export pipeline              │
│  (CLI tool)           ├─ CozeProcessor                      │
│       │               ├─ WeixinProcessor                    │
│       ▼               └─ VideoProcessor                     │
│  plain .md files           │                                │
│       │                    ▼                                │
│       │            output/export/<source>/*.json             │
│       │                    │                                │
│       └────────┬───────────┘                                │
│                ▼                                            │
│     index_unified.py                                        │
│     ├─ load_obsidian_documents()                            │
│     ├─ load_assistant_documents()                           │
│     ├─ split_documents() [RecursiveCharacterTextSplitter]   │
│     └─ Chroma.from_documents() [Ollama bge-m3]              │
│                │                                            │
│                ▼                                            │
│           chroma_db/                                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      QUERY RUNTIME                          │
│                                                             │
│  User Question                                              │
│       │                                                     │
│       ▼                                                     │
│  web/app.py                                                 │
│  ├─ MMR Retriever (optional source_type filter)             │
│  ├─ format_context() [per-source_type branch]               │
│  ├─ Message assembly [System + History + Context+Question]  │
│  └─ LLM call [DeepSeek stream / Ollama invoke]              │
│       │                                                     │
│       ▼                                                     │
│  Streamed response + Source citations                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 Vector Database (`chroma_db/`)

**Collection:** Single unnamed collection containing all document types.

**Document Schema:**

```json
{
  "page_content": "<chunked text content>",
  "metadata": {
    "source_type": "markdown | qa | segment",
    "source_name": "obsidian | ai_assistant",
    "source": "coze_knowledge | weixinchat | class_video_excel",
    "id": "obsidian/path/to/note | coze_knowledge/__path__to__file",
    "chunk_index": 0,
    "parent_id": "<same as id of parent doc>",
    "title": "<optional, from markdown H1 or metadata>",
    "answer": "<full answer text, qa type only>",
    "text": "<full transcript text, segment type only>",
    "segment_index": "<int, segment type only>",
    "frontmatter": "<raw YAML frontmatter, markdown type only>",
    "source_file": "<original file path>",
    "original_question": "<optional, from WeChat Q&A>"
  }
}
```

**Key invariants:**
- `source_type` is the retrieval-time discriminator — determines both Chroma `where` filter and `format_context()` branch.
- `source_name` is the rebuild-time discriminator — `--obsidian-only` deletes by `where={"source_name": "obsidian"}`.
- `id` is unique per source document (chunks share a `parent_id` pointing to it).

**Persistence:** `chroma_db/` directory on disk. Build metadata at `chroma_db/.last_build.json`:

```json
{
  "timestamp": "2026-06-28T12:00:00",
  "mode": "full | obsidian_only",
  "total_documents": 150,
  "total_chunks": 1200,
  "type_counts": {"markdown": 80, "qa": 50, "segment": 20},
  "obsidian_chunks": 600,
  "assistant_chunks": 600,
  "obsidian_documents": 80,
  "assistant_documents": 70
}
```

### 3.2 Chunking Strategy

```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,        # EMBEDDING_CHUNK_SIZE
    chunk_overlap=200,      # EMBEDDING_CHUNK_OVERLAP
    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
)
```

Chinese punctuation separators (`。！？；`) ensure semantic boundaries for mixed-language content. Parameter values are configurable via `src/config.py`.

### 3.3 Retrieval

**Algorithm:** MMR (Maximal Marginal Relevance) via LangChain `Chroma.as_retriever(search_type="mmr")`.

**Parameters:**
- `k` (default 4): Number of documents to return. User-adjustable in sidebar (1–10).
- `fetch_k` (default 8): Candidate pool size for MMR diversity selection. User-adjustable (k–20).

**Filtering:** Chroma `where` clause based on `source_type`:
- "个人笔记" → `{"source_type": "markdown"}`
- "AI 助教" → `{"source_type": {"$in": ["qa", "segment"]}}`
- "全部" → no filter

### 3.4 Context Formatting (`format_context()`)

Branches on `source_type` per document — multiple types can appear in a single result set when no filter is applied:

| `source_type` | Content source | Truncation |
|---|---|---|
| `markdown` | `doc.page_content` (chunk text) | First 2000 chars |
| `qa` | `doc.metadata["answer"]` (full answer) | First 2000 chars |
| `segment` | `doc.metadata["text"]` (full transcript) | First 2000 chars |

Output format:
```
[1] 来源: coze_knowledge
<content>

---

[2] 来源: obsidian
<content>
```

### 3.5 LLM Invocation

**DeepSeek (primary):** Streaming via `llm.stream(messages)` for incremental UI rendering. Backed by LangChain `ChatOpenAI` pointed at `https://api.deepseek.com`.

**Ollama (fallback):** Non-streaming via `llm.invoke(messages)`. Uses `llama3.2:3b`.

**Message structure:**
```
SystemMessage(persona_prompt)          # Switches by source filter
HumanMessage(history[0])               # Last 10 rounds (20 messages max)
AIMessage(history[1])
...
HumanMessage(context + question)       # USER_PROMPT_TEMPLATE
```

**System prompt personas:**

| Source filter | Prompt |
|---|---|
| 个人笔记 | `SYSTEM_PROMPT_OBSIDIAN` (inline constant) |
| AI 助教 | `docs/ai_assistant.md` (file; 20yo female teaching assistant persona) |
| 全部 | `SYSTEM_PROMPT_ALL` (inline constant) |

---

## 4. Data Pipeline Specifications

### 4.1 AI Assistant Export Pipeline

```
Raw sources → Processor → Export JSONs → Archived to processed/

data/raw/ai_assistant/<source>/     →  input
output/export/<source>/*.json       →  output
data/processed/ai_assistant/<source>/ → archive (on success)
output/export/_errors/<source>.log  →  error log
```

**Entry point:** `python -m src.pipelines.generate_export --source <source>`

### 4.2 Processor Details

#### CozeProcessor
| Aspect | Detail |
|---|---|
| Input | `.txt` files under `data/raw/ai_assistant/coze_knowledge/` |
| LLM call | `DeepSeekClient.chat_json()` with `docs/coze_gen.md` system prompt |
| Output | 5 QA pairs (generated questions + full original text as answer) |
| Export path | `output/export/coze_knowledge/` |
| Validation | Requires exactly 5 questions; raises `ValueError` if fewer |

#### WeixinProcessor
| Aspect | Detail |
|---|---|
| Input | `.xlsx` files under `data/raw/ai_assistant/weixinchat/` |
| Processing | Reads Excel; extracts `文字提问问题` (question) and `文本解答` (answer) columns |
| LLM call | `DeepSeekClient.chat_json()` with `docs/questions_gen.md` |
| Output | QA pairs derived from spreadsheet rows |
| Export path | `output/export/weixinchat/` |

#### VideoProcessor
| Aspect | Detail |
|---|---|
| Input | `.txt` transcript files under `data/raw/ai_assistant/class_video_excel/video_to_txt/` or `video_to_text/` |
| LLM call | `DeepSeekClient.chat_json()` with `docs/video_process.md` |
| Output | Segmented transcript with generated summaries |
| Export path | `output/export/class_video_excel/` |
| Note | Splits long transcripts into segments; each segment is a separate document with `segment_index` |

### 4.3 Process Lifecycle

1. `list_pending_files()` — scans `data/raw/ai_assistant/<source>/` for unprocessed files
2. `process_file()` — LLM call → export JSON written to `output/export/<source>/`
3. `move_to_processed()` — on success, `shutil.move` raw file to `data/processed/ai_assistant/<source>/`
4. On failure → logged to `output/export/_errors/<source_name>.log`; raw file remains in place

**Destructive processing guarantee:** Raw files are **moved** (not copied) on success. Re-running the pipeline is safe — already-processed files won't be picked up.

### 4.4 Index Building

**Full rebuild** (`build_unified_store(rebuild=True)`):
1. `shutil.rmtree(CHROMA_DIR)` — wipe existing vectors
2. Load Obsidian + AI assistant documents
3. Split with `RecursiveCharacterTextSplitter`
4. `Chroma.from_documents()` — embed with Ollama `bge-m3`
5. Write `.last_build.json`

**Incremental Obsidian update** (`update_obsidian_only()`):
1. Load only Obsidian documents
2. If Chroma has data: `vectordb._collection.delete(where={"source_name": "obsidian"})`
3. `vectordb.add_documents(chunks)` — add fresh chunks
4. Merge build info: preserve `assistant_chunks` from previous build, update `type_counts`
5. Write `.last_build.json`

**Important:** AI assistant vectors are never individually updated — they require a full rebuild after `generate_export`.

---

## 5. Web Application (`web/app.py`)

### 5.1 Page Layout

```
┌────────────── Sidebar ──────────────┐  ┌─── Main ───────────────────────┐
│                                      │  │                                │
│  ⚙️ 设置                             │  │  🧠 统一知识库助手              │
│                                      │  │                                │
│  📚 知识库: ○全部 ○个人笔记 ○AI助教  │  │  [Chat messages]               │
│  ──────────────────────────────      │  │                                │
│  检索条数: [4]                       │  │  User: 问你的知识库...          │
│  MMR 候选池: [8]                     │  │  Assistant: [answer + sources]  │
│  ──────────────────────────────      │  │                                │
│  📊 系统状态                         │  │                                │
│  - LLM: deepseek-chat                │  │                                │
│  - 嵌入: bge-m3 (Ollama)             │  │                                │
│  - 向量库: chroma_db/                │  │                                │
│  - 📅 索引更新: 2 小时前             │  │                                │
│  ──────────────────────────────      │  │                                │
│  [📥 同步 Obsidian]                  │  │                                │
│  [🔄 重建全部索引]                   │  │                                │
│  [🗑️ 清除对话]                      │  │                                │
│  [📊 知识库统计]                     │  │                                │
│  [💾 导出对话]                      │  │                                │
│                                      │  │                                │
│  💡 AI 助教数据更新后请点「重建     │  │                                │
│     全部索引」                       │  │                                │
└──────────────────────────────────────┘  └────────────────────────────────┘
```

### 5.2 Session State

| Key | Type | Description |
|---|---|---|
| `messages` | `list[dict]` | Chat history: `{"role": "user"/"assistant", "content": str, "sources": list[str]}` |

### 5.3 Caching

| Decorator | Target | Behavior |
|---|---|---|
| `@st.cache_resource` | `load_vectordb()` | Chroma client singleton — cleared on sidebar rebuild |
| `@st.cache_resource` | `load_llm()` | DeepSeek ChatOpenAI singleton — never cleared |

### 5.4 Index Freshness Detection

`detect_changed_files()` walks source directories and compares file `mtime` against `.last_build.json` timestamp. If any `.md` or `.json` files are newer, a warning is shown in the sidebar.

### 5.5 Batch Processing

Users can upload a `.txt` file (UTF-8, one question per line). Each question is processed with `llm.invoke()` (non-streaming) against the current retriever. Results are aggregated into a downloadable `.txt` file.

### 5.6 Error States

| Condition | Behavior |
|---|---|
| Chroma DB not found | `st.error()` + `st.stop()` — app halts |
| Index rebuild timeout (>10 min) | Error message in sidebar |
| Obsidian sync failure | Error message, no state change |
| `obsidian-export` not installed | Descriptive error with install link |

---

## 6. Watchdog Auto-Sync (`scripts/auto_sync.py`)

**Mechanism:** `watchdog.Observer` monitors `VAULT_PATH` recursively.

**Triggers:**
- `on_modified` → `.md` file changed
- `on_created` → new `.md` file
- `on_deleted` → `.md` file removed

**Action:** Calls `sync_obsidian_vectors()` — full export + incremental index update.

**Limitations:**
- Waits for each sync to complete before processing the next event (synchronous handler).
- No debouncing — rapid successive edits trigger multiple syncs.
- Export timeout: 300 seconds.
- Only watches `VAULT_PATH`, not AI assistant source directories.

---

## 7. Configuration Reference (`src/config.py`)

### 7.1 Paths

| Variable | Default | Must edit? |
|---|---|---|
| `VAULT_PATH` | `D:\helen\workspace\repositories\brain\MyKnowledge` | **Yes** — user-specific |
| `EXPORT_PATH` | `data/raw/ai_assistant/MyKnowledge_Export/` | No |
| `CHROMA_DIR` | `chroma_db/` (project root) | No |
| `AI_EXPORT_PATH` | `output/export/` | No |
| `AI_ERRORS_PATH` | `output/export/_errors/` | No |

### 7.2 Models & Parameters

| Variable | Default | Notes |
|---|---|---|
| `DEEPSEEK_MODEL` | `deepseek-chat` | |
| `DEEPSEEK_TEMPERATURE` | `0.1` | Low temp for factual accuracy |
| `JSON_RETRY_COUNT` | `1` | Retries on malformed JSON from LLM |
| `OLLAMA_EMBEDDING_MODEL` | `bge-m3` | Must be pulled in Ollama |
| `EMBEDDING_CHUNK_SIZE` | `1000` | Characters per chunk |
| `EMBEDDING_CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `DEFAULT_K` | `4` | Default retrieval count |
| `DEFAULT_FETCH_K` | `8` | Default MMR candidate pool |

### 7.3 Excel Column Names (WeChat Q&A)

| Variable | Value |
|---|---|
| `WEIXIN_QUESTION_COL` | `文字提问问题` |
| `WEIXIN_ANSWER_COL` | `文本解答` |

---

## 8. File Structure

```
RAG_System/
├── chroma_db/                          # Vector store + .last_build.json
├── data/
│   ├── raw/ai_assistant/               # Unprocessed source files
│   │   ├── coze_knowledge/
│   │   ├── weixinchat/
│   │   └── class_video_excel/
│   └── processed/ai_assistant/         # Successfully processed raw files (archive)
├── output/export/                      # Generated JSONs (input to indexer)
│   ├── coze_knowledge/
│   ├── weixinchat/
│   ├── class_video_excel/
│   └── _errors/                        # Per-source error logs
├── docs/                               # Prompt templates
│   ├── ai_assistant.md                 # AI teaching assistant persona
│   ├── coze_gen.md                     # Coze Q&A generation prompt
│   ├── questions_gen.md                # WeChat Q&A generation prompt
│   └── video_process.md                # Video transcript processing prompt
├── src/
│   ├── config.py                       # All configuration
│   ├── llm/
│   │   ├── deepseek_client.py          # DeepSeekClient (chat + chat_json)
│   │   └── factory.py                  # get_embeddings() + get_chat_llm()
│   ├── processors/
│   │   ├── base.py                     # BaseProcessor (scan → process → archive)
│   │   ├── coze_processor.py
│   │   ├── weixin_processor.py
│   │   └── video_processor.py
│   ├── pipelines/
│   │   └── generate_export.py          # CLI entry for export pipeline
│   ├── sync/
│   │   └── obsidian_sync.py            # obsidian-export + incremental index
│   ├── vector_db/
│   │   └── index_unified.py            # Unified index builder + updater
│   ├── loaders/
│   │   └── loaders.py                  # MultiFormatLoader (utility)
│   └── utils/
│       └── tree.py                     # TreeViewer (utility)
├── web/
│   └── app.py                          # Streamlit application
├── scripts/
│   ├── auto_sync.py                    # Watchdog auto-sync
│   ├── start_rag.bat                   # Unified launcher
│   └── start_web.bat                   # Web app launcher
├── requirements/
│   └── base.txt                        # Python dependencies
├── .env                                # DEEPSEEK_API_KEY (git-ignored)
└── CLAUDE.md                           # Project guide for AI assistants
```

---

## 9. Design Decisions & Trade-offs

### 9.1 Single Chroma Collection

**Decision:** One collection with `source_type` metadata, rather than separate collections per source.

**Rationale:** Enables cross-source MMR retrieval (user gets diverse results from both Obsidian and AI assistant in one query). The `source_type` Chroma `where` filter provides source isolation when needed.

**Cost:** All documents share one embedding space — a poor fit if the semantic domains were radically different. In practice, the overlap (Chinese tech/AI content) makes this acceptable.

### 9.2 Manual RAG Loop (not LangChain ConversationalRetrievalChain)

**Decision:** Custom message assembly with manual `format_context()`.

**Rationale:** `ConversationalRetrievalChain` assumes uniform document structure. This system needs per-`source_type` content extraction (`answer` vs `text` vs `page_content`), which LangChain's built-in chains don't support without invasive subclassing.

**Cost:** More boilerplate; conversation memory management is manual (last 10 rounds, 20 messages max).

### 9.3 DeepSeek via ChatOpenAI Adapter

**Decision:** Use `langchain_openai.ChatOpenAI` pointed at `api.deepseek.com`, rather than a dedicated DeepSeek SDK.

**Rationale:** DeepSeek's API is OpenAI-compatible. This avoids an extra dependency and keeps the LLM abstraction uniform with the Ollama fallback path.

**Cost:** Tied to OpenAI message format; any DeepSeek-specific features require raw `model_kwargs`.

### 9.4 Ollama bge-m3 for Embeddings (not DeepSeek)

**Decision:** Embeddings run locally via Ollama, while generation uses cloud DeepSeek.

**Rationale:** DeepSeek does not offer an embeddings API. `bge-m3` is a strong multilingual model (supports Chinese) and running locally avoids per-token embedding costs.

**Cost:** Requires local Ollama service running; adds operational complexity.

### 9.5 Destructive Processing

**Decision:** `shutil.move()` raw files to `data/processed/` on successful export.

**Rationale:** Simplifies `list_pending_files()` — just scan the raw directory. No dedup logic needed.

**Cost:** Raw files are no longer in their original location after processing. Must re-acquire raw data to reprocess with different prompts/parameters.

### 9.6 Index Freshness via File mtime

**Decision:** Compare `.last_build.json` timestamp against source file modification times.

**Rationale:** Simple, no external dependencies. Works for a single-user deployment where the index builder is the only writer.

**Cost:** Doesn't detect deletions (files removed from source dirs are still in Chroma until a rebuild). Doesn't track AI assistant raw data changes — only Obsidian export dir and AI export JSON dir.

### 9.7 MMR over Similarity Search

**Decision:** Maximal Marginal Relevance as the default retrieval strategy.

**Rationale:** A unified knowledge base with two sources risks returning near-duplicate content. MMR's diversity objective ensures results span different documents/sources.

**Cost:** Slightly higher latency (larger `fetch_k` candidate pool, then greedy selection). Parameter `lambda_mult` uses LangChain default (0.5).

---

## 10. Operational Notes

### 10.1 Setup Checklist

1. `python -m venv venv && .\venv\Scripts\activate`
2. `pip install -r requirements/base.txt`
3. Create `.env` with `DEEPSEEK_API_KEY=sk-...`
4. `ollama pull bge-m3`
5. Edit `VAULT_PATH` in `src/config.py`
6. Install `obsidian-export` CLI (optional, for sync features)
7. Run `python -m src.pipelines.generate_export --source all` (if AI assistant data present)
8. Run `python src/vector_db/index_unified.py`
9. `streamlit run web/app.py`

### 10.2 Routine Operations

| Task | Command |
|---|---|
| Add new AI source data | `generate_export --source <src>` → `index_unified.py` (full rebuild) |
| Update Obsidian notes | Sidebar "同步 Obsidian" or `index_unified.py --obsidian-only` |
| Continuous Obsidian sync | `python scripts/auto_sync.py` |
| Debug export for one file | `generate_export --source coze_knowledge --limit 1` |

### 10.3 Backup Targets

- `chroma_db/` — the vector store
- `output/export/` — generated JSONs (can be regenerated from raw data)
- `data/raw/` — raw source data (not backed up by git; protect separately)
- `.env` — API key

### 10.4 Known Limitations

- **No authentication** — single-user Streamlit deployment, not secured for multi-user access.
- **No incremental AI assistant update** — any change to AI assistant data requires a full Chroma rebuild.
- **Hardcoded export path** for conversation exports (`D:\RAG_Exports\`).
- **No deletion tracking** — documents removed from source directories remain in Chroma until a full rebuild or manual `source_name`-scoped deletion.
- **Embedding model is fixed** — changing `bge-m3` requires a full rebuild (vectors are not compatible across models).
