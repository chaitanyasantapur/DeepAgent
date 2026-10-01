# Report Writer Skill - Examples

## Example 1: Research question

User asked: "What is the current stable version of Python?"

File written: `/workspace/reports/2026-10-01-current-stable-python-version.md`

```markdown
# Report: Current stable Python version

- **Date:** 2026-10-01
- **Question:** What is the current stable version of Python?
- **Skills consulted:** web-research, report-writer

## Summary

Python 3.13 is the current stable release line; 3.14 is in pre-release.

## Answer

Python 3.13 is the latest stable release series as of October 2026 [1]. Python 3.14 is available as a release candidate and is scheduled for final release in October 2026 [2].

Sources:
1. Python Downloads - https://www.python.org/downloads/
2. PEP 745 - Python 3.14 Release Schedule - https://peps.python.org/pep-0745/

## Method

- Read /skills/web-research/SKILL.md
- internet_search("Python latest stable release")
- internet_search("Python 3.14 release schedule PEP")
- Read /skills/report-writer/SKILL.md and template.md

## Tools Used

- read_file x3
- internet_search x2
- write_file x1

## Sources

1. Python Downloads - https://www.python.org/downloads/
2. PEP 745 - Python 3.14 Release Schedule - https://peps.python.org/pep-0745/

## Confidence

High - both facts come from python.org primary sources dated within the last month.

## Open Questions

- None
```

Reply to the user ended with: `Report saved to /workspace/reports/2026-10-01-current-stable-python-version.md`

## Example 2: Code task with no searching

User asked: "Write a Python function that reverses the words in a sentence."

File written: `/workspace/reports/2026-10-01-reverse-words-python-function.md`

```markdown
# Report: Reverse words in a sentence (Python)

- **Date:** 2026-10-01
- **Question:** Write a Python function that reverses the words in a sentence.
- **Skills consulted:** python, report-writer

## Summary

Provided a one-line function using split and join, plus a pytest test.

## Answer

```python
def reverse_words(sentence: str) -> str:
    return " ".join(reversed(sentence.split()))
```

```python
def test_reverse_words() -> None:
    assert reverse_words("hello big world") == "world big hello"
```

Multiple spaces collapse to one because `split()` with no argument drops empty fields.

## Method

- Read /skills/python/SKILL.md
- Wrote the function and a test following the python skill standards

## Tools Used

- read_file x2
- write_file x1

## Sources

None (answered from prior knowledge)

## Confidence

High - standard library behaviour, no external facts involved.

## Open Questions

- Should punctuation stay attached to words? Current version keeps it attached.
```

## Example 3: Short conversational answer

User asked: "Thanks, that's all for now."

File written: `/workspace/reports/2026-10-01-conversation-closed.md`

```markdown
# Report: Conversation closed

- **Date:** 2026-10-01
- **Question:** Thanks, that's all for now.
- **Skills consulted:** report-writer

## Summary

User ended the session. No task performed.

## Answer

You're welcome. The reports from this session are in /workspace/reports/.

## Method

- None

## Tools Used

- write_file x1

## Sources

None (answered from prior knowledge)

## Confidence

High - no factual content.

## Open Questions

- None
```
