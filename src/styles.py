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
    padding: 4rem 1rem 2rem 1rem;
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

/* Example query cards */
.example-card {
    background: #0A0A14;
    border: 1px solid #1a1a2e;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 0.5rem;
}
.example-card:hover {
    border-color: #0032FF;
    background: #0d0d1a;
}
.example-card p {
    margin: 0;
    color: #ccc;
    font-size: 0.95rem;
}

/* CTA button */
.cta-container {
    text-align: center;
    margin: 2rem 0;
}
.cta-container .stButton > button {
    background: #0032FF;
    color: #FFFFFF;
    border: none;
    padding: 0.75rem 2.5rem;
    font-size: 1.1rem;
    font-weight: 600;
    border-radius: 8px;
    letter-spacing: 0.03em;
}
.cta-container .stButton > button:hover {
    background: #0028CC;
    box-shadow: 0 0 24px rgba(0, 50, 255, 0.3);
}

/* Footer */
.footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    color: #555;
    font-size: 0.85rem;
}

/* Section headers */
.section-header {
    text-align: center;
    font-size: 1.3rem;
    font-weight: 600;
    color: #FFFFFF;
    margin: 3rem 0 1.25rem 0;
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
