---
name: web-research
description: Structured workflow for researching a topic with the internet_search tool, cross-checking sources, and producing a sourced summary. Use for any factual, current-events, comparison, or "what is the latest" question.
license: MIT
---

# Web Research Skill

Use this skill when an answer depends on facts you should verify or on information newer than your training data.

## When to Use

- The user asks about recent events, releases, prices, versions, or statistics
- The user asks to compare products, libraries, vendors, or approaches
- The user asks "what is X" about something you are not certain of
- Another skill (python, aws, report-writer) tells you to verify a fact

## Supporting Files

- `instructions.md` - the search, triage, synthesis, and citation workflow
- `examples.md` - sample research tasks and well-formed outputs

## Quick Rules

1. Run at least two `internet_search` calls with different phrasings before answering a factual question.
2. Prefer primary sources: official docs, the vendor's own announcement, the paper, the standard.
3. Note the publication date of every source. Flag anything older than a year on fast-moving topics.
4. When sources disagree, say so and explain which you trust and why.
5. Cite every source you used at the end as a numbered list with title and URL.
6. Never invent a URL. If you cannot find a source, say that the claim is unverified.
