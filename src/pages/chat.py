"""Chat page — economic data conversation interface."""

import logging

import streamlit as st

from src.chat_store import create_chat, delete_chat, derive_title, list_chats, load_chat, save_chat
from src.charts import create_chart
from src.data import fetch_fred_data, fetch_multiple_series, transform_series
from src.llm import create_agent_executor, pop_pending_charts, run_agent
from src.styles import BASE_CSS, CHAT_CSS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def render_chart(spec: dict):
    """Fetch data and render a Plotly chart from a chart spec."""
    series_ids = spec.get("series_ids", [])
    chart_type = spec.get("chart_type", "line")
    title = spec.get("title", "")
    years_back = spec.get("years_back", 5)
    start_date = spec.get("start_date")
    end_date = spec.get("end_date")
    transform = spec.get("transform", "")

    if not isinstance(years_back, int) or years_back <= 0:
        years_back = 5

    # Fetch extra history when a transform needs look-back (e.g. YoY)
    fetch_years = years_back + 2 if transform else years_back

    if not series_ids:
        st.warning("No series IDs provided for chart.")
        return

    try:
        if len(series_ids) == 1:
            df, meta = fetch_fred_data(
                series_ids[0],
                years_back=fetch_years,
                start_date=start_date,
                end_date=end_date,
            )
            if transform:
                df, meta = transform_series(df, meta, transform)
                # Trim to requested window after transform
                if not start_date:
                    from datetime import datetime, timedelta
                    cutoff = datetime.today() - timedelta(days=365 * years_back)
                    df = df[df["date"] >= cutoff].reset_index(drop=True)
            chart_title = title or meta["title"]
            y_label = meta.get("units", "")
            fig = create_chart(
                df, chart_type=chart_type, title=chart_title,
                y_label=y_label, meta_list=[meta],
            )
        else:
            df, all_meta = fetch_multiple_series(
                series_ids,
                years_back=fetch_years,
                start_date=start_date,
                end_date=end_date,
            )
            if transform:
                import pandas as pd
                for i, sid in enumerate(series_ids):
                    col_df = df[["date", sid]].rename(columns={sid: "value"}).dropna()
                    col_df, all_meta[i] = transform_series(col_df, all_meta[i], transform)
                    col_df = col_df.rename(columns={"value": sid})
                    if i == 0:
                        merged = col_df
                    else:
                        merged = pd.merge(merged, col_df, on="date", how="outer")
                df = merged.sort_values("date").reset_index(drop=True)
                if not start_date:
                    from datetime import datetime, timedelta
                    cutoff = datetime.today() - timedelta(days=365 * years_back)
                    df = df[df["date"] >= cutoff].reset_index(drop=True)
            chart_title = title or "Comparison: " + ", ".join(
                m["title"] for m in all_meta
            )
            fig = create_chart(
                df,
                chart_type=chart_type if chart_type != "line" else "comparison",
                title=chart_title,
                series_columns=series_ids,
                meta_list=all_meta,
            )

        st.plotly_chart(fig, width="stretch")
    except Exception:
        logger.exception("Chart rendering failed")
        st.error("Could not render chart. Please try a different query or time range.")


def _switch_chat(chat_id: str) -> None:
    """Load a saved chat into session state."""
    data = load_chat(chat_id)
    if data:
        st.session_state.active_chat_id = chat_id
        st.session_state.messages = data.get("messages", [])
        st.session_state.chat_history = data.get("chat_history", [])
        # Recreate agent for the new conversation
        st.session_state.agent = create_agent_executor()


def _new_chat() -> None:
    """Start a fresh chat."""
    _persist_current_chat()
    chat_id = create_chat()
    st.session_state.active_chat_id = chat_id
    st.session_state.messages = []
    st.session_state.chat_history = []
    st.session_state.agent = create_agent_executor()


def _persist_current_chat() -> None:
    """Save the current chat to disk if it has messages."""
    chat_id = st.session_state.get("active_chat_id")
    messages = st.session_state.get("messages", [])
    if chat_id and messages:
        title = derive_title(messages)
        save_chat(chat_id, title, messages, st.session_state.get("chat_history", []))


# ---------------------------------------------------------------------------
# Page layout
# ---------------------------------------------------------------------------

# Inject CSS
st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(CHAT_CSS, unsafe_allow_html=True)

# Header bar
header_left, header_right = st.columns([8, 1])
with header_left:
    st.markdown(
        '<div class="chat-header-title">'
        '<span class="chat-header-accent">MILLENNIUM</span> Economic Data Chat'
        "</div>",
        unsafe_allow_html=True,
    )
with header_right:
    if st.button("Home", key="nav_home"):
        _persist_current_chat()
        st.switch_page("pages/home.py")

# --- Session state init ---
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = create_chat()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent" not in st.session_state:
    st.session_state.agent = create_agent_executor()

# --- Sidebar: chat management ---
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.1rem;font-weight:600;color:#fff;margin-bottom:0.75rem;">'
        "Conversations</div>",
        unsafe_allow_html=True,
    )
    if st.button("+ New Chat", key="new_chat", width="stretch"):
        _new_chat()
        st.rerun()

    st.markdown("---")

    saved_chats = list_chats()
    for cid, title, _created in saved_chats:
        col_btn, col_del = st.columns([5, 1])
        is_active = cid == st.session_state.get("active_chat_id")
        with col_btn:
            label = f"\u25B6 {title}" if is_active else title
            if st.button(label, key=f"chat_{cid}", width="stretch"):
                if not is_active:
                    _persist_current_chat()
                    _switch_chat(cid)
                    st.rerun()
        with col_del:
            if st.button("x", key=f"del_{cid}"):
                delete_chat(cid)
                if is_active:
                    _new_chat()
                st.rerun()

# Welcome message
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Welcome! I can help you explore economic data from the Federal Reserve (FRED). "
            "Try asking about **inflation**, **GDP**, **unemployment**, **interest rates**, "
            "or any other economic indicator."
        )

# Render previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for chart_spec in msg.get("charts", []):
            render_chart(chart_spec)

# User input
prompt = st.chat_input("Ask about economic data...")

# Check for pending query from home page
if "pending_query" in st.session_state:
    prompt = st.session_state.pop("pending_query")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt, "charts": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Analyzing your question..."):
                response_text, updated_history = run_agent(
                    prompt,
                    st.session_state.chat_history,
                    agent=st.session_state.agent,
                )
                st.session_state.chat_history = updated_history

            # Collect charts generated via the structured tool
            chart_specs = pop_pending_charts()

            if not response_text or not response_text.strip():
                response_text = (
                    "I wasn't able to generate a response for that. "
                    "Could you try rephrasing your question?"
                )

            st.markdown(response_text)

        except Exception as e:
            logger.exception("Agent error")
            response_text = (
                "Sorry, something went wrong while processing your request. "
                "Please try again or rephrase your question."
            )
            chart_specs = []
            st.error(response_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "charts": chart_specs,
    })
    _persist_current_chat()
    # Rerun so the history loop renders charts inside the correct assistant
    # message bubble — avoids charts visually attaching to the next user message.
    st.rerun()
