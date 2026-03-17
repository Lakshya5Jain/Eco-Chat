"""LLM layer — LangGraph ReAct agent with FRED data tools."""

import json
import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent

from src.data import (
    fetch_fred_data,
    fetch_multiple_series,
    resolve_series_id,
    search_fred_series,
)

load_dotenv(override=True)
logger = logging.getLogger(__name__)


def _safe_int_env(name: str, default: int) -> int:
    """Parse int environment variables with a safe fallback."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _safe_float_env(name: str, default: float) -> float:
    """Parse float environment variables with a safe fallback."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _looks_like_timeout(exc: Exception) -> bool:
    """Best-effort check for timeout-like transport/runtime errors."""
    text = str(exc).lower()
    return (
        "timed out" in text
        or "timeout" in text
        or "connection error" in text
        or "connection reset" in text
        or "proxyerror" in text
        or "forbidden" in text
    )


DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")


def _extract_text(content) -> str:
    """Extract plain text from an AIMessage content field.

    Reasoning models (o-series, gpt-5.4-pro, etc.) return structured content:
    [{"type": "reasoning", ...}, {"type": "text", "text": "..."}]
    This helper normalises that to a plain string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts).strip()
    return str(content)
OPENAI_REQUEST_TIMEOUT_SECONDS = _safe_float_env("OPENAI_REQUEST_TIMEOUT_SECONDS", 60.0)
AGENT_RECURSION_LIMIT = _safe_int_env("AGENT_RECURSION_LIMIT", 8)

# --------------------------------------------------------------------------- #
# Tools — the LLM decides when to call these                                  #
# --------------------------------------------------------------------------- #

@tool
def search_economic_data(query: str) -> str:
    """Search FRED for economic data series matching a topic.

    Use this when you need to find the right series ID for an economic concept.
    For example, search for "inflation", "GDP", "unemployment", etc.
    Returns a list of matching FRED series with their IDs.
    """
    return search_fred_series(query)


@tool
def get_economic_data(
    series_id: str,
    years_back: int = 5,
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Fetch economic data from FRED for a specific series.

    Parameters
    ----------
    series_id : str
        The FRED series ID (e.g. "CPIAUCSL" for CPI, "UNRATE" for unemployment).
        Use the search_economic_data tool first if you don't know the series ID.
    years_back : int
        Number of years of historical data to fetch (default 5).
    start_date : str
        Optional ISO date "YYYY-MM-DD" — overrides years_back if provided.
    end_date : str
        Optional ISO date "YYYY-MM-DD" — defaults to today.

    Returns a JSON summary of the data including metadata and recent values.
    """
    try:
        df, meta = fetch_fred_data(
            series_id,
            start_date=start_date or None,
            end_date=end_date or None,
            years_back=years_back,
        )
    except (ValueError, RuntimeError) as e:
        return f"Error: {e}"

    # Build a concise summary for the LLM
    summary = {
        "series_id": meta["series_id"],
        "title": meta["title"],
        "units": meta["units"],
        "frequency": meta["frequency"],
        "observations": len(df),
        "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
        "latest_value": float(df["value"].iloc[-1]),
        "min_value": float(df["value"].min()),
        "max_value": float(df["value"].max()),
        "mean_value": round(float(df["value"].mean()), 2),
    }

    # Include a sample of data points (first 3 + last 5) for context
    sample_rows = []
    head = df.head(3)
    tail = df.tail(5)
    for _, row in head.iterrows():
        sample_rows.append({"date": str(row["date"].date()), "value": float(row["value"])})
    if len(df) > 8:
        sample_rows.append({"note": f"... ({len(df) - 8} more rows) ..."})
    for _, row in tail.iterrows():
        sample_rows.append({"date": str(row["date"].date()), "value": float(row["value"])})

    summary["sample_data"] = sample_rows

    return json.dumps(summary, indent=2)


@tool
def compare_economic_series(
    series_ids: list[str],
    years_back: int = 5,
) -> str:
    """Fetch and compare multiple FRED economic data series side by side.

    Parameters
    ----------
    series_ids : list[str]
        List of FRED series IDs to compare (e.g. ["UNRATE", "FEDFUNDS"]).
    years_back : int
        Number of years of historical data (default 5).

    Returns a JSON summary of the comparison.
    """
    if not series_ids:
        return "Error: No series IDs provided. Please specify at least one FRED series to compare."

    try:
        df, all_meta = fetch_multiple_series(series_ids, years_back=years_back)
    except (ValueError, RuntimeError) as e:
        return f"Error: {e}"

    summary = {
        "series": [
            {
                "series_id": m["series_id"],
                "title": m["title"],
                "units": m["units"],
            }
            for m in all_meta
        ],
        "observations": len(df),
        "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
    }

    for sid in series_ids:
        col = df[sid].dropna()
        if not col.empty:
            summary[sid] = {
                "latest": float(col.iloc[-1]),
                "min": float(col.min()),
                "max": float(col.max()),
                "mean": round(float(col.mean()), 2),
            }

    return json.dumps(summary, indent=2)


