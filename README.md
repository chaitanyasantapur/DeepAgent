# Deep agent with Tavily web search

## Setup (uv)

```bash
cd /Users/kas/DeepAgent
uv sync                      # creates .venv and installs pyproject.toml deps
# or: uv pip install --python .venv/bin/python -r requirements.txt
```

Fill in `.env`:

```
GROQ_API_KEY=gsk_...
OPENAI_API_KEY=sk-...        # only needed if you switch to ChatOpenAI
TAVILY_API_KEY=tvly-...      # https://app.tavily.com
```

## Run the chat UI (Streamlit)

```bash
uv run streamlit run app.py
```

The sidebar follows the earlier LangGraph chatbot layout and is driven by `uiconfig.ini`:

- **Configuration**: Select LLM (Groq / OpenAI), Select Model (with info caption), API Key
  (password field, falls back to `.env`), Temperature slider.
- **Agent options**: Answer style radio (Short answer / Full report) and feature checkboxes:
  skills library, AGENTS.md memory, web search (with Tavily key field), code interpreter
  (`eval`), sync subagents, async subagents (with server URL field), write a report after
  every answer, show tool activity.
- **Conversation**: thread selector and "New thread". Threads live in one shared
  `MemorySaver`, so changing the model or features rebuilds the agent but keeps history.
- **Active capabilities** and **Reports** expanders show what is loaded, tracked async
  tasks, and let you preview or download reports from `workspace/reports/`.

Tool calls (eval, searches, file reads, subagent delegation) stream into a status box
above each answer. With sync subagents unchecked the `task` tool is still present because
deepagents always ships a built-in general-purpose subagent.

## Run as a script

```bash
uv run deepagent.py
```

## Run as a notebook

A Jupyter kernel named "Python (deepagent)" is registered for this venv.

```bash
uv run jupyter lab deepagent.ipynb      # or open in VS Code and pick the kernel
```

## Files

- `app.py` + `uiconfig.ini` / `uiconfig.py` - Streamlit chat UI (see above)
- `deepagent.py` - `build_agent()` factory and default agent: `create_deep_agent` with skills, AGENTS.md memory, `StateBackend`, `MemorySaver` checkpointer, a QuickJS `eval` tool (`CodeInterpreterMiddleware` from `langchain-quickjs`), and sync + async subagents
- `common.py` - shared `internet_search` (Tavily) tool and `build_model()`
- `subagents.py` - synchronous `SubAgent` specs (researcher, coder, critic) and async `AsyncSubAgent` specs (remote_researcher, remote_summarizer)
- `remote_agents.py` + `langgraph.json` - the graphs served by `langgraph dev` that back the async subagents
- `deepagent.ipynb` - same code split into cells
- `requirements.txt` / `pyproject.toml` - dependencies

## Backends notebook

`backends.ipynb` shows the three storage backends for the agent's built-in
file tools, plus a CompositeBackend that mixes them:

- `StateBackend` - files in LangGraph state, per thread, ephemeral
- `FilesystemBackend` - real files on disk under `workspace/`
- `StoreBackend` - files in a LangGraph store, shared across threads

`backends_demo.py` is the same code as a runnable script.

## Skills

`deepagent.py` loads skills from `skills/` with `create_deep_agent(skills=["/skills/"])`.
The backend is a `StateBackend`, so `load_context_files()` reads `skills/**` and `AGENTS.md`
from disk and passes them as `files={...}` on every invoke. Each skill is a directory:

```
skills/
  python/          SKILL.md, instructions.md, examples.md
  aws/             SKILL.md, instructions.md, examples.md
  web-research/    SKILL.md, instructions.md, examples.md
  report-writer/   SKILL.md, instructions.md, examples.md, template.md
```

- `SKILL.md` is required by deepagents. Its YAML frontmatter `name` must equal the
  folder name, and the `description` is what the agent sees in its system prompt.
- `instructions.md` and `examples.md` are supporting files. The agent reads them with
  `read_file` only when a skill is relevant (progressive disclosure).
- `report-writer` is mandatory: after every answer the agent writes
  `/workspace/reports/<YYYY-MM-DD>-<slug>.md` in state, and `ask()` copies new
  reports to `workspace/reports/` on disk.

## Checkpointer, threads, and the eval tool

- `MemorySaver` keeps messages, files, and REPL state per `thread_id`. Call
  `ask("...", thread_id="alice")` repeatedly to continue one conversation; a new
  `thread_id` starts fresh. Swap in a SQLite or Postgres checkpointer for persistence
  across process restarts.
- `CodeInterpreterMiddleware(mode="thread", ptc=["internet_search"])` adds an `eval`
  tool that runs JavaScript in a QuickJS sandbox (5 s timeout, 64 MiB heap). Globals
  persist across turns of a thread, and JS code can call `tools.internetSearch({query})`
  to orchestrate several searches in one call.
- Skills are cached per thread. After editing a skill, start a new thread or pass
  `"skills_metadata": None` in the invoke input.

Add a skill: create `skills/<name>/SKILL.md` with `name:` and `description:` frontmatter,
add `instructions.md` / `examples.md` next to it, and list it in `AGENTS.md`.

Run:

```bash
uv run deepagent.py "How do I give a Lambda read access to one S3 bucket?"
ls workspace/reports/
```

Model selection is driven by `.env`: `LLM_PROVIDER=groq` (default, `GROQ_MODEL`) or
`LLM_PROVIDER=openai` (`OPENAI_MODEL`, default `gpt-4.1`).

Groq's free tier allows 8,000 tokens per minute and rejects any single request above
that. A deep agent with file tools, skills, memory, and the eval tool sends more than
8,000 tokens per model call, so skills-enabled runs need a paid Groq tier or `LLM_PROVIDER=openai` with a
real `OPENAI_API_KEY`.

## Subagents

### Synchronous (in-process, via the `task` tool)

Defined in `subagents.py` and passed as `create_deep_agent(subagents=[...])`. The parent
blocks until the subagent returns its final message.

| Name | Mode | What it does |
|---|---|---|
| `researcher` | isolated | Web research with `internet_search` and the web-research skill. Sees only the task text. |
| `coder` | isolated | Python / AWS code and reviews using the python and aws skills. Sees only the task text. |
| `critic` | fork | Continues the parent's conversation to review the draft answer. Sees full history. Experimental in deepagents 0.7.x. |

Isolated subagents get a fresh context with their own `system_prompt`, the parent's tools,
and the skills listed in their spec. Fork subagents inherit the parent's prompt and history
and cannot declare their own skills.

### Asynchronous (background runs on a LangGraph server)

Async subagents are `AsyncSubAgent` specs pointing at graphs on an Agent Protocol server.
The parent gets `start_async_task`, `check_async_task`, `update_async_task`,
`cancel_async_task`, and `list_async_tasks`, and keeps working while the remote run proceeds.
Task IDs are stored in the parent's state under `async_tasks`.

The graphs live in `remote_agents.py` and are registered in `langgraph.json`:

- `research_agent` -> subagent `remote_researcher`
- `summarizer_agent` -> subagent `remote_summarizer`

Run them locally (dev dependency `langgraph-cli[inmem]` is already installed):

```bash
uv run langgraph dev --no-browser --port 2024     # terminal 1
```

Then add to `.env` and run the main agent:

```
LANGGRAPH_SERVER_URL=http://127.0.0.1:2024
```

Without `LANGGRAPH_SERVER_URL` the async subagents are not registered, so the agent still
works with sync subagents only. Point the URL at a LangGraph Platform deployment to run the
same specs remotely (the SDK picks up `LANGSMITH_API_KEY` for auth).
