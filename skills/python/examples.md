# Python Skill - Examples

## Example 1: Small script request

**User:** Write a script that reads a CSV of orders and prints total revenue per customer.

**Good answer:**

```python
"""Sum order revenue per customer from a CSV file."""

import csv
import sys
from collections import defaultdict
from pathlib import Path


def revenue_per_customer(csv_path: Path) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            totals[row["customer"]] += float(row["amount"])
    return dict(totals)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run revenue.py orders.csv")
    for customer, total in sorted(revenue_per_customer(Path(sys.argv[1])).items()):
        print(f"{customer}: {total:.2f}")


if __name__ == "__main__":
    main()
```

Expects columns `customer` and `amount`. Run with `uv run revenue.py orders.csv`.

```python
# test_revenue.py
from pathlib import Path
from revenue import revenue_per_customer

def test_sums_per_customer(tmp_path: Path) -> None:
    p = tmp_path / "orders.csv"
    p.write_text("customer,amount\nann,10\nbob,5\nann,2.5\n")
    assert revenue_per_customer(p) == {"ann": 12.5, "bob": 5.0}
```

## Example 2: Bug fix from a traceback

**User:**
```
TypeError: unsupported operand type(s) for +: 'int' and 'str'
    total += row["amount"]
```

**Good answer:**

Root cause: `csv.DictReader` returns every field as a string, so `row["amount"]` is `"10"` not `10`.

Fix: convert before adding.

```python
total += float(row["amount"])
```

If some rows may be blank, guard it: `float(row["amount"] or 0)`.

## Example 3: Async fan-out

**User:** Fetch 50 URLs concurrently and return the status codes.

**Good answer:**

```python
import asyncio
import httpx


async def fetch_statuses(urls: list[str], limit: int = 10) -> dict[str, int]:
    sem = asyncio.Semaphore(limit)
    results: dict[str, int] = {}

    async def one(client: httpx.AsyncClient, url: str) -> None:
        async with sem:
            try:
                r = await client.get(url, timeout=10)
                results[url] = r.status_code
            except httpx.HTTPError:
                results[url] = -1

    async with httpx.AsyncClient() as client, asyncio.TaskGroup() as tg:
        for url in urls:
            tg.create_task(one(client, url))
    return results


if __name__ == "__main__":
    print(asyncio.run(fetch_statuses(["https://example.com"])))
```

Add the dependency with `uv add httpx`. The semaphore caps concurrency at 10 so you do not get rate limited.

## Example 4: Code review

**User:** Review this.

```python
def load(path, cache={}):
    if path in cache: return cache[path]
    data = eval(open(path).read())
    cache[path] = data
    return data
```

**Good answer:**

- **Security (high):** `eval` on file contents executes arbitrary code. Use `json.loads` or `ast.literal_eval`.
- **Bug:** `cache={}` is a mutable default shared across all calls. Use `functools.lru_cache` or pass the cache explicitly.
- **Resource leak:** `open(path)` is never closed. Use `Path(path).read_text(encoding="utf-8")`.
- **Style:** add type hints and split the one-line `if`.

```python
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=128)
def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
```

## Example 5: Explanation question

**User:** When should I use a dataclass vs a TypedDict?

**Good answer:**

Use a `dataclass` when you want a real object: methods, defaults, `__eq__`, immutability via `frozen=True`. Use a `TypedDict` when the data must stay a plain `dict`, for example JSON you pass straight through or LangGraph state. Rule of thumb: internal domain models are dataclasses; wire formats and state schemas are TypedDicts.
