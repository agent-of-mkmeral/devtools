# Goals: first-response

Critic acceptance criteria when the `first-response` skill is active — getting an incoming issue
maintainer-ready.

- **A disposition is present:** one of `needs-info` / `confirmed-bug` / `duplicate` / `wrong-repo` /
  `works-as-intended` / `escalate`.
- **Reproduction was attempted for any bug report**, in the sandbox, with the actual output shown —
  not speculated. For a `confirmed-bug` disposition, the repro evidence must exist; re-run or inspect
  it. (`needs-info` is acceptable when the report genuinely lacks repro steps.)
- **A duplicate / related search was done** (e.g. via `use_github`) and links are included, OR the
  absence of duplicates is stated.
- **A prepared ticket is present**: summary, repro status with output, suspected area, and
  duplicate/related links.
- **A draft first-response comment was produced**, ready for a maintainer.
- **Nothing was posted to GitHub unless the user explicitly asked.** The skill drafts; it does not
  post on its own. A self-initiated public comment is a gap.
