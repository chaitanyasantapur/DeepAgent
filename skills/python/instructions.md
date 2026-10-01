# Python Skill - Instructions

## Workflow

1. **Understand the request**
   - Identify the deliverable: script, function, fix, review, or explanation.
   - Note the runtime constraints: Python version, allowed dependencies, OS, performance targets.
   - If the user shared code, read all of it before proposing changes.

2. **Decide the shape of the answer**
   - Single function or short script: write it directly.
   - Multi-file project: list the files first, then write each one.
   - Bug fix: reproduce the failure mentally, name the root cause, then patch the smallest surface.

3. **Write the code**
   - Follow the coding standards below.
   - Put configuration (paths, keys, URLs) in constants or environment variables, never inline.
   - Handle the obvious failure modes (missing file, bad input, network error) with clear messages.

4. **Verify**
   - Walk through the code once with a sample input and confirm the output.
   - Check imports, indentation, and that every name used is defined.
   - For anything non-trivial, add a `pytest` test.

5. **Explain briefly**
   - One paragraph on what the code does and any decision worth knowing.
   - List how to run it with `uv`.

## Coding Standards

- Python 3.11+ syntax: `match`, `X | None` unions, `tomllib`, `ExceptionGroup` where useful.
- Type hints on all public functions. Use `TypedDict`, `dataclass`, or `pydantic` for structured data.
- `pathlib.Path` instead of `os.path`.
- Logging via `logging`, not `print`, in anything that is not a throwaway script.
- Async: use `asyncio` with `async with` for clients, `asyncio.gather` for fan-out, and `asyncio.TaskGroup` for structured concurrency.
- Format as `ruff format` would. Line length 100.
- Docstrings on modules and public functions, one line unless the behaviour is subtle.

## Environment and Packaging

- Create a project: `uv init name && cd name`
- Add a dependency: `uv add requests`
- Add a dev dependency: `uv add --dev pytest`
- Run: `uv run script.py` or `uv run pytest`
- Pin Python: `uv python pin 3.12`
- Lock file `uv.lock` is committed. `pyproject.toml` is the single source of truth for dependencies.

## Debugging Checklist

- Read the last line of the traceback first, then walk up to the first frame in user code.
- `NameError` / `AttributeError`: typo or wrong object type. Print `type(obj)`.
- `TypeError` on call: check positional vs keyword arguments and `self`.
- `ModuleNotFoundError`: wrong environment. Confirm with `uv run python -c "import sys; print(sys.executable)"`.
- Unexpected `None`: a function missing a `return` on one branch.
- Encoding errors: open files with `encoding="utf-8"` explicitly.
- Hanging async code: an `await` is missing or a blocking call is inside a coroutine.

## Review Checklist

When asked to review code, go through this list and report only items that apply:

- Correctness: edge cases, off-by-one, mutable default arguments, exceptions swallowed silently.
- Security: `eval`, `shell=True`, unvalidated paths, secrets in source, `pickle` on untrusted input.
- Performance: repeated work inside loops, loading whole files when streaming would do, N+1 queries.
- Readability: names, function length, nesting depth, missing type hints.
- Tests: missing, brittle, or not covering the failure path.

## Performance Notes

- Measure first with `time.perf_counter()` or `cProfile`. Do not guess.
- Use built-ins and comprehensions over manual loops.
- For numeric work, suggest `numpy`; for tabular work, `pandas` or `polars`.
- For CPU-bound parallelism, `concurrent.futures.ProcessPoolExecutor`. For I/O-bound, `asyncio` or threads.
- Cache pure functions with `functools.lru_cache`.
