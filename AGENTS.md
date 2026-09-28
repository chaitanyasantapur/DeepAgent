# AGENTS.md

This file is loaded into the deep agent's system prompt on every invocation
via `create_deep_agent(memory=["/AGENTS.md"])`. Put anything here the agent
should always know.

## How to use this project

- Install: `uv sync`
- Keys go in `.env`: `GROQ_API_KEY`, `TAVILY_API_KEY`
- Run the context example: `uv run context_example.py`
- The agent uses the Groq model `openai/gpt-oss-120b` and the `internet_search` tool (Tavily)
- Files the agent reads or writes live under this project folder (`FilesystemBackend`)

## User preferences

- Prefers `uv` over `pip`
- Prefers short, direct answers with sources listed at the end

## How the agent should behave

- Research with `internet_search` before answering factual questions
- Cite sources at the end of the answer
- Keep answers under 200 words unless asked for a full report
- If the user shares a lasting preference, update this file with `edit_file`

## Deep agents architecture (deepagents 0.7.x)

- `create_deep_agent(model, tools, system_prompt, backend, memory, subagents, middleware, checkpointer, store)` returns a compiled LangGraph graph
- Built-in tools on every deep agent: `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, `execute` (needs a sandbox backend), `task` (calls subagents)
- Middleware runs in this order around each model call: Skills, Filesystem, SubAgent, Summarization, PatchToolCalls, then user middleware, then prompt caching, Memory, HumanInTheLoop, UnsupportedContent
- System prompt assembly: your `system_prompt` first, then harness profile text, then the `<agent_memory>` block built from the `memory=[...]` files
- Backends decide where file tools store data: `StateBackend` (per-thread state, default), `FilesystemBackend` (real disk under `root_dir`), `StoreBackend` (LangGraph store, shared across threads), `CompositeBackend` (route by path prefix)
- Context protection: tool results over 20k tokens are saved to `/large_tool_results/<id>` and replaced with a stub; when history nears the model limit older messages are summarized and saved to `/conversation_history/<session>.md`
- Subagents are isolated by default: they get only the task text and return only their final answer to the parent
- Memory files are read on every invocation, so edits to this file take effect on the next call
