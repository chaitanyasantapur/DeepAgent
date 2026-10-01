"""Deep agent with Tavily web search, skills, memory, a JS code interpreter,
sync + async subagents, and a per-thread checkpointer.

`build_agent()` is the configurable factory used by the Streamlit app
(`app.py`); the module-level `agent` is the default build used by the CLI.

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
- `CodeInterpreterMiddleware` - a sandboxed QuickJS `eval` tool; `internet_search`
  is callable from JS via `tools.internetSearch(...)`.
- `subagents=[...]` - synchronous subagents (researcher, coder, critic) called
  through the `task` tool, plus asynchronous subagents (remote_researcher,
  remote_summarizer) on a LangGraph server when a server URL is given.

The `report-writer` skill is mandatory by default: after every answer the agent
saves a markdown report to `/workspace/reports/` in state, and `ask()` /
`save_reports()` copy it to `workspace/reports/` on disk.
"""

import os
from datetime import date
from pathlib import Path

from langchain_quickjs import CodeInterpreterMiddleware
from langgraph.checkpoint.memory import MemorySaver

from common import build_model, internet_search  # noqa: F401  (re-exported for context_example.py)
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.backends.utils import create_file_data
from subagents import SYNC_SUBAGENTS, async_subagents

PROJECT_ROOT = Path(__file__).parent
SKILLS_DIR = PROJECT_ROOT / "skills"
SKILLS_PATH = "/skills/"  # path of the skills library inside the agent's state
MEMORY_FILE = "/AGENTS.md"
REPORTS_PATH = "/workspace/reports/"  # where the report-writer skill writes
REPORTS_DIR = PROJECT_ROOT / "workspace" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# One checkpointer for the whole process so threads survive agent rebuilds
# (e.g. when the Streamlit sidebar changes the model or feature flags).
checkpointer = MemorySaver()


def load_context_files(*, skills: bool = True, memory: bool = True) -> dict:
    """Read skills/ and AGENTS.md from disk into StateBackend file entries."""
    files = {}
    if skills:
        for path in sorted(SKILLS_DIR.rglob("*")):
            if path.is_file() and not path.name.startswith("."):
                agent_path = SKILLS_PATH + path.relative_to(SKILLS_DIR).as_posix()
                files[agent_path] = create_file_data(path.read_text(encoding="utf-8"))
    if memory:
        files[MEMORY_FILE] = create_file_data((PROJECT_ROOT / "AGENTS.md").read_text(encoding="utf-8"))
    return files


def build_system_prompt(
    *,
    skills: bool = True,
    memory: bool = True,
    code_interpreter: bool = True,
    web_search: bool = True,
    sync_subagents: bool = True,
    async_enabled: bool = False,
    report_required: bool = True,
    answer_style: str = "Short answer",
) -> str:
    parts = [f"You are an expert researcher and engineer.\n\nToday's date: {date.today().isoformat()}"]
    if skills:
        parts.append(
            "You have a skills library (see the Skills System section below). Before\n"
            "answering, check whether a skill matches the task. If it does, read its\n"
            "SKILL.md with read_file (limit=1000) and then read the instructions.md and\n"
            "examples.md files next to it. Follow them."
        )
    if web_search:
        parts.append(
            "You have an internet_search tool. Use it to look up current information\n"
            "before answering factual questions, and cite your sources at the end."
        )
    if code_interpreter:
        parts.append(
            "You have an eval tool that runs JavaScript in a sandbox. Use it for\n"
            "arithmetic, date math, parsing or transforming data"
            + (", and for looping over\ntools.internetSearch(...) calls when you need several searches at once" if web_search else "")
            + ". Never guess at a calculation you could run."
        )
    if sync_subagents or async_enabled:
        delegation = []
        if sync_subagents:
            delegation.append(
                "You can delegate with the task tool. Available subagents: researcher\n"
                "(isolated web research), coder (Python/AWS code), critic (fork; reviews your\n"
                "draft with full context). Delegate when a sub-problem is self-contained or\n"
                "when two things can be researched in parallel; otherwise do it yourself."
            )
        if async_enabled:
            delegation.append(
                "Async subagent tools are present (start_async_task, check_async_task,\n"
                "list_async_tasks). Use them for long-running research you can poll later,\n"
                "and finish other work while they run."
            )
        delegation.append("Subagents never write reports; you do.")
        parts.append("\n".join(delegation))
    if answer_style == "Full report":
        parts.append("Answer style: write a full, well-structured report with headings. Length is not limited.")
    else:
        parts.append("Answer style: short and direct, under 200 words unless the user asks for a full report.")
    if report_required:
        parts.append(
            "MANDATORY FINAL STEP: after you have composed your answer and before you\n"
            f"reply, follow the report-writer skill and save a report to {REPORTS_PATH}\n"
            "with write_file. End your reply with the line\n"
            f'"Report saved to {REPORTS_PATH}<file>.md".'
        )
    if memory:
        parts.append(
            "Your system prompt also ends with an <agent_memory> block loaded from\n"
            "AGENTS.md. Treat it as standing instructions."
        )
    return "\n\n".join(parts)


def build_agent(
    model=None,
    *,
    skills: bool = True,
    memory: bool = True,
    code_interpreter: bool = True,
    web_search: bool = True,
    sync_subagents: bool = True,
    async_server_url: str | None = None,
    report_required: bool = True,
    answer_style: str = "Short answer",
):
    """Create a deep agent with the selected features. `model` defaults to build_model()."""
    model = model or build_model()
    tools = [internet_search] if web_search else []
    middleware = []
    if code_interpreter:
        middleware.append(
            CodeInterpreterMiddleware(
                timeout=5.0,
                mode="thread",  # REPL globals persist across turns of the same thread
                ptc=["internet_search"] if web_search else None,
            )
        )
    subagents = []
    if sync_subagents:
        subagents.extend(SYNC_SUBAGENTS)
    async_specs = async_subagents(async_server_url) if async_server_url else []
    subagents.extend(async_specs)

    return create_deep_agent(
        model=model,
        tools=tools,
        system_prompt=build_system_prompt(
            skills=skills,
            memory=memory,
            code_interpreter=code_interpreter,
            web_search=web_search,
            sync_subagents=sync_subagents,
            async_enabled=bool(async_specs),
            report_required=report_required,
            answer_style=answer_style,
        ),
        backend=StateBackend(),
        checkpointer=checkpointer,
        skills=[SKILLS_PATH] if skills else None,
        memory=[MEMORY_FILE] if memory else None,
        middleware=middleware,
        subagents=subagents or None,
    )


# Default build (CLI, notebooks): everything on; async only if LANGGRAPH_SERVER_URL is set.
agent = build_agent(async_server_url=os.getenv("LANGGRAPH_SERVER_URL"))


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


def ask(question: str, thread_id: str = "default", agent_=None) -> str:
    """Send one turn on `thread_id`, print the answer, persist reports."""
    agent_ = agent_ or agent
    config = {"configurable": {"thread_id": thread_id}}
    before = {p for p in agent_.get_state(config).values.get("files", {}) if p.startswith(REPORTS_PATH)}
    result = agent_.invoke(
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
