"""Add a second batch of professional articles to the existing blog.db.

This is idempotent: articles whose slug already exists are skipped, so it is
safe to run repeatedly. Run:

    source .venv/bin/activate
    python scripts/seed_extra.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import init_schema  # noqa: E402
from models import create_article, get_article_by_slug  # noqa: E402
from slug import slugify  # noqa: E402

DB = str(ROOT / "blog.db")

EXTRA = [
    {
        "title": "Rate-Limiting Public APIs Without a Dedicated Service",
        "tags": ["apis", "performance"],
        "body": """Every public API eventually asks the same question: how do I protect a
resource from its own popularity? Rate limiting is the most direct answer, and
it does not require a dedicated service to do well.

## The sliding concern

Rate limiting protects a shared resource while staying simple for clients. A
token-bucket or sliding-window counter tracks how many requests a client may
make per interval:

```python
requests = cache.incr(f"rl:{client_id}")
if requests > 100:
    return 429 Too Many Requests
```

The key insight is that limits are experienced by clients, so the scheme must
be documented and expressed in standard headers:

```
RateLimit-Limit: 100
RateLimit-Remaining: 87
RateLimit-Reset: 60
```

Clients read those headers and back off in the way you specify, turning a
free-for-all into a cooperative protocol.

## Scope the key correctly

A limit keyed only by IP punishes people behind shared egress. Prefer
authenticated keys when possible — API token, user id — and fall back to IP
only as a floor. Look at real traffic before choosing intervals.

## The boring part wins

Run the counter in the store you already have, keep expiry short so counters
do not pile up, and respond with a clear 429 and a retry-after header rather
than a silent failure. The best rate limiter is one nobody notices. A rule
that is undocumented or inconsistent drives more support tickets than it
prevents.
"""
    },
    {
        "title": "Docker Compose for Local Development",
        "tags": ["docker", "devops"],
        "body": """When a project becomes multi-service, `docker compose up` establishes a
shared development environment in one command. It is worth adopting with an
accurate mental model of what it does and does not do.

## What Compose gives you

Compose declares services, networks, and volumes in a single file:

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
  db:
    image: postgres:16
