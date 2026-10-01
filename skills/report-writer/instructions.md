# Report Writer Skill - Instructions

## Steps

1. **Finish the answer first.** Do all research, run all other skills, and compose the final answer text before writing the report.

2. **Build the file name.**
   - Date: take the `YYYY-MM-DD` value from the "Today's date" line in the system prompt. If it is absent, use `undated`.
   - Slug: lowercase, 3-6 meaningful words from the user's question, hyphen-separated, no punctuation. Example: "How do I set up a Lambda in a VPC?" -> `lambda-in-vpc-setup`.
   - Path: `/workspace/reports/<date>-<slug>.md`.
   - If `ls /workspace/reports/` shows the name already exists, append `-2`, `-3`, and so on.

3. **Read `template.md`** (same directory as this file) and fill it in. Section rules:

   | Section | Content |
   |---|---|
   | Title | `# Report: <short title>` |
   | Metadata | Date, the exact user question, and the list of skills consulted |
   | Summary | 1-3 sentences. The answer a busy reader needs. |
   | Answer | The full answer you are giving the user, verbatim. Keep markdown formatting. |
   | Method | Bullet list of what you did: searches run (with queries), files read, skills followed, subagents used. |
   | Tools Used | One bullet per tool name with a count, e.g. `internet_search x3`, `read_file x2`. |
   | Sources | Numbered list `Title - URL`. "None (answered from prior knowledge)" if no searches. |
   | Confidence | High / Medium / Low with one sentence on why. |
   | Open Questions | Anything unverified, assumptions made, or sensible follow-ups. "None" if nothing. |

4. **Save** with `write_file(file_path="/workspace/reports/<date>-<slug>.md", content=<report>)`.

5. **Tell the user** by ending your reply with the line `Report saved to /workspace/reports/<date>-<slug>.md`.

## Style

- Plain markdown, no HTML.
- Headings exactly as in the template so reports can be parsed later.
- Dates absolute, numbers with units.
- Do not include secrets, API keys, or personal data in the report.

## Failure Handling

- If `write_file` fails, retry once with the same path. If it fails again, include the full report inline in your reply under a `## Report` heading and say that saving failed.
- If `/workspace/reports/` does not exist, `write_file` creates it. Do not try to create directories separately.
