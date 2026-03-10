# Take-Home Project: Economic Data Chat Application – 1 Week

## What to Build
A chat app where a user types a plain English question about economic data and gets back a written answer and a chart. Example: "Show me inflation over the last 5 years" → app fetches real data, LLM explains it, chart appears in the chat.

## 1. Data Layer
- Pick any free public economic data source — FRED, BLS, World Bank, Alpha Vantage, etc.
- All data sources used must be public so that your work product (code, outputs, and charts) can be created, run, and shared without violating any terms of use
- You are free to write your own API call or use a library that is reliable
- Return clean structured data — a Pandas DataFrame is fine
- Handle errors gracefully — bad inputs, API downtime, and missing values should not crash the app

## 2. LLM Layer
- Use LangChain to manage LLM interactions and tool calling
- The LLM should decide on its own when to fetch data based on what the user asks — use LangChain's agents for this
- Responses to the user must always be plain English — never return raw JSON or a data dump to the user
- Maintain conversation history so the user can ask natural follow-up questions. You don't need to maintain out of state memory just for the session user is currently in

## 3. UI Layer
- Build a chat interface — Streamlit, Panel, Gradio, Next.js or any other way you feel is better
- Charts should appear in-line with the conversation, not in a separate panel
- Support at least a few chart types based on what the user asks — line, bar, and multi-series comparison
- Try to make such that it does not crash on user input, including vague or nonsense queries

## Environment and Setup
- Use uv to manage all dependencies
- Include a pyproject.toml and uv.lock
- Running uv sync and then uv run should be the only steps needed to get it running on any machine

## Secrets and Keys
- All API keys go in a .env file only
- Include a .env.example with all the variable names but blank values
- Never hardcode keys anywhere in the codebase

## Code Organization
- Keep data fetching, LLM logic, and visualization code in separate files — do not put everything in one file
- Beyond that, organize it however makes sense to you

## Submission
- We will schedule a Webex walkthrough approximately one week after you receive the assignment.
- You should not send any code or materials into Millennium systems in advance.
- Please be prepared to share screen via Webex during the debrief call and be prepared to run it locally through your own environment.
- During the scheduled session, you will walk the team through your project live, including how to set it up, how it runs, and how you approached the problem.
- If you choose to prepare a short write-up, architecture diagram, or notes to aid the discussion, you may share those live on screen during the debrief, but they should also remain on your own system.

## Walkthrough will Cover These Points
- Walk through how you organized the code and why
- Demo the app live with different queries including at least one vague or tricky one
- Explain specifically how you used LangChain — which abstractions and why
- Call out one or two decisions you found interesting or unexpectedly difficult
- Be prepared to answer questions on the logic (i.e. you are free to use any tool available including AI tools, but you need to understand what is happening in your code and why)

## What We Are Looking For
- Does it run out of the box with no manual setup
- Is the code readable and reasonably organized
- Is LangChain being used thoughtfully and not just dropped in
- Does the LLM know when to fetch data versus when to just answer
- Are the charts appropriate for what was asked
- How does it handle edge cases — vague questions, bad input, API errors

## What We Are Leaving Open on Purpose
- Which freely distributable public datasets you use
- How you structure your files and folders
- Which chart library you use (Plotly, Altair, Matplotlib, etc.)
- Which LangChain abstractions you use
- Any extra features you want to add
