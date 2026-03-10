# Economic Data Chat Application

An interactive chat application that lets you explore economic data through natural conversation. Powered by the [FRED](https://fred.stlouisfed.org/) (Federal Reserve Economic Data) API, LangChain, and Streamlit.

Ask questions in plain English — the app fetches real data, generates interactive Plotly charts, and explains trends in context.

## Features

- **Natural language queries** — ask about inflation, GDP, unemployment, and more
- **Real-time FRED data** — fetches live economic data from the Federal Reserve
- **Interactive charts** — line, bar, and multi-series comparison charts via Plotly
- **Conversation memory** — follow-up questions work naturally
- **25+ common series** built-in for instant lookup (CPI, S&P 500, Fed Funds Rate, etc.)

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

## Example Queries

- "Show me inflation over the last 5 years"
- "Compare GDP and unemployment"
- "What was the highest S&P 500 value last year?"
- "Show me a bar chart of retail sales"
- "How has the federal funds rate changed since 2020?"
- "What is the current unemployment rate?"

## Project Structure

```
src/
  app.py      — Streamlit chat UI and chart rendering
  llm.py      — LangChain agent with FRED data tools
  data.py     — FRED API integration and data fetching
  charts.py   — Plotly chart builders (line, bar, comparison)
```
