"""LLM layer — LangChain agent with FRED data tools."""

import json
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from src.data import (
    fetch_fred_data,
    fetch_multiple_series,
    resolve_series_id,
    search_fred_series,
)

load_dotenv(override=True)

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
When you fetch data and want to show a chart, include a JSON block at the END \
of your response in this exact format (the UI will parse it):

```chart
{
  "action": "chart",
  "series_ids": ["SERIES_ID"],
  "chart_type": "line",
  "title": "Chart Title",
  "years_back": 5
}
```

Chart types: "line", "bar", "comparison" (for multi-series).
For multi-series comparisons, list all series IDs in the array.
Only include the chart block when you have actually fetched data.

## When NOT to fetch data
- If the user asks a general economics question (e.g., "what is GDP?"), just answer from \
your knowledge — no need to fetch data.
- If the user says hello or makes small talk, respond naturally.
- Only fetch data when the user is asking about specific data, trends, or numbers.

## Conversation style
- Be concise but informative.
- Use plain English, avoid jargon unless the user is clearly technical.
- If something goes wrong with the data fetch, explain the issue and suggest alternatives.
"""

TOOLS = [search_economic_data, get_economic_data, compare_economic_series, resolve_series]


def build_llm():
    """Create the ChatOpenAI instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in .env")
    return ChatOpenAI(model="gpt-5.4-2026-03-05", temperature=0.3, api_key=api_key)


def create_agent_executor():
    """Create a LangChain agent with tools bound."""
    llm = build_llm()
    return llm.bind_tools(TOOLS)


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
    if agent is None:
        agent = create_agent_executor()

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + chat_history + [HumanMessage(content=user_input)]

    # Agentic loop — keep running until the model stops calling tools
    max_iterations = 10
    for _ in range(max_iterations):
        response = agent.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        # Execute each tool call
        for tc in response.tool_calls:
            tool_fn = {t.name: t for t in TOOLS}.get(tc["name"])
            if tool_fn is None:
                from langchain_core.messages import ToolMessage
                messages.append(
                    ToolMessage(content=f"Unknown tool: {tc['name']}", tool_call_id=tc["id"])
                )
                continue

            try:
                result = tool_fn.invoke(tc["args"])
            except Exception as e:
                result = f"Tool error: {e}"

            from langchain_core.messages import ToolMessage
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    # Extract final response
    final_text = response.content if isinstance(response.content, str) else str(response.content)

    # Update history (skip the system message)
    updated_history = chat_history + [
        HumanMessage(content=user_input),
        AIMessage(content=final_text),
    ]

    return final_text, updated_history
