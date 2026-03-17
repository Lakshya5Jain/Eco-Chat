"""Landing page for Eco-Chat."""

import streamlit as st

from src.data import COMMON_SERIES
from src.styles import BASE_CSS, HOME_CSS

EXAMPLE_QUERIES = [
    ("Monetary Policy", "How has the Fed Funds rate changed since January 2022?"),
    ("Inflation Comparison", "Compare CPI and Core PCE inflation over the last 3 years"),
    ("GDP Analysis", "Show me a bar chart of quarterly GDP growth in 2024"),
    ("Labor Market", "What's the unemployment rate vs pre-COVID levels?"),
    ("Multi-Asset", "Plot 10-year Treasury yields vs S&P 500 over the past 5 years"),
    ("Housing & Sentiment", "Show housing starts and consumer sentiment since 2020"),
]

# --- Inject CSS ---
st.markdown(BASE_CSS, unsafe_allow_html=True)
st.markdown(HOME_CSS, unsafe_allow_html=True)

# --- Hero ---
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">ECO-CHAT</div>
        <div class="hero-subtitle">Real-Time Economic Data, Explained</div>
        <div class="hero-desc">
            Explore GDP, inflation, employment, interest rates, and more from the
            Federal Reserve (FRED). Ask questions in plain English and get instant
            analysis with interactive visualizations.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- How It Works ---
st.markdown('<div class="section-header">How It Works</div>', unsafe_allow_html=True)

cols = st.columns(3)
steps = [
    ("1", "Ask a Question", "Ask about any macroeconomic indicator \u2014 inflation trends, rate comparisons, labor market data. No FRED codes or special syntax required."),
    ("2", "AI Fetches Data", "The LangChain agent identifies the right FRED series, selects the appropriate date range, and retrieves the latest available data."),
    ("3", "Get Insights", "Receive a plain-English analysis with interactive Plotly charts. Ask follow-up questions to refine or compare."),
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

for col, (category, query) in zip(all_cols, EXAMPLE_QUERIES):
    with col:
        st.markdown(f'<div class="example-category">{category}</div>', unsafe_allow_html=True)
        if st.button(query, key=f"home_ex_{query}", width="stretch"):
            st.session_state["pending_query"] = query
            st.switch_page("pages/chat.py")

# --- CTA ---
st.markdown(
    '<div class="cta-section"><div class="cta-label">Ready to explore economic data?</div></div>',
    unsafe_allow_html=True,
)
_cta_left, _cta_mid, _cta_right = st.columns([1, 2, 1])
with _cta_mid:
    if st.button("Start Chatting \u2192", key="cta_start", width="stretch", type="primary"):
        st.switch_page("pages/chat.py")

# --- Footer ---
st.markdown(
    """
    <div class="footer">
        <div class="footer-attribution">Made for Millennium Saxa Capital Management by Laksh J.</div>
        <div class="footer-powered">Powered by FRED API &middot; LangChain &middot; Plotly</div>
    </div>
    """,
    unsafe_allow_html=True,
)
