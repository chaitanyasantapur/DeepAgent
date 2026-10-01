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


def build_model(
    provider: str | None = None,
    model_name: str | None = None,
    temperature: float | None = None,
    api_key: str | None = None,
):
    """Build the chat model. Every argument falls back to .env.

    provider:    LLM_PROVIDER  -> "groq" (default) or "openai"
    model_name:  GROQ_MODEL (default openai/gpt-oss-120b) or OPENAI_MODEL (default gpt-4.1)
    temperature: default 0.7
    api_key:     GROQ_API_KEY / OPENAI_API_KEY

    Note: Groq's free tier allows 8,000 tokens per minute per request. A deep
    agent with file tools, skills, memory, subagents, and the eval tool needs
    more than that, so use a paid Groq tier or OpenAI for real runs.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "groq")).lower()
    temperature = 0.7 if temperature is None else temperature
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4.1"),
            temperature=temperature,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )
    return ChatGroq(
        model=model_name or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=temperature,
        api_key=api_key or os.getenv("GROQ_API_KEY"),
    )
