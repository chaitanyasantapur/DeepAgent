"""Graphs served by `langgraph dev` and used as async subagents.

These are deliberately lightweight `create_agent` graphs (not full deep agents)
so each call stays small: the parent deep agent launches them as background runs
through `start_async_task` and polls with `check_async_task`.

Served graphs (see langgraph.json):
    research_agent   - internet_search + sourced summary
    summarizer_agent - no tools, structured summary of the given text

Run locally:
    uv run langgraph dev            # http://127.0.0.1:2024
"""

from dotenv import load_dotenv
from langchain.agents import create_agent

from common import build_model, internet_search

load_dotenv()

research_agent = create_agent(
    model=build_model(),
    tools=[internet_search],
    system_prompt=(
        "You are a web research specialist. Run at least two internet_search calls "
        "with different phrasings, prefer primary sources, and cross-check key facts. "
        "Reply with a 2-3 sentence answer, supporting bullets with dates, and a "
        "numbered Sources list (title - URL)."
    ),
)

summarizer_agent = create_agent(
    model=build_model(),
    tools=[],
    system_prompt=(
        "You summarize text. Reply with: a one-paragraph summary, 3-7 key points as "
        "bullets, and an 'Open questions' list. Keep the whole reply under 250 words. "
        "Do not add information that is not in the text."
    ),
)
