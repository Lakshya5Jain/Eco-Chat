"""Landing page for Eco-Chat."""

import streamlit as st

from src.data import COMMON_SERIES
from src.styles import BASE_CSS, HOME_CSS

EXAMPLE_QUERIES = [
    "Show me inflation over the last 5 years",
    "Compare GDP and unemployment",
    "What is the current unemployment rate?",
    "Show me a bar chart of retail sales",
    "How has the federal funds rate changed since 2020?",
    "What was the highest S&P 500 value last year?",
]

# --- Inject CSS ---
st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(HOME_CSS, unsafe_allow_html=True)

# --- Hero ---
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">ECO-CHAT</div>
        <div class="hero-subtitle">Economic Data Intelligence</div>
        <div class="hero-desc">
            Ask plain-English questions about economic data and get instant
            insights with interactive charts — powered by AI and the Federal Reserve.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- How It Works ---
st.markdown('<div class="section-header">How It Works</div>', unsafe_allow_html=True)

cols = st.columns(3)
steps = [
    ("1", "Ask a Question", "Type any economic question in plain English — no codes or syntax needed."),
    ("2", "AI Fetches Data", "The agent identifies the right FRED series and pulls real-time data."),
    ("3", "Get Insights", "Receive a clear explanation and interactive charts in seconds."),
]
for col, (num, title, desc) in zip(cols, steps):
    with col:
        st.markdown(
            f"""
            <div class="step-card">
                <div class="step-number">{num}</div>
                <div class="step-title">{title}</div>
                <div class="step-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# --- Available Data ---
st.markdown('<div class="section-header">Available Data</div>', unsafe_allow_html=True)

# Deduplicate display names from COMMON_SERIES
seen = set()
pill_labels = []
for key, (sid, title) in COMMON_SERIES.items():
    if sid not in seen:
        seen.add(sid)
        pill_labels.append(title)

pills_html = "".join(f'<span class="data-pill">{label}</span>' for label in sorted(pill_labels))
st.markdown(f'<div class="pill-container">{pills_html}</div>', unsafe_allow_html=True)

# --- Example Queries ---
st.markdown('<div class="section-header">Try an Example</div>', unsafe_allow_html=True)

row1 = st.columns(3)
row2 = st.columns(3)
all_cols = row1 + row2

for col, query in zip(all_cols, EXAMPLE_QUERIES):
    with col:
        if st.button(query, key=f"home_ex_{query}", use_container_width=True):
            st.session_state["pending_query"] = query
            st.switch_page("pages/chat.py")

# --- CTA ---
st.markdown('<div class="cta-container">', unsafe_allow_html=True)
if st.button("Start Chatting", key="cta_start", use_container_width=False):
    st.switch_page("pages/chat.py")
st.markdown("</div>", unsafe_allow_html=True)

# --- Footer ---
st.markdown(
    '<div class="footer">Powered by FRED API &amp; LangChain</div>',
    unsafe_allow_html=True,
)
