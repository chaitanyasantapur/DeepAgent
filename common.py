"""Shared pieces used by the main deep agent and the remote (async subagent) graphs."""

import os
from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tavily import TavilyClient

load_dotenv()

# Reads TAVILY_API_KEY from the environment (.env)
tavily_client = TavilyClient()


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search and return the results."""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


def build_model():
    """Pick the chat model from .env.

    LLM_PROVIDER=groq   (default) -> ChatGroq(GROQ_MODEL or openai/gpt-oss-120b)
    LLM_PROVIDER=openai           -> ChatOpenAI(OPENAI_MODEL or gpt-4.1)

    Note: Groq's free tier allows 8,000 tokens per minute per request. A deep
    agent with file tools, skills, memory, subagents, and the eval tool needs
    more than that, so use a paid Groq tier or OpenAI for real runs.
    """
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1"))
    return ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))
