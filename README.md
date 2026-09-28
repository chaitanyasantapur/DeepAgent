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

- `deepagent.py` - Tavily `internet_search` tool + `create_deep_agent` with system prompt and Groq model
- `deepagent.ipynb` - same code split into cells
- `requirements.txt` / `pyproject.toml` - dependencies

## Backends notebook

`backends.ipynb` shows the three storage backends for the agent's built-in
file tools, plus a CompositeBackend that mixes them:

- `StateBackend` - files in LangGraph state, per thread, ephemeral
- `FilesystemBackend` - real files on disk under `workspace/`
- `StoreBackend` - files in a LangGraph store, shared across threads

`backends_demo.py` is the same code as a runnable script.
