---
name: first-response
description: >
  First response to a freshly-filed issue/ticket: reproduce it, find duplicates, decide where it
  belongs, and prepare the ticket + a draft reply. TRIGGER when handling an incoming bug report or
  issue ("triage this issue", "is this a dup", "can you repro this", "first response"). SKIP for
  changes already understood/scoped. Disposition: needs-info / confirmed-bug / duplicate /
  wrong-repo / works-as-intended / escalate.
allowed-tools: bash file_editor use_github think spawn
---

# First Response

Use this to get an incoming issue maintainer-ready: reproduce → find duplicates → assess
disposition → prepare the ticket → draft a reply. More action-oriented than `triage` (which only
judges go/no-go): this one actually reproduces and prepares the ticket.

## How to run it

Spawn a subagent with the first-responder role prompt:

```
spawn(
  prompt="First-response triage for <issue link / the report text>. <repo context, repro steps "
         "given>.",
  system_prompt="skills/first-response/assets/roles/first-responder.md",
)
```

The subagent inherits the harness toolset (there is no `tools=` argument on `spawn`): `bash` to
reproduce in the sandbox, `use_github` to search duplicates/related and read issue context.
Reproduction is mandatory for bug reports — it runs the report, it doesn't speculate. Keep the
default model tier — disposition calls (duplicate vs. new, bug vs. works-as-intended) gate what a
maintainer sees next.

## What you get back

A prepared ticket (summary, repro status with output, suspected area, duplicates/related links), a
recommended **disposition**, and a draft first-response comment ready for a maintainer to post (it
drafts; it does not post unless you tell it to).
