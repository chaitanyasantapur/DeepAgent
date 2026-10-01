# Web Research Skill - Instructions

## Workflow

1. **Frame the question**
   - Write down (mentally) the exact claim or set of facts you need.
   - Split broad questions into 2-4 sub-questions.

2. **Search**
   - Call `internet_search(query, max_results=5, topic="general")`.
   - Use `topic="news"` for events of the last few weeks and `topic="finance"` for market or company data.
   - Vary phrasing: official product name, common abbreviation, "vs" for comparisons, "release notes" or "changelog" for versions.
   - Set `include_raw_content=True` only when a snippet is clearly insufficient; it is expensive in context.

3. **Triage results**
   - Rank by source type: official docs or announcement > reputable publication > well-known blog > forum post.
   - Discard SEO content farms and pages without a date or author.
   - Open at most the top 3 per sub-question.

4. **Cross-check**
   - Every key number, date, or claim should appear in two independent sources, or be marked as single-source.
   - If sources conflict, prefer the newer primary source and note the conflict.

5. **Synthesize**
   - Lead with the direct answer in one or two sentences.
   - Follow with supporting detail grouped by sub-question.
   - Keep the body under 200 words unless the user asked for a full report.

6. **Cite**
   - End with a `Sources` section: numbered list, `Title - URL (date if known)`.
   - Reference sources inline with `[1]`, `[2]` where a specific claim needs it.

## Quality Bar

- No claim without a source or an explicit "unverified" label.
- Dates are absolute (e.g. "March 2026"), never "recently" or "last month".
- Numbers include units and the as-of date.
- Comparisons use the same criteria for every option.

## Common Pitfalls

- Trusting a single snippet without opening the page.
- Mixing up similarly named products or versions.
- Reporting a preview or beta feature as generally available.
- Using marketing claims as facts. Look for independent confirmation.
