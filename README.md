# Eco-Chat: Economic Data Chat Application

A conversational interface for exploring macroeconomic data from the Federal Reserve (FRED). Users ask questions in plain English — the application autonomously fetches real data, generates interactive Plotly charts inline in the conversation, and explains trends in context. Built with LangGraph, Streamlit, and the FRED API.

## Table of Contents

- [What This Project Accomplishes](#what-this-project-accomplishes)
- [How It Goes Above and Beyond](#how-it-goes-above-and-beyond)
- [Architecture Overview](#architecture-overview)
- [File-by-File Breakdown](#file-by-file-breakdown)
- [How the Files Connect](#how-the-files-connect)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Example Queries](#example-queries)
- [Key Design Decisions](#key-design-decisions)

---

## What This Project Accomplishes

The assignment calls for a chat application where a user types a plain-English question about economic data and receives a written answer plus a chart. This implementation delivers that through three cleanly separated layers:

1. **Data Layer** — Wraps the FRED API with caching, timeout protection, error handling, and a transformation engine so the LLM can compute derived metrics (YoY growth, percent change, rolling averages) from base-level series without searching for obscure pre-computed FRED series.

2. **LLM Layer** — A LangGraph ReAct agent that autonomously decides when to fetch data versus answer from general knowledge. The agent has five tools at its disposal: series search, series resolution, single-series fetch (with optional transforms), multi-series comparison, and chart generation. All orchestrated through LangGraph's `create_react_agent`, which implements the full ReAct loop (observe → think → act → observe) as a compiled state graph.

3. **UI Layer** — A Streamlit multi-page application with a branded landing page and a chat interface. Charts render inline inside assistant message bubbles via a structured tool-calling mechanism — the LLM calls a `generate_chart` tool that queues chart specs, and the UI renders them after the agent completes.

---

## How It Goes Above and Beyond

Beyond the core requirements, this project includes:

| Feature | Why It Matters |
|---|---|
| **Branded landing page** with hero section, "How It Works" walkthrough, clickable example queries, and available data pills | Gives the app a polished, production feel — not just a bare chat input |
| **Chat persistence with sidebar navigation** | Users can switch between conversations and pick up where they left off; conversations serialize LangChain message objects to disk |
| **Data transformation engine** (YoY, pct_change, diff, rolling_mean, index_100) | Lets users ask about growth rates without needing obscure FRED series — the agent fetches the well-known base series and applies the transform |
| **Dual y-axis detection** | When comparing two series with different units (e.g., unemployment rate % vs GDP in billions), the chart automatically uses dual y-axes |
| **Normalized comparison for 3+ series** | When comparing three or more series with different scales, automatically normalizes to percent change from start for apples-to-apples comparison |
| **25+ common series lookup table** | Instant resolution of "inflation" → CPIAUCSL without an API call — reduces latency and avoids FRED search overhead |
| **4 chart types** (line, area, bar, comparison) | The spec requires "at least a few"; area charts add a fourth option good for cumulative measures |
| **Interactive range slider + range selectors** (6M, 1Y, 2Y, 5Y, All) on every chart | Users can zoom into specific periods without re-querying |
| **TTL cache on all FRED API calls** (5-minute expiry) | Avoids redundant API calls when the agent fetches the same series multiple times in a session |
| **FRED HTTP timeout monkey-patch** | The `fredapi` library uses `urlopen` with no timeout by default, which can block indefinitely — we patch it to enforce a configurable socket timeout |
| **Configurable timeouts and recursion limits** via environment variables | Production-ready tunability without touching code |
| **Graceful timeout recovery with partial results** | If the LLM times out but data was already fetched and charts queued, the UI still shows the chart with a message explaining the text analysis timed out |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                              │
│  ┌────────────┐    ┌────────────────────────────────────────┐    │
│  │  home.py   │    │              chat.py                   │    │
│  │  Landing   │───>│  Chat interface + inline chart render  │    │
│  │  page      │    │                                        │    │
│  └────────────┘    └──────────────┬───────────────────────┬─┘    │
│       app.py (navigation hub)     │                       │      │
└───────────────────────────────────┼───────────────────────┼──────┘
                                    │                       │
                              ┌─────▼─────┐          ┌──────▼─────┐
                              │  llm.py   │          │ charts.py  │
                              │  LangGraph│          │ Plotly     │
                              │  ReAct    │          │ builders   │
                              │  Agent    │          └──────▲─────┘
                              └─────┬─────┘                │
                                    │ (tool calls)         │
                              ┌─────▼─────┐                │
                              │  data.py  │────────────────┘
                              │  FRED API │  (chat.py also calls
                              │  + cache  │   data.py to fetch
                              │  + transforms│ data for chart rendering)
                              └───────────┘
```

**Data flow for a typical query:**
1. User types "Show me inflation over the last 5 years" in `chat.py`
2. `chat.py` calls `run_agent()` in `llm.py` with the message + conversation history
3. The LangGraph ReAct agent decides to call `resolve_series("inflation")` → returns `CPIAUCSL`
4. Agent calls `get_economic_data(series_id="CPIAUCSL", years_back=5)` → returns JSON summary
5. Agent calls `generate_chart(series_ids=["CPIAUCSL"], chart_type="line", ...)` → queues a chart spec
6. Agent composes a plain-English response explaining the data
7. Control returns to `chat.py`, which calls `pop_pending_charts()` to get queued chart specs
8. `chat.py` calls `render_chart()` which fetches data via `data.py` and builds a Plotly figure via `charts.py`
9. The chart and text render inline in the assistant's message bubble

---

## File-by-File Breakdown

### `src/app.py` — Navigation Hub

The Streamlit entry point. Configures page settings (title, icon, wide layout) and registers the two pages (`home.py` and `chat.py`) using Streamlit's `st.navigation` API with `position="hidden"` so navigation is handled programmatically (via `st.switch_page`) rather than through a visible nav bar. This is a deliberate design choice — the home page has its own CTA buttons and the chat page manages its own sidebar.

### `src/data.py` — Data Layer (FRED API)

The backbone of the application. Responsible for all communication with the FRED API.

**Key components:**

- **`COMMON_SERIES` dictionary** — Maps 25+ plain-English terms (e.g., "inflation", "gdp", "unemployment") to their FRED series IDs and descriptions. This lookup table lets the agent resolve common queries instantly without making a FRED search API call.

- **`_get_fred()`** — Lazy-initializes the `Fred` client from the `FRED_API_KEY` environment variable. The client is a module-level singleton to avoid re-authentication on every call.

- **`search_fred_series(query, limit)`** — First checks `COMMON_SERIES` for an instant match, then falls back to the FRED search API. Results are sorted by popularity. Decorated with `@_cached` (5-minute TTL).

- **`fetch_fred_data(series_id, start_date, end_date, years_back)`** — Core data fetch function. Retrieves a single FRED series, fetches metadata (title, units, frequency), handles date parsing, and returns a clean `(DataFrame, metadata_dict)` tuple. The DataFrame always has columns `["date", "value"]`. Decorated with `@_cached`.

- **`transform_series(df, meta, transform)`** — Applies in-memory transformations to a fetched series. Supports five transforms:
  - `yoy` — Year-over-year percent change (auto-detects frequency via `_infer_periods_per_year`)
  - `pct_change` — Period-over-period percent change
  - `diff` — Period-over-period absolute difference
  - `rolling_mean_N` — N-period moving average
  - `index_100` — Rebases the series so the first observation equals 100

  This is a critical design decision: rather than searching FRED for obscure pre-computed growth-rate series (which are inconsistent and often discontinued), the agent fetches well-known base series and applies the transform. The system prompt explicitly guides the LLM to use this pattern.

- **`fetch_multiple_series(series_ids, ...)`** — Fetches multiple series and merges them into a single wide DataFrame (one column per series, joined on date via outer merge). Used by the comparison tool.

- **`resolve_series_id(user_query)`** — Simple lookup against `COMMON_SERIES`. Returns the series ID or `None`.

- **TTL cache (`_cached` decorator)** — A simple dictionary-based cache with 5-minute expiry. Chosen over `st.cache_data` because LangGraph tool functions execute in a thread pool where Streamlit's session context is unavailable.

- **FRED timeout monkey-patch** — The `fredapi` library calls `urlopen` without a `timeout` parameter, which can block indefinitely on bad networks. At module load time, we patch `fred_module.urlopen` to inject a configurable timeout (default 15s). A guard flag (`_eco_chat_timeout_patched`) prevents double-patching.

### `src/llm.py` — LLM Layer (LangGraph Agent)

Defines the LangGraph ReAct agent, its tools, and the system prompt that governs its behavior.

**Tools (5 total):**

1. **`search_economic_data(query)`** — Wraps `search_fred_series`. Used when the agent needs to discover which FRED series matches a topic.

2. **`get_economic_data(series_id, years_back, start_date, end_date, transform)`** — Wraps `fetch_fred_data` + optional `transform_series`. Returns a JSON summary with metadata, stats (min/max/mean/latest), and a sample of data points (first 3 + last 5). When a transform is requested, it fetches 2 extra years of history so YoY calculations don't lose the first year of the requested window, then trims back.

3. **`compare_economic_series(series_ids, years_back)`** — Wraps `fetch_multiple_series`. Returns a JSON summary with per-series stats for side-by-side comparison.

4. **`resolve_series(concept)`** — Wraps `resolve_series_id`. A fast lookup the agent tries first before falling back to the heavier search tool.

5. **`generate_chart(series_ids, chart_type, title, years_back, start_date, end_date, transform)`** — Does not render anything directly. Instead, it appends a chart specification dict to a module-level `_pending_charts` list and returns a confirmation string. After the agent completes, the UI calls `pop_pending_charts()` to retrieve and render all queued charts. This decoupled design avoids mixing Plotly rendering into the LLM tool execution context.

**System prompt** — A detailed prompt that instructs the agent on:
- When to fetch data vs. answer from knowledge
- How to use transforms instead of searching for obscure FRED series
- Which chart type to use for different scenarios
- How to handle gibberish, vague, or nonsensical input
- Tone and style guidelines

**Agent construction** — Uses `langgraph.prebuilt.create_react_agent`, which compiles a ReAct-style state graph. The agent receives all 5 tools and a system message. The LLM (configurable, default `gpt-5.4`) decides autonomously which tools to call and in what order.

**`run_agent(user_input, chat_history, agent)`** — The main entry point called by the UI. Handles:
- Empty input guard
- Clearing stale pending charts before each run
- `GraphRecursionError` — catches infinite tool-call loops and returns a helpful fallback
- Timeout detection — if the LLM times out but charts were already queued, returns a partial-success message so the user still sees the chart
- Empty response guard — if the agent returns blank text, substitutes a helpful fallback
- History management — appends only the user message and final AI response (not intermediate tool calls) to keep history clean

**`_extract_text(content)`** — Normalizes AIMessage content. Reasoning models (o-series, gpt-5.4) return structured content blocks `[{"type": "reasoning", ...}, {"type": "text", ...}]` instead of plain strings. This helper extracts just the text blocks.

### `src/charts.py` — Visualization Layer (Plotly)

Builds interactive Plotly charts. All chart functions follow the same signature: `(df, title, y_label, series_columns, meta_list) -> go.Figure`.

**Chart types:**

- **`line_chart`** — Standard time series. Supports automatic dual y-axes when `meta_list` contains two series with different units (detected by `_needs_dual_axis`). Uses `plotly.subplots.make_subplots` with `secondary_y=True` for dual-axis layout.

- **`area_chart`** — Filled line chart using `fill="tozeroy"` / `fill="tonexty"`. Good for cumulative measures like money supply or GDP levels.

- **`bar_chart`** — Grouped bar chart (`barmode="group"`). Good for discrete comparisons or shorter date ranges.

- **`comparison_chart`** — Smart dispatcher for multi-series:
  - 2 series with different units → delegates to `line_chart` with dual y-axes
  - 3+ series with different units → delegates to `_normalized_comparison` (percent change from start)
  - Same units → delegates to `line_chart` with shared axis

- **`_normalized_comparison`** — Rebases each series to percent change from its first value, so series with wildly different scales (e.g., GDP in trillions vs. unemployment rate at 4%) can be meaningfully compared on the same axis.

**Shared styling:**
- Dark theme (`plotly_dark`) with transparent backgrounds to blend with the Streamlit dark UI
- Spike lines for cross-series reference on hover
- Unified hover mode (`hovermode="x unified"`)
- Range slider + range selector buttons (6M, 1Y, 2Y, 5Y, All) on every chart via `_apply_rangeslider`
- Millennium blue (`#0032FF`) as primary color in the 8-color palette

**`create_chart`** — Public dispatch function. Maps `chart_type` strings to builder functions with a fallback to `line_chart` for unknown types.

### `src/styles.py` — UI Styling

Centralized CSS constants injected into Streamlit via `st.markdown(CSS, unsafe_allow_html=True)`. Three CSS blocks:

- **`BASE_CSS`** — Global styles: hides default Streamlit footer/menu, sets Inter font family, custom scrollbar theming, button hover effects with Millennium blue glow.

- **`HOME_CSS`** — Landing page styles: hero section typography (4rem title, letter-spacing), step cards with hover borders, data pills for available series, example category labels, pulsing CTA button with keyframe animation, footer.

- **`CHAT_CSS`** — Chat page styles: branded header bar, chat message bubbles with blue left border accent, chat input styling with focus glow, sidebar styling for conversation list.

### `src/chat_store.py` — Chat Persistence

JSON-based storage for conversation history. Stores all chats in a single `chat_history.json` file (gitignored).

- **`_serialize_history` / `_deserialize_history`** — Converts between LangChain `HumanMessage`/`AIMessage` objects and JSON-safe dicts. Only serializes `type` and `content` fields — tool messages and system messages are intentionally skipped since they're not needed for conversation continuity.

- **`create_chat`** — Generates an 8-character hex ID, initializes empty chat, persists to disk.

- **`save_chat` / `load_chat`** — Persist and retrieve both the Streamlit display messages (with chart specs) and the LangChain message history (for agent context).

- **`list_chats`** — Returns all chats sorted newest-first by creation timestamp.

- **`derive_title`** — Extracts the first 50 characters of the first user message as the chat title for the sidebar.

### `src/utils.py` — Shared Utilities

Three helper functions used by both `data.py` and `llm.py`:

- **`safe_int_env` / `safe_float_env`** — Parse environment variables with type-safe fallbacks. Never crash on malformed input.

- **`looks_like_timeout`** — Heuristic string matching on exception messages to detect timeout-like failures (connection reset, name resolution, proxy errors). Used to provide user-friendly error messages instead of raw tracebacks.

### `src/pages/home.py` — Landing Page

The first page users see. No sidebar (hidden via CSS). Contains:

- Hero section with "ECO-CHAT" branding and subtitle
- "How It Works" — three step cards explaining the flow (Ask → Fetch → Insights)
- "Available Data" — dynamically generates pills from `COMMON_SERIES` keys, deduplicated by series ID
- "Try an Example" — six clickable example queries spanning different categories (Monetary Policy, Inflation, GDP, Labor, Multi-Asset, Housing). Clicking one sets `st.session_state["pending_query"]` and calls `st.switch_page("pages/chat.py")`, which picks it up and runs it immediately.
- CTA button with pulsing animation to enter the chat
- Footer with attribution

### `src/pages/chat.py` — Chat Interface

The main interaction page. Manages the full conversation lifecycle.

- **Session state initialization** — Creates a new chat ID, empty message lists, and a fresh agent on first load.

- **Sidebar** — Lists saved conversations with switch/delete buttons. "New Chat" persists the current conversation before starting fresh.

- **Message rendering loop** — Iterates `st.session_state.messages` and renders each in a `st.chat_message` bubble. Chart specs stored in each message's `charts` list are re-rendered on every rerun via `render_chart()`.

- **`render_chart(spec)`** — Takes a chart spec dict (from `generate_chart` tool), fetches the data (via `data.py`), applies transforms if specified, and builds a Plotly figure (via `charts.py`). Handles single-series and multi-series paths separately. Uses `st.plotly_chart` for inline rendering.

- **Input handling** — Accepts input from `st.chat_input` or from `pending_query` (set by the home page). Calls `run_agent()`, collects pending chart specs, appends the assistant message (with chart specs) to session state, persists to disk, and calls `st.rerun()` so charts render inside the correct message bubble.

- **Error boundary** — Wraps the agent call in try/except. On failure, shows a user-friendly error message instead of crashing.

### `src/__main__.py` — Entry Point

Enables `uv run econ-chat` via the `[project.scripts]` entry in `pyproject.toml`. Launches Streamlit as a subprocess pointing at `src/app.py`, with `cwd` set to the project root so relative paths resolve correctly.

### `src/__init__.py` and `src/pages/__init__.py`

Empty files that mark `src` and `src/pages` as Python packages, required for the import system.

### Configuration Files

- **`pyproject.toml`** — Project metadata, dependencies, build system (hatchling), and the `econ-chat` script entry point. Dependencies: streamlit, langchain, langchain-openai, langchain-community, langgraph, fredapi, pandas, plotly, python-dotenv.

- **`uv.lock`** — Lockfile generated by `uv`. Ensures reproducible installs across machines.

- **`.python-version`** — Pins the Python version for `uv` to use.

- **`.streamlit/config.toml`** — Streamlit theme configuration: dark base, Millennium blue (`#0032FF`) primary color, black background, white text. Checked into the repo so the theme is consistent for anyone running the app.

- **`.env.example`** — Template for required and optional environment variables with explanatory comments.

- **`.gitignore`** — Excludes `.env`, `chat_history.json`, virtual environments, compiled Python files, IDE configs, OS artifacts, and `.claude/settings.local.json`.

- **`CLAUDE.md`** — Project instructions for Claude Code. Checked into the repo so anyone using Claude Code as a development tool gets the full project context automatically.

- **`.claude/launch.json`** — Claude Code launch configuration for running the app with `uv run econ-chat`.

---

## How the Files Connect

```
User input
    │
    ▼
pages/chat.py ──── run_agent() ────▶ llm.py (LangGraph ReAct agent)
    │                                    │
    │                                    ├── resolve_series()  ──▶ data.py (COMMON_SERIES lookup)
    │                                    ├── search_economic_data() ──▶ data.py (FRED search API)
    │                                    ├── get_economic_data()  ──▶ data.py (fetch + transform)
    │                                    ├── compare_economic_series() ──▶ data.py (multi-fetch)
    │                                    └── generate_chart()  ──▶ _pending_charts (queued)
    │                                    │
    │◀── response text + pop_pending_charts()
    │
    ├── render_chart(spec)
    │       ├── data.py (re-fetch for chart rendering)
    │       └── charts.py (build Plotly figure)
    │
    ├── chat_store.py (persist conversation)
    │
    └── styles.py (CSS injection)
```

Both `data.py` and `llm.py` import from `utils.py` for shared helpers. The `home.py` page imports `COMMON_SERIES` from `data.py` to dynamically generate the available data pills, and imports from `styles.py` for consistent theming.

---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) (free)
- [OpenAI API key](https://platform.openai.com/api-keys)

## Setup

```bash
# 1. Copy the example env file and fill in your API keys
cp .env.example .env

# 2. Install dependencies
uv sync

# 3. Run the app
uv run econ-chat
```

The app will open at **http://localhost:8501**.

## Configuration

All configuration is via environment variables in `.env`. Only two are required:

| Variable | Required | Default | Description |
|---|---|---|---|
| `FRED_API_KEY` | Yes | — | FRED API key for data access |
| `OPENAI_API_KEY` | Yes | — | OpenAI API key for the LLM |
| `OPENAI_MODEL` | No | `gpt-5.4` | LLM model identifier |
| `OPENAI_REQUEST_TIMEOUT_SECONDS` | No | `60` | Max seconds to wait for OpenAI |
| `AGENT_RECURSION_LIMIT` | No | `25` | Max tool-call loops per query |
| `FRED_HTTP_TIMEOUT_SECONDS` | No | `15` | Socket timeout for FRED requests |

## Example Queries

| Category | Query |
|---|---|
| Inflation | "Show me inflation over the last 5 years" |
| Comparison | "Compare GDP and unemployment" |
| Specific data | "What was the highest S&P 500 value last year?" |
| Chart type | "Show me a bar chart of retail sales" |
| Time range | "How has the federal funds rate changed since 2020?" |
| Current data | "What is the current unemployment rate?" |
| Growth rates | "Show me GDP growth rate over the last decade" |
| Multi-asset | "Plot 10-year Treasury yields vs S&P 500" |
| Vague query | "How's the economy doing?" |

## Key Design Decisions

1. **LangGraph `create_react_agent` over legacy LangChain `AgentExecutor`** — LangGraph is the modern recommended approach. It compiles the ReAct loop as a state graph with built-in tool dispatch and stopping conditions, rather than the deprecated `initialize_agent` / `AgentExecutor` pattern.

2. **Structured tool calling for charts instead of regex parsing** — The `generate_chart` tool returns a structured spec that the UI renders, rather than trying to parse chart instructions from the LLM's text output. This is more reliable and lets the LLM specify exact chart parameters.

3. **Transform engine over pre-computed FRED series** — FRED has thousands of pre-computed series (e.g., `A191RL1Q225SBEA` for GDP growth), but they're inconsistent, hard to discover, and often discontinued. Fetching base series + applying transforms is more reliable and gives the agent a consistent interface.

4. **TTL cache over `st.cache_data`** — LangGraph tools execute in a thread pool where Streamlit's session context is unavailable. A simple dictionary cache with timestamp expiry works reliably across all execution contexts.

5. **Dual y-axis auto-detection** — Rather than requiring the user or LLM to specify axis configuration, the chart layer inspects series metadata and automatically chooses the right layout based on whether units differ.
