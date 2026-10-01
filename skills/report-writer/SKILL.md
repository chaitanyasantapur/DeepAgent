---
name: report-writer
description: MANDATORY after every answer. Writes a structured markdown report of the question, the answer, the skills and tools used, and the sources to /workspace/reports/ using write_file. Also use when the user explicitly asks for a report.
license: MIT
---

# Report Writer Skill

This skill runs at the end of **every** response. Once you have finished researching and have your final answer ready, you must save a report file before you reply to the user.

## When to Use

- Always, as the last step of answering any user query
- When the user explicitly asks for "a report", "write this up", or "document this"

## Supporting Files

- `instructions.md` - the exact steps, file naming rules, and section definitions
- `examples.md` - complete sample reports
- `template.md` - the markdown template to fill in

## Quick Rules

1. Reports live in `/workspace/reports/`. Create the file with `write_file`.
2. File name: `<YYYY-MM-DD>-<slug>.md`. The date comes from the "Today's date" line in your system prompt. The slug is 3-6 lowercase words from the question joined by hyphens.
3. Fill every section of `template.md`. Write "None" rather than leaving a section empty.
4. The `Answer` section is the same answer you give the user, not a shortened version.
5. List every skill you read and every tool you called in this turn.
6. Sources are a numbered list of title and URL. If you did no searching, write "None (answered from prior knowledge)".
7. After saving, finish your reply to the user with one line: `Report saved to /workspace/reports/<file>.md`.
8. Never skip the report, even for short or conversational answers. For trivial exchanges the report can be short, but it must exist.
