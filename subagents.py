"""Subagent definitions for the deep agent.

Two kinds are wired into `create_deep_agent(subagents=[...])`:

Synchronous (`SubAgent`) - run in-process through the parent's `task` tool. The
parent blocks until the subagent returns its final answer.

    - `researcher` (isolated): web research with internet_search + the
      web-research skill. Sees only the delegated task text.
    - `coder`      (isolated): Python / AWS code and reviews using the python
      and aws skills. Sees only the delegated task text.
    - `critic`     (fork):     continues the parent's conversation to review
      the draft answer. Sees the full history. `mode="fork"` is experimental
      in deepagents 0.7.x and cannot define its own skills.

Asynchronous (`AsyncSubAgent`) - run as background runs on an Agent Protocol
server (LangGraph server). The parent gets `start_async_task`,
`check_async_task`, `update_async_task`, `cancel_async_task`, and
`list_async_tasks` tools and keeps working while the remote run proceeds.

    - `remote_researcher` -> graph `research_agent` in remote_agents.py
    - `remote_summarizer` -> graph `summarizer_agent` in remote_agents.py

Start the server with `uv run langgraph dev` (port 2024) and set
`LANGGRAPH_SERVER_URL=http://127.0.0.1:2024` in .env to enable them.
"""

import os

from deepagents.middleware.async_subagents import AsyncSubAgent
from deepagents.middleware.subagents import SubAgent

SKILLS_PATH = "/skills/"

NO_REPORT_RULE = (
    "Do NOT write report files; only the main agent does that. "
    "Return your findings as plain markdown in your final message."
)

researcher: SubAgent = {
    "name": "researcher",
    "description": (
        "Researches a question on the web and returns a sourced summary. Use for any "
        "factual, current-events, comparison, or 'what is the latest' question that "
        "needs more than one or two searches, or when you want research done in "
        "parallel while you work on something else."
    ),
    "system_prompt": (
        "You are a research specialist. Read /skills/web-research/SKILL.md and its "
        "instructions.md with read_file (limit=1000) and follow that workflow: at least "
        "two internet_search calls with different phrasings, prefer primary sources, "
        "cross-check key facts, note dates. Reply with: a 2-3 sentence answer, "
        "supporting bullets, and a numbered Sources list (title - URL). "
        + NO_REPORT_RULE
    ),
    "skills": [SKILLS_PATH],
    # tools omitted -> inherits the parent's tools (internet_search + file tools)
}

coder: SubAgent = {
    "name": "coder",
    "description": (
        "Writes, reviews, or debugs Python and AWS code (boto3, IAM policies, CLI, CDK). "
        "Use when the user needs working code or a code review and the task is "
        "self-contained enough to describe in a paragraph."
    ),
    "system_prompt": (
        "You are a senior engineer. For Python work read /skills/python/SKILL.md and "
        "instructions.md; for AWS work read /skills/aws/SKILL.md and instructions.md "
        "(use read_file with limit=1000). Follow their rules: runnable code, type hints, "
        "least-privilege IAM, uv not pip. If asked to write files, use write_file under "
        "/workspace/code/. Reply with the code, how to run it, and one short paragraph "
        "of explanation. " + NO_REPORT_RULE
    ),
    "skills": [SKILLS_PATH],
}

critic: SubAgent = {
    "name": "critic",
    "description": (
        "Reviews the answer you have drafted so far in this conversation and returns "
        "concrete corrections. Use before finalising a long or high-stakes answer. It "
        "already sees the whole conversation, so the task text only needs to say what "
        "to focus on."
    ),
    "mode": "fork",  # continues the parent's conversation instead of starting blank
    "system_prompt": (
        "You are now acting as a critical reviewer of the draft answer above. Check "
        "facts against the sources cited, look for missing steps, unsafe advice, and "
        "unclear wording. Reply with a short list of specific fixes, or 'No changes "
        "needed'. Do not call tools unless a fact must be re-checked. " + NO_REPORT_RULE
    ),
}

SYNC_SUBAGENTS: list[SubAgent] = [researcher, coder, critic]


def async_subagents(url: str | None = None) -> list[AsyncSubAgent]:
    """Async subagent specs for the server at `url` (default: LANGGRAPH_SERVER_URL).

    Returns an empty list when no URL is available.

    The specs point at graphs served by `langgraph dev` (see langgraph.json and
    remote_agents.py). Without a URL the SDK would try in-process ASGI transport,
    which needs the langgraph_api server app and an `ainvoke` entrypoint, so we
    require an explicit URL for a predictable setup.
    """
    url = url or os.getenv("LANGGRAPH_SERVER_URL")
    if not url:
        return []
    return [
        {
            "name": "remote_researcher",
            "description": (
                "Background web researcher running on the LangGraph server. Start it "
                "with start_async_task when research will take a while or when you "
                "want several topics researched at once, then keep working and poll "
                "with check_async_task. Returns a sourced summary."
            ),
            "graph_id": "research_agent",
            "url": url,
        },
        {
            "name": "remote_summarizer",
            "description": (
                "Background summarizer running on the LangGraph server. Give it long "
                "text (a document, search results, a transcript) and it returns a "
                "structured summary with key points and open questions."
            ),
            "graph_id": "summarizer_agent",
            "url": url,
        },
    ]
