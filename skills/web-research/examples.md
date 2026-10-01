# Web Research Skill - Examples

## Example 1: Version question

**User:** What is the current stable version of Python and when does 3.11 reach end of life?

**Process:**
1. `internet_search("Python latest stable release", max_results=5)`
2. `internet_search("Python 3.11 end of life date python.org", max_results=5)`
3. Open python.org downloads page and the PEP 664 (3.11 release schedule) page.

**Good answer:**

Python 3.13 is the current stable release line as of the search date [1]. Python 3.11 receives security fixes until October 2027 [2].

Sources:
1. Python Downloads - https://www.python.org/downloads/
2. PEP 664 - Python 3.11 Release Schedule - https://peps.python.org/pep-0664/

## Example 2: Comparison

**User:** Compare SQS and Kinesis for an event pipeline.

**Process:**
1. Search for the official SQS and Kinesis Data Streams docs.
2. Search `"SQS vs Kinesis" when to use` and pick one independent article.
3. Build a table on the same criteria: ordering, retention, consumers, throughput, pricing model.

**Good answer:**

Short verdict first, then a table with one row per criterion, then sources. Every cell should trace back to a doc page.

## Example 3: Unverifiable claim

**User:** I heard AWS is shutting down CodeCommit. Is that true?

**Process:**
1. `internet_search("AWS CodeCommit deprecation announcement", topic="news")`
2. Open the AWS blog or docs page. Check the date.

**Good answer:**

Yes. AWS announced in July 2024 that CodeCommit is closed to new customers, while existing customers can continue to use it [1]. AWS recommends migrating to GitHub, GitLab, or Bitbucket and published a migration guide [2].

Sources:
1. AWS blog, "How to migrate your AWS CodeCommit repository to another Git provider" - https://aws.amazon.com/blogs/devops/how-to-migrate-your-aws-codecommit-repository-to-another-git-provider/ (July 2024)
2. AWS CodeCommit documentation - https://docs.aws.amazon.com/codecommit/

## Example 4: Nothing found

**User:** What did Acme Corp announce at their conference yesterday?

**Good answer:**

I could not find any coverage of an Acme Corp conference in the last week after three searches (general and news). Either the event has not been reported yet or the company name differs. If you can share a link or the event name, I will look again.
