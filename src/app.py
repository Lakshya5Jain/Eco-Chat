"""Streamlit chat UI for the Economic Data Chat Application."""

import json
import logging
import re
import sys
from pathlib import Path

# Ensure project root is on sys.path so `from src.X` imports work
# regardless of how Streamlit is invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.charts import create_chart
from src.data import fetch_fred_data, fetch_multiple_series
from src.llm import create_agent_executor, run_agent

logger = logging.getLogger(__name__)

EXAMPLE_QUERIES = [
    "Show me inflation over the last 5 years",
    "Compare GDP and unemployment",
    "What is the current unemployment rate?",
    "Show me a bar chart of retail sales",
    "How has the federal funds rate changed since 2020?",
    "What was the highest S&P 500 value last year?",
]


def parse_chart_blocks(text: str) -> tuple[str, list[dict]]:
    """Extract ```chart ... ``` JSON blocks from the LLM response.

    Returns (cleaned_text, list_of_chart_specs).
    """
    pattern = r"```chart\s*\n(.*?)\n```"
    charts = []
    for match in re.finditer(pattern, text, re.DOTALL):
        try:
            spec = json.loads(match.group(1))
            charts.append(spec)
        except json.JSONDecodeError:
            pass

    cleaned = re.sub(pattern, "", text, flags=re.DOTALL).strip()
    return cleaned, charts


def render_chart(spec: dict):
    """Fetch data and render a Plotly chart from a chart spec."""
    series_ids = spec.get("series_ids", [])
    chart_type = spec.get("chart_type", "line")
    title = spec.get("title", "")
    years_back = spec.get("years_back", 5)
    start_date = spec.get("start_date")
    end_date = spec.get("end_date")

    # Validate years_back
    if not isinstance(years_back, int) or years_back <= 0:
        years_back = 5

    if not series_ids:
        st.warning("No series IDs provided for chart.")
        return

    try:
        if len(series_ids) == 1:
            df, meta = fetch_fred_data(
                series_ids[0],
                years_back=years_back,
                start_date=start_date,
                end_date=end_date,
            )
            chart_title = title or meta["title"]
            y_label = meta.get("units", "")
            fig = create_chart(df, chart_type=chart_type, title=chart_title, y_label=y_label)
        else:
            df, all_meta = fetch_multiple_series(
                series_ids,
                years_back=years_back,
                start_date=start_date,
                end_date=end_date,
            )
            chart_title = title or "Comparison: " + ", ".join(
                m["title"] for m in all_meta
            )
            fig = create_chart(
                df,
                chart_type="comparison",
                title=chart_title,
                series_columns=series_ids,
            )

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        logger.exception("Chart rendering failed")
        st.error("Could not render chart. Please try a different query or time range.")


def main():
    st.set_page_config(
        page_title="Economic Data Chat",
        page_icon="📊",
        layout="wide",
    )

    st.title("Economic Data Chat")
    st.caption("Ask questions about economic data — powered by FRED & GPT")

    # ---------- Sidebar with example queries ----------
    with st.sidebar:
        st.header("Example Queries")
        st.markdown("Click any example to try it:")
        for q in EXAMPLE_QUERIES:
            if st.button(q, key=f"ex_{q}", use_container_width=True):
                st.session_state["pending_query"] = q
                st.rerun()

    # ---------- Session state ----------
    if "messages" not in st.session_state:
        st.session_state.messages = []       # display messages (role, content, charts)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []   # LangChain message objects
    if "agent" not in st.session_state:
        st.session_state.agent = create_agent_executor()

    # ---------- Welcome message ----------
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                "Welcome! I can help you explore economic data from the Federal Reserve (FRED). "
                "Try asking about **inflation**, **GDP**, **unemployment**, **interest rates**, "
                "or any other economic indicator.\n\n"
                "You can also click an example query in the sidebar to get started."
            )

    # ---------- Render previous messages ----------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            for chart_spec in msg.get("charts", []):
                render_chart(chart_spec)

    # ---------- User input (chat input or sidebar button) ----------
    prompt = st.chat_input("Ask about economic data...")

    # Check for pending query from sidebar
    if "pending_query" in st.session_state:
        prompt = st.session_state.pop("pending_query")

    if prompt:
        # Show user message
        st.session_state.messages.append({"role": "user", "content": prompt, "charts": []})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response_text, updated_history = run_agent(
                        prompt,
                        st.session_state.chat_history,
                        agent=st.session_state.agent,
                    )
                    st.session_state.chat_history = updated_history

                    # Parse out any chart instructions
                    cleaned_text, chart_specs = parse_chart_blocks(response_text)

                    # Guard against empty response
                    if not cleaned_text or not cleaned_text.strip():
                        cleaned_text = (
                            "I wasn't able to generate a response for that. "
                            "Could you try rephrasing your question?"
                        )

                    st.markdown(cleaned_text)
                    for spec in chart_specs:
                        render_chart(spec)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": cleaned_text,
                        "charts": chart_specs,
                    })

                except Exception as e:
                    logger.exception("Agent error")
                    error_msg = (
                        "Sorry, something went wrong while processing your request. "
                        "Please try again or rephrase your question."
                    )
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "charts": [],
                    })


if __name__ == "__main__":
    main()
