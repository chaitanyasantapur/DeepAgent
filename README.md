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

- `deepagent.py` - Tavily `internet_search` tool + `create_deep_agent` with skills, AGENTS.md memory, `StateBackend`, `MemorySaver` checkpointer, and a QuickJS `eval` tool (`CodeInterpreterMiddleware` from `langchain-quickjs`)
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