@tool
def resolve_series(concept: str) -> str:
    """Resolve a plain-English economic concept to its FRED series ID.

    Use this as a quick lookup before fetching data. For example:
    "inflation" -> "CPIAUCSL", "unemployment" -> "UNRATE".
    Returns the series ID or a message saying it wasn't found.
    """
    result = resolve_series_id(concept)
    if result:
        return f"Series ID for '{concept}': {result}"
    return (
        f"No direct mapping for '{concept}'. "
        "Use search_economic_data to find the right series."
    )


# --------------------------------------------------------------------------- #
# Chart tool — structured tool calling replaces fragile regex parsing         #
# --------------------------------------------------------------------------- #

_pending_charts: list[dict] = []


@tool
def generate_chart(
    series_ids: list[str],
    chart_type: str = "line",
    title: str = "",
    years_back: int = 5,
    start_date: str = "",
    end_date: str = "",
) -> str:
    """Generate an inline chart for economic data series.

    Call this AFTER fetching data to show a visualization to the user.
    The chart will appear inline in the chat interface.

    Parameters
    ----------
    series_ids : list[str]
        FRED series IDs to chart (e.g. ["CPIAUCSL"] or ["UNRATE", "FEDFUNDS"]).
    chart_type : str
        Type of chart:
        - "line" — time series trend (default)
        - "area" — filled line chart, good for cumulative or volume data
        - "bar" — bar chart, good for periodic comparisons
        - "comparison" — multi-series with automatic dual y-axes when units differ
        When charting 2+ series, prefer "comparison" as it auto-detects whether
        dual y-axes are needed based on the series units.
    title : str
        Chart title.
    years_back : int
        Years of data to show (default 5).
    start_date : str
        Optional ISO date "YYYY-MM-DD" — overrides years_back.
    end_date : str
        Optional ISO date "YYYY-MM-DD".
    """
    spec = {
        "series_ids": series_ids,
        "chart_type": chart_type,
        "title": title,
        "years_back": years_back,
    }
    if start_date:
        spec["start_date"] = start_date
    if end_date:
        spec["end_date"] = end_date

    _pending_charts.append(spec)
    return f"Chart queued: {chart_type} chart of {', '.join(series_ids)}"


def pop_pending_charts() -> list[dict]:
    """Return and clear all pending chart specs."""
    result = list(_pending_charts)
    _pending_charts.clear()
    return result


# --------------------------------------------------------------------------- #
# Agent setup                                                                  #
# --------------------------------------------------------------------------- #

SYSTEM_PROMPT = """\
You are an expert economic data analyst assistant. You help users explore and \
understand economic data by fetching real data from the FRED (Federal Reserve \
Economic Data) database.

## How you work
- When a user asks about economic data, use your tools to fetch real data from FRED.
- First try resolve_series to quickly map common concepts to series IDs.
- If that doesn't work, use search_economic_data to find the right series.
- Then use get_economic_data to fetch the actual data.
- For comparisons, use compare_economic_series.
- ALWAYS explain the data in plain, accessible English — never return raw JSON to the user.
- Mention key trends, recent values, historical context, and what the data means.

## Chart instructions
After fetching data, call the generate_chart tool to show a visualization. \
Choose the appropriate chart_type:
- "line" for single series trends over time
- "area" for filled charts — good for cumulative measures, money supply, GDP levels
- "bar" for period-based comparisons, shorter date ranges, or discrete values
- "comparison" for multi-series — this automatically uses dual y-axes when the \
series have different units (e.g. unemployment rate % vs GDP in billions), and \
normalizes to % change when comparing 3+ series with different scales
Pass the same series_ids and years_back you used when fetching the data. \
When comparing 2+ series, always use "comparison" as the chart_type. \
Only call generate_chart when you have actually fetched data — do not chart \
data you haven't retrieved.

## When NOT to fetch data
- If the user asks a general economics question (e.g., "what is GDP?"), just answer from \
your knowledge — no need to fetch data.
- If the user says hello or makes small talk, respond naturally.
- Only fetch data when the user is asking about specific data, trends, or numbers.

## Handling unclear or nonsensical input
- If the user sends gibberish, random characters, or a very vague message that does not \
relate to economics, do NOT call any tools. Instead, respond politely and suggest topics \
you can help with, such as: inflation, GDP, unemployment, interest rates, stock market, \
housing, retail sales, or trade data.
- If you are unsure what the user is asking for, ask a clarifying question instead of \
guessing.

## Conversation style
- Be concise but informative.
- Use plain English, avoid jargon unless the user is clearly technical.
- If something goes wrong with the data fetch, explain the issue and suggest alternatives.
"""

TOOLS = [search_economic_data, get_economic_data, compare_economic_series, resolve_series, generate_chart]


