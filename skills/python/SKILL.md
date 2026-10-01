---
name: python
description: Write, review, debug, and explain Python code. Use for scripts, CLIs, data processing, async code, packaging with uv, testing with pytest, and performance questions.
license: MIT
compatibility: Python 3.11+
---

# Python Skill

Use this skill whenever the task involves writing, fixing, reviewing, or explaining Python code.

## When to Use

- The user asks for a Python script, function, class, module, or CLI
- The user shares a traceback or a bug in Python code
- The user asks how to structure, package, test, or speed up Python code
- The user asks a "how do I do X in Python" question

## Supporting Files

Read these with `read_file` (pass `limit=1000`) before starting non-trivial work:

- `instructions.md` - step-by-step workflow, coding standards, and review checklist
- `examples.md` - worked examples of requests and good answers

## Quick Rules

1. Target Python 3.11+. Use type hints, f-strings, `pathlib`, and dataclasses where they help.
2. Prefer the standard library. Add a dependency only when it clearly saves effort, and say why.
3. Every snippet must be runnable as shown. Include imports. Never leave `...` placeholders in logic.
4. For bugs, state the root cause in one sentence before showing the fix.
5. Use `uv` for environments and running (`uv run script.py`, `uv add package`). Do not suggest `pip install`.
6. Tests use `pytest`. Show at least one test for any non-trivial function you write.
7. If the answer is code plus explanation, keep the explanation under the code and short.
8. When you need facts about a library's current API, use `internet_search` and cite the source.
