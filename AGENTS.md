# AGENTS.md

This file is loaded into the deep agent's system prompt on every invocation
via `create_deep_agent(memory=["/AGENTS.md"])`. Put anything here the agent
should always know.

## How to use this project

- Install: `uv sync`
- Keys go in `.env`: `GROQ_API_KEY`, `TAVILY_API_KEY`
- Run the agent: `uv run deepagent.py "your question"` (also `uv run context_example.py`)
- Skills live in `skills/<name>/` and are loaded via `create_deep_agent(skills=["/skills/"])`
- Reports the agent writes go to `workspace/reports/`
- The agent uses the Groq model `openai/gpt-oss-120b` and the `internet_search` tool (Tavily)
- `deepagent.py` uses `StateBackend` + `MemorySaver`: files live in per-thread LangGraph state; `skills/` and this file are preloaded into state on every call, and reports are copied to `workspace/reports/` on disk after each turn
- `context_example.py` and `backends_demo.py` show the `FilesystemBackend` / `StoreBackend` alternatives
- The agent also has an `eval` tool (QuickJS sandbox via `langchain-quickjs`) for calculations and data wrangling; `tools.internetSearch(...)` is callable from inside it

## User preferences

- Prefers `uv` over `pip`
- Prefers short, direct answers with sources listed at the end

## How the agent should behave

- Research with `internet_search` before answering factual questions
- Cite sources at the end of the answer
- Keep answers under 200 words unless asked for a full report
- If the user shares a lasting preference, update this file with `edit_file`
- Before answering, check the Skills System list; when a skill matches, read its `SKILL.md`, then `instructions.md` and `examples.md` in the same folder
- After every answer, follow the `report-writer` skill and save a report to `/workspace/reports/` (no exceptions)

## Skills available

- `python` - writing, reviewing, debugging Python; uv and pytest conventions
- `aws` - AWS architecture, IAM, CLI, boto3, CDK/Terraform snippets, troubleshooting
- `web-research` - search, cross-check, and cite with `internet_search`
- `report-writer` - mandatory end-of-answer report saved to `/workspace/reports/<date>-<slug>.md`

Each skill folder has `SKILL.md` (frontmatter + quick rules), `instructions.md` (full workflow), and `examples.md` (worked examples). `report-writer` also has `template.md`.

## Deep agents architecture (deepagents 0.7.x)

- `create_deep_agent(model, tools, system_prompt, backend, memory, subagents, middleware, checkpointer, store)` returns a compiled LangGraph graph
- Built-in tools on every deep agent: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` (needs a sandbox backend), `task` (calls subagents); this project adds `eval` (JavaScript REPL) via `CodeInterpreterMiddleware`
- Middleware runs in this order around each model call: Skills, Filesystem, SubAgent, Summarization, PatchToolCalls, then user middleware, then prompt caching, Memory, HumanInTheLoop, UnsupportedContent
- System prompt assembly: your `system_prompt` first, then harness profile text, then the `<agent_memory>` block built from the `memory=[...]` files
- Backends decide where file tools store data: `StateBackend` (per-thread state, default), `FilesystemBackend` (real disk under `root_dir`), `StoreBackend` (LangGraph store, shared across threads), `CompositeBackend` (route by path prefix)
- Context protection: tool results over 20k tokens are saved to `/large_tool_results/<id>` and replaced with a stub; when history nears the model limit older messages are summarized and saved to `/conversation_history/<session>.md`
- Subagents are isolated by default: they get only the task text and return only their final answer to the parent. `mode="fork"` subagents continue the parent's conversation instead
- This project's sync subagents (`task` tool): `researcher` (isolated, web research), `coder` (isolated, Python/AWS), `critic` (fork, reviews the draft)
- Async subagents (`start_async_task` / `check_async_task` / `list_async_tasks` / `update_async_task` / `cancel_async_task`): `remote_researcher` and `remote_summarizer`, background runs on the LangGraph server started with `uv run langgraph dev`; only present when `LANGGRAPH_SERVER_URL` is set
- Subagents never write reports; the main agent writes the report after every answer
- Memory files are read on every invocation, so edits to this file take effect on the next call