```

One command brings the whole topology online with a shared network and named
volumes that survive container restarts.

## Compose for dependencies, not necessarily for your runtime

Running your entire app in a container is fine for demos, but for daily work a
two-arrangement with the database in a container and the app on the host keeps
iteration fast while still isolating the heavy dependencies.

## The discipline that keeps teams sane

- Pin image versions.
- Keep the compose file in version control.
- Add healthchecks so `depends_on` waits for a ready service.
- Document how to tear a stale state down with `compose down`.

Containers package your assumptions. Compose is valuable precisely because it
makes those assumptions reviewable and reproducible across a team.
"""
    },
    {
        "title": "SQL JOINs: A Mental Model That Sticks",
        "tags": ["sql", "databases"],
        "body": """Most developers fear joins because they memorise syntax before they adopt a
model. The model is small: a join pairs rows from two sets, and the join kind
decides what happens when nothing matches.

## The four kinds

- `INNER` — keep only matches found on both sides.
- `LEFT` — keep all left rows, filling nulls where there is no match.
- `RIGHT` — the mirror that most engines implement.
- `FULL OUTER` — keep everything, null where either side is missing.

## Fan-out is the real bug

Most join errors are not a wrong key; they are *duplication*. A one-to-many
query returns one row per match, so one article with three tags produces three
rows. Aggregating those rows double-counts unless you are careful:

```sql
SELECT a.id, COUNT(at.tag_id) AS tags
FROM articles a
LEFT JOIN article_tags at ON at.article_id = a.id
GROUP BY a.id;
```

## Read the model, not the reference

Index the columns you join, keep queries legible, and choose between `JOIN` and
`LEFT JOIN` deliberately to state intent. SQL is declarative; a solid mental
model is what keeps an expression truthful and a query sane.
"""
    },
    {
        "title": "Async in Python: When to Reach for asyncio",
        "tags": ["python", "performance"],
        "body": """Python offers threads, processes, and async as ways to juggle work, and
choosing wrongly costs more than not choosing at all.

## The decision rule

**I/O-bound** (waiting on sockets, files, databases) — use async or threads.
**CPU-bound** (computing numbers) — use processes or native code. Async is
efficient precisely when the program is mostly waiting.

```python
import asyncio

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.text()
```

## Async is not faster; it is smaller

Async interleaves work during waits with an event loop. It does not run two
pieces on different cores. If your workload is CPU-bound, async and threads will
both churn on the same processors — reach for processes.

## Two practical rules

1. Keep the event loop at your program's entry point; do not scatter it.
2. When unsure, prefer the simplest primitive. Reach for threads and a bounded
   pool until latency or concurrency demand a loop.

Async shines for network fan-out — crawling, proxying, aggregation. It fails
the moment a single core becomes the bottleneck. Match the tool to the
workload, not to fashion.
"""
    },
    {
        "title": "Keyboard and Focus: An Accessibility Floor People Notice",
        "tags": ["accessibility", "frontend"],
        "body": """Many teams treat accessibility as a final checkbox. The most valuable
discipline is cheaper and earlier: make the whole product usable by keyboard.
Every interactive element must be reachable, operable, and visibly focused.

## Three facts that cover it

- **Order** — Tab traces a logical path through the page.
- **Visibility** — a focus ring shows where you are.
- **Activation** — Enter or Space triggers the same action as a click.

```css
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
```

## Semantics before styling

Use a real `<button>` for buttons and a real `<a>` for links; form a label.
Native semantics bring keyboard support for you; replacing them with `div`s is
how the keyboard tree is lost entirely.

## Test it fairly often

Walk the product with only Tab, Shift+Tab, Enter, and Space. If anything cannot
be done this way, that is a bug. Accessibility is the difference between
software you can only click and software people can actually use.
"""
    },
    {
        "title": "Semantic Versioning and Changelogs People Actually Read",
        "tags": ["git", "engineering"],
        "body": """A version number is a promise. `1.4.2` says the API should keep working, and
the discipline behind that promise begins with a changelog that readers want.

## The shape of a good number

- **MAJOR** — breaking changes.
- **MINOR** — features with backward compatibility.
- **PATCH** — backward-compatible fixes.

```
2.0.0   breaking: removed legacy /v1 endpoint
1.4.0   added: filter search by tag
1.4.1   fixed: crash on empty excerpt
```

## Write for the reader, not the log

A changelog is communication, not a dump of commit messages. Group by
intent, link to the issue or PR, and describe the user-facing effect. Skip
opaque references to tickets.

## Value beyond the label

Clear versions let consumers upgrade predictably and give your releases a
shared vocabulary. When the world re-sorts your abstractions, a consistent
name and a readable changelog keep the promise evident.
"""
    },
    {
        "title": "Data Sanitization: A Boundary Model",
        "tags": ["security", "python"],
        "body": """Input you accept is input you will sometimes render. Sanitisation is not one
call at the edge; it is a boundary you maintain about what a value may reach.

## Trust zones

Define what is untrusted: anything that originates with a user — form fields,
headers, uploads, external APIs. Every boundary between the trusted and the
untrusted is where you validate or escape.

## Escape where you emit

Keep the original value intact and escape exactly where it is rendered:

- HTML output: escape or allowlist-sanitise.
- SQL: use parameters, never concatenation.
- URLs: percent-encode when interpolated.
- Logs: strip secrets before they reach the file.

## The common error

Do not double-escape; do not decode-and-resanitise. Decide a policy at each
boundary and apply it consistently. A small, stable policy prevents both
injection and the brittle over-encoding that makes a product fragile.

Sanitisation is the quietest security. The best version is the one no one
notices, because every boundary behaves correctly exactly where it meets the
outside world.
"""
    },
]


def main() -> None:
    init_schema(DB)
    added, skipped = 0, 0
    for item in EXTRA:
        slug = slugify(item["title"])
        if get_article_by_slug(slug, db_path=DB) is not None:
            skipped += 1
            continue
        excerpt = _first_paragraph(item["body"])
        create_article(item["title"], slug, item["body"], excerpt, item["tags"],
                       db_path=DB)
        added += 1
    print(f"Added {added} article(s); skipped {skipped} existing.")


def _first_paragraph(markdown: str) -> str:
    for line in markdown.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            return line[:160]
    return ""


if __name__ == "__main__":
    main()