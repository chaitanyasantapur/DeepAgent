"""Deep agent with Tavily web search, skills, memory, a JS code interpreter,
and a per-thread checkpointer.

Storage and context:

- `StateBackend`  - the agent's file tools (ls, read_file, write_file, ...) work on
  files held in LangGraph state. Skills and AGENTS.md are loaded from disk into
  that state on each call via `files={...}`.
- `MemorySaver`   - in-memory checkpointer so state (messages, files, REPL
  snapshot) survives between turns of the same `thread_id`.
- `skills=["/skills/"]`  - every `skills/<name>/SKILL.md` is listed in the system
  prompt; the agent reads the full SKILL.md, instructions.md, and examples.md
  with `read_file` when a task matches.
- `memory=["/AGENTS.md"]` - injected into the system prompt as <agent_memory>.
- `CodeInterpreterMiddleware` - a sandboxed QuickJS `eval` tool for calculations
  and data wrangling; `internet_search` is callable from JS via
  `tools.internetSearch(...)`.

The `report-writer` skill is mandatory: after every answer the agent saves a
markdown report to `/workspace/reports/` in state, and `ask()` copies it to
`workspace/reports/` on disk.
"""

import os
from datetime import date
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_quickjs import CodeInterpreterMiddleware
from langgraph.checkpoint.memory import MemorySaver
from tavily import TavilyClient

from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.utils import create_file_data

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
SKILLS_DIR = PROJECT_ROOT / "skills"
SKILLS_PATH = "/skills/"  # path of the skills library inside the agent's state
MEMORY_FILE = "/AGENTS.md"
REPORTS_PATH = "/workspace/reports/"  # where the report-writer skill writes
REPORTS_DIR = PROJECT_ROOT / "workspace" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

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


def load_context_files() -> dict:
    """Read skills/ and AGENTS.md from disk into StateBackend file entries.

    Keys are agent-side paths ("/skills/python/SKILL.md", "/AGENTS.md"); values
    are FileData dicts the StateBackend understands.
    """
    files = {}
    for path in sorted(SKILLS_DIR.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            agent_path = SKILLS_PATH + path.relative_to(SKILLS_DIR).as_posix()
            files[agent_path] = create_file_data(path.read_text(encoding="utf-8"))
    files[MEMORY_FILE] = create_file_data((PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8"))
    return files


def build_model():
    """Pick the chat model from .env.

    LLM_PROVIDER=groq   (default) -> ChatGroq(GROQ_MODEL or openai/gpt-oss-120b)
    LLM_PROVIDER=openai           -> ChatOpenAI(OPENAI_MODEL or gpt-4.1)

    Note: Groq's free tier allows 8,000 tokens per minute per request. A deep
    agent with file tools, skills, memory, and the eval tool needs more than
    that, so use a paid Groq tier or OpenAI for real runs.
    """
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4.1"))
    return ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"))


system_prompt = f"""You are an expert researcher and engineer.

Today's date: {date.today().isoformat()}

You have a skills library (see the Skills System section below). Before
answering, check whether a skill matches the task. If it does, read its
SKILL.md with read_file (limit=1000) and then read the instructions.md and
examples.md files next to it. Follow them.

You have an internet_search tool. Use it to look up current information
before answering factual questions, and cite your sources at the end.

You have an eval tool that runs JavaScript in a sandbox. Use it for
arithmetic, date math, parsing or transforming data, and for looping over
tools.internetSearch(...) calls when you need several searches at once.
Never guess at a calculation you could run.

MANDATORY FINAL STEP: after you have composed your answer and before you
reply, follow the report-writer skill and save a report to {REPORTS_PATH}
with write_file. End your reply with the line
"Report saved to {REPORTS_PATH}<file>.md".

Your system prompt also ends with an <agent_memory> block loaded from
AGENTS.md. Treat it as standing instructions."""

model = build_model()
backend = StateBackend()
checkpointer = MemorySaver()

code_interpreter = CodeInterpreterMiddleware(
    timeout=5.0,
    mode="thread",  # REPL globals persist across turns of the same thread
    ptc=["internet_search"],  # callable from JS as tools.internetSearch({query: "..."})
)

agent = create_deep_agent(
    model=model,
    tools=[internet_search],
    system_prompt=system_prompt,
    backend=backend,
    checkpointer=checkpointer,
    skills=[SKILLS_PATH],
    memory=[MEMORY_FILE],
    middleware=[code_interpreter],
)


def save_reports(files: dict, before: set[str]) -> list[Path]:
    """Copy any new /workspace/reports/*.md from agent state to disk."""
    saved = []
    for agent_path, file_data in files.items():
        if agent_path.startswith(REPORTS_PATH) and agent_path not in before:
            content = file_data["content"]
            if isinstance(content, list):
                content = "\n".join(content)
            target = REPORTS_DIR / agent_path.removeprefix(REPORTS_PATH)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            saved.append(target)
    return saved


def ask(question: str, thread_id: str = "default") -> str:
    """Send one turn to the agent on `thread_id`, print the answer, persist reports.

    The same `thread_id` keeps conversation history, files, and REPL state
    between calls thanks to the MemorySaver checkpointer.
    """
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = agent.get_state(config)
    before = {p for p in snapshot.values.get("files", {}) if p.startswith(REPORTS_PATH)}

    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}], "files": load_context_files()},
        config=config,
    )
    answer = result["messages"][-1].content
    print(answer)

    saved = save_reports(result.get("files", {}), before)
    if saved:
        print("\n[reports written]", ", ".join(str(p.relative_to(PROJECT_ROOT)) for p in saved))
    else:
        print("\n[warning] agent did not write a report this turn")
    return answer


if __name__ == "__main__":
    import sys

    ask(" ".join(sys.argv[1:]) or "what is deep agents", thread_id="cli")
