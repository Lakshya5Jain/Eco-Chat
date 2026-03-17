"""Centralized CSS constants for the Millennium-branded UI."""

BASE_CSS = """
<style>
/* Hide default Streamlit footer */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}

/* Global font */
html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
}

/* Scrollbar theming */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #0A0A14;
}
::-webkit-scrollbar-thumb {
    background: #1a1a2e;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #0032FF;
}

/* Button base */
.stButton > button {
    border: 1px solid #1a1a2e;
    border-radius: 8px;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: #0032FF;
    box-shadow: 0 0 12px rgba(0, 50, 255, 0.15);
}
</style>
"""

HOME_CSS = """
<style>
/* Hide sidebar on home page */
[data-testid="stSidebar"] {
    display: none;
}
[data-testid="stSidebarCollapsedControl"] {
    display: none;
}

/* Hero section */
.hero-container {
    text-align: center;
    padding: 5rem 1rem 2rem 1rem;
}
.hero-title {
    font-size: 4rem;
    font-weight: 200;
    letter-spacing: 0.35em;
    color: #FFFFFF;
    margin-bottom: 0.25rem;
    line-height: 1.1;
}
.hero-subtitle {
    font-size: 1.5rem;
    font-weight: 500;
    color: #0032FF;
    margin-bottom: 0.75rem;
    letter-spacing: 0.05em;
}
.hero-desc {
    font-size: 1.05rem;
    color: #888;
    max-width: 600px;
    margin: 0 auto;
    line-height: 1.6;
}

/* How-it-works step cards */
.step-card {
    background: #0A0A14;
    border: 1px solid #1a1a2e;
    border-radius: 12px;
    padding: 2rem 1.25rem;
    text-align: center;
    transition: all 0.3s ease;
    height: 100%;
}
.step-card:hover {
    border-color: #0032FF;
    box-shadow: 0 0 20px rgba(0, 50, 255, 0.12);
}
.step-number {
    width: 44px;
    height: 44px;
    background: #0032FF;
    color: #FFFFFF;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 1rem;
}
.step-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 0.5rem;
}
.step-desc {
    font-size: 0.9rem;
    color: #888;
    line-height: 1.5;
}

/* Data source pills */
.pill-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
    margin: 1rem 0;
}
.data-pill {
    background: #0A0A14;
    border: 1px solid #1a1a2e;
    border-radius: 20px;
    padding: 6px 16px;
    font-size: 0.82rem;
    color: #ccc;
    display: inline-block;
}

/* Example category label */
.example-category {
    font-size: 0.7rem;
    font-weight: 700;
    color: #0032FF;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
    text-align: center;
}

/* CTA section */
.cta-section {
    text-align: center;
    margin-top: 3rem;
}
.cta-label {
    font-size: 1.15rem;
    color: #888;
    margin-bottom: 0.75rem;
}
@keyframes cta-pulse {
    0%, 100% { box-shadow: 0 0 24px rgba(0, 50, 255, 0.2); }
    50% { box-shadow: 0 0 36px rgba(0, 50, 255, 0.35); }
}
/* Primary CTA button */
button[kind="primary"] {
    background: #0032FF !important;
    color: #FFFFFF !important;
    border: none !important;
    padding: 1.25rem 3rem !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
    letter-spacing: 0.04em;
    animation: cta-pulse 3s ease-in-out infinite;
    transition: all 0.2s ease !important;
    min-height: 64px !important;
}
button[kind="primary"]:hover {
    background: #0028CC !important;
    box-shadow: 0 0 40px rgba(0, 50, 255, 0.5) !important;
    transform: translateY(-2px);
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    border-top: 1px solid #1a1a2e;
    margin-top: 2rem;
}
.footer-attribution {
    color: #FFFFFF;
    font-size: 0.95rem;
    font-weight: 500;
    margin-bottom: 0.35rem;
}
.footer-powered {
    color: #555;
    font-size: 0.8rem;
}

/* Section headers */
.section-header {
    text-align: center;
    font-size: 1.3rem;
    font-weight: 600;
    color: #FFFFFF;
    margin: 3.5rem 0 1.5rem 0;
    letter-spacing: 0.02em;
}
</style>
"""

CHAT_CSS = """
<style>
/* Branded header bar */
.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 0;
    margin-bottom: 1rem;
    border-bottom: 1px solid #1a1a2e;
}
.chat-header-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #FFFFFF;
    letter-spacing: 0.08em;
}
.chat-header-accent {
    color: #0032FF;
}

/* Chat message styling */
[data-testid="stChatMessage"] {
    background: #0A0A14 !important;
    border: 1px solid #1a1a2e;
    border-left: 3px solid #0032FF;
    border-radius: 8px;
    margin-bottom: 0.75rem;
    padding: 1rem;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: #0A0A14 !important;
    border: 1px solid #1a1a2e !important;
    border-radius: 8px !important;
    color: #FFFFFF !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #0032FF !important;
    box-shadow: 0 0 8px rgba(0, 50, 255, 0.2) !important;
}

/* Sidebar styling for chat page */
[data-testid="stSidebar"] {
    background: #0A0A14;
    border-right: 1px solid #1a1a2e;
}
[data-testid="stSidebar"] .stButton > button {
    background: transparent;
    color: #ccc;
    border: 1px solid #1a1a2e;
    text-align: left;
    font-size: 0.88rem;
    padding: 0.5rem 0.75rem;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #0d0d1a;
    border-color: #0032FF;
    color: #FFFFFF;
}
</style>
"""