def build_llm():
    """Create the ChatOpenAI instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return ChatOpenAI(
        model=DEFAULT_OPENAI_MODEL,
        temperature=0.3,
        api_key=api_key,
        request_timeout=OPENAI_REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )


def create_agent_executor():
    """Create a LangGraph ReAct agent with tools.

    Uses LangGraph's `create_react_agent` — the modern recommended approach.
    It implements a ReAct-style loop as a compiled state graph, handling tool
    dispatch and stopping conditions automatically.
    """
    llm = build_llm()
    return create_react_agent(llm, TOOLS, prompt=SystemMessage(content=SYSTEM_PROMPT))


def run_agent(
    user_input: str,
    chat_history: list,
    agent=None,
) -> tuple[str, list]:
    """Run the agent on user input with conversation history.

    Parameters
    ----------
    user_input : str
        The user's message.
    chat_history : list
        List of LangChain message objects (maintains conversation context).
    agent : optional
        Pre-built agent. Creates a new one if None.

    Returns
    -------
    (response_text, updated_chat_history)
    """
    # Guard against empty / whitespace-only input
    if not user_input or not user_input.strip():
        fallback = (
            "It looks like you sent an empty message. Try asking about economic data — "
            "for example, \"Show me inflation over the last 5 years\" or "
            "\"What is the current unemployment rate?\""
        )
        updated = chat_history + [
            HumanMessage(content=user_input or ""),
            AIMessage(content=fallback),
        ]
        return fallback, updated

    if agent is None:
        agent = create_agent_executor()

    # Clear any stale pending charts
    pop_pending_charts()

    # Build messages: history + new user message
    messages = list(chat_history) + [HumanMessage(content=user_input)]

    # Invoke the LangGraph ReAct agent — it handles the full tool-dispatch
    # cycle (observe → think → act → observe) automatically
    try:
        result = agent.invoke(
            {"messages": messages},
            config={"recursion_limit": AGENT_RECURSION_LIMIT},
        )
    except GraphRecursionError:
        logger.warning("Agent hit recursion limit for input: %s", user_input)
        fallback = (
            "I got stuck while analyzing that request. Please try a simpler or more specific "
            "question, for example: 'Show CPI inflation over the last 5 years.'"
        )
        updated = chat_history + [
            HumanMessage(content=user_input),
            AIMessage(content=fallback),
        ]
        return fallback, updated
    except Exception as e:
        if _looks_like_timeout(e):
            logger.warning("Agent timed out for input: %s", user_input)
            # If tools already ran and queued charts, the data was fetched
            # successfully — only the final text summary timed out.
            if _pending_charts:
                fallback = (
                    "I fetched the data and generated a chart for you (shown below). "
                    "The detailed text analysis timed out — feel free to ask a "
                    "follow-up question about what you see in the chart."
                )
            else:
                fallback = (
                    "That request timed out while contacting the model or data source. "
                    "Please try again, or use a narrower query (single indicator + date range)."
                )
            updated = chat_history + [
                HumanMessage(content=user_input),
                AIMessage(content=fallback),
            ]
            return fallback, updated
        raise

    # Extract the final AI response from the agent's message list
    final_message = result["messages"][-1]
    final_text = _extract_text(final_message.content)

    # Guard against empty final response
    if not final_text or not final_text.strip():
        final_text = (
            "I wasn't able to generate a response for that. Could you try rephrasing "
            "your question? For example, you can ask about inflation, GDP, unemployment, "
            "or other economic indicators."
        )

    # Update history with just the user message and final AI response
    updated_history = chat_history + [
        HumanMessage(content=user_input),
        AIMessage(content=final_text),
    ]

    return final_text, updated_history


def run_agent_stream(
    user_input: str,
    chat_history: list,
    agent=None,
):
    """Stream the agent's response, yielding text chunks and status updates.

    Yields
    ------
    dict with keys:
        "type": "text" | "status"
        "content": str
    """
    if not user_input or not user_input.strip():
        yield {
            "type": "text",
            "content": (
                "It looks like you sent an empty message. Try asking about economic data — "
                "for example, \"Show me inflation over the last 5 years\" or "
                "\"What is the current unemployment rate?\""
            ),
        }
        return

    if agent is None:
        agent = create_agent_executor()

    # Clear any stale pending charts
    pop_pending_charts()

    messages = list(chat_history) + [HumanMessage(content=user_input)]

    final_text = ""

    for event in agent.stream({"messages": messages}, stream_mode="updates"):
        for node_name, node_output in event.items():
            if node_name == "agent":
                # The agent node produced a response
                msgs = node_output.get("messages", [])
                for msg in msgs:
                    if isinstance(msg, AIMessage):
                        text = _extract_text(msg.content)
                        if text and not msg.tool_calls:
                            # Final text response
                            final_text = text
                            yield {"type": "text", "content": text}
                        elif msg.tool_calls:
                            # Agent is about to call tools
                            for tc in msg.tool_calls:
                                yield {"type": "status", "content": f"Calling {tc['name']}..."}
            elif node_name == "tools":
                # Tool execution completed
                pass

    if not final_text:
        yield {
            "type": "text",
            "content": (
                "I wasn't able to generate a response for that. Could you try rephrasing "
                "your question? For example, you can ask about inflation, GDP, unemployment, "
                "or other economic indicators."
            ),
        }
