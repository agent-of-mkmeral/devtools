"""Owner write allow-list enforcement for the ``use_github`` tool, wired from ``Config.github``.

These are hermetic: the only network seam is ``tools.github._graphql`` (monkeypatched), exactly
as the rest of the suite stays network-free. They assert that flipping the allow-list ON via
``Config.github`` (PR 2) actually blocks writes outside the Strands orgs while letting Strands
writes through, and that ``strict_mutations`` blocks an unverifiable mutation target.
"""

from __future__ import annotations

from typing import Any

import pytest

from strandly_harness.core.config import Config
from strandly_harness.tools import github as gh_tool
from strandly_harness.tools.github import make_use_github, validate_owner


@pytest.fixture
def gh_settings():
    """Default (env-free) Config → the hardcoded Strands-orgs allow-list."""
    return Config(values={}).github


def test_use_github_blocks_non_strands_owner(monkeypatch, gh_settings):
    monkeypatch.setenv("STRANDLY_GITHUB_TOKEN", "t")

    def _boom(*a, **k):  # the call must be blocked *before* any network I/O
        raise AssertionError("network must not be reached for a blocked owner")

    monkeypatch.setattr(gh_tool, "_graphql", _boom)

    use_github = make_use_github(gh_settings)
    res = use_github(
        query_type="mutation",
        query="mutation($id: ID!) { addComment(input: {subjectId: $id}) { clientMutationId } }",
        label="comment",
        variables={"owner": "agent-of-mkmeral", "name": "strands-coder-private"},
    )
    assert res["status"] == "error"
    assert "not in the allowed list" in res["content"][0]["text"]


def test_use_github_allows_strands_owner(monkeypatch, gh_settings):
    monkeypatch.setenv("STRANDLY_GITHUB_TOKEN", "t")
    calls: list[dict[str, Any]] = []

    def _fake_graphql(query, variables, token):
        calls.append({"query": query, "variables": variables, "token": token})
        return {"data": {"createIssue": {"issue": {"number": 1}}}}

    monkeypatch.setattr(gh_tool, "_graphql", _fake_graphql)

    use_github = make_use_github(gh_settings)
    res = use_github(
        query_type="mutation",
        query="mutation { createIssue { issue { number } } }",
        label="create issue",
        variables={"owner": "strands-agents", "name": "sdk-python"},
    )
    assert res["status"] == "success"
    assert len(calls) == 1  # the real mutation executed once


def test_validate_owner_node_id_strict_block(monkeypatch, gh_settings):
    # A mutation carrying only an opaque node id that cannot be resolved is blocked under strict
    # mode (the default) rather than silently allowed.
    monkeypatch.setattr(gh_tool, "resolve_node_owner", lambda node_id, token: None)
    err, resolved = validate_owner(
        {"subjectId": "PR_kwDOABCDEF1234567890"},
        allowed_owners=set(gh_settings.allowed_owners),
        is_mutative=True,
        strict=gh_settings.strict_mutations,
        token="t",
    )
    assert err is not None and "cannot verify" in err
    assert resolved is None


def test_validate_owner_node_id_resolves_to_blocked_owner(monkeypatch, gh_settings):
    monkeypatch.setattr(gh_tool, "resolve_node_owner", lambda node_id, token: "evilcorp")
    err, _ = validate_owner(
        {"subjectId": "PR_kwDOABCDEF1234567890"},
        allowed_owners=set(gh_settings.allowed_owners),
        is_mutative=True,
        strict=gh_settings.strict_mutations,
        token="t",
    )
    assert err is not None and "evilcorp" in err


def test_validate_owner_node_id_resolves_to_allowed_owner(monkeypatch, gh_settings):
    monkeypatch.setattr(gh_tool, "resolve_node_owner", lambda node_id, token: "strands-labs")
    err, resolved = validate_owner(
        {"subjectId": "PR_kwDOABCDEF1234567890"},
        allowed_owners=set(gh_settings.allowed_owners),
        is_mutative=True,
        strict=gh_settings.strict_mutations,
        token="t",
    )
    assert err is None
    assert resolved == "strands-labs"


# ---------------------------------------------------------------------------
# BARE-CR comment classifier bypass (round-5 remediation, PR #35 follow-up).
# A GraphQL comment ends at a bare carriage return ``\r`` (U+000D), so
# ``# x\rmutation{...}`` executes the trailing mutation on GitHub. The tool must
# classify it as a mutation and route its inline external node id through the
# owner allow-list (BLOCK), while a genuine bare-CR-prefixed read is untouched.
# ---------------------------------------------------------------------------
_BARE_CR_PREFIXES = ["# x\r", "# x\r\n", "\ufeff,# c\r "]


@pytest.mark.parametrize("prefix", _BARE_CR_PREFIXES)
def test_use_github_blocks_bare_cr_inline_external_node_poc(monkeypatch, gh_settings, prefix):
    """The round-5 PoC: bare-CR comment + inline external node id + empty vars,
    mislabelled ``query_type='query'`` — must be BLOCKED before any network I/O
    (allow-list ON = Strands orgs, strict ON = the default)."""
    monkeypatch.setenv("STRANDLY_GITHUB_TOKEN", "t")
    # resolve_node_owner: GitHub-realistic — the attacker node resolves to an external owner.
    monkeypatch.setattr(gh_tool, "resolve_node_owner", lambda node_id, token: "attacker-org")

    def _boom(*a, **k):
        raise AssertionError("network must NOT be reached — the mutation should be blocked")

    monkeypatch.setattr(gh_tool, "_graphql", _boom)

    use_github = make_use_github(gh_settings)
    q = prefix + 'mutation{ addComment(input:{subjectId:"PR_kwDOEXTattacker0123"}){clientMutationId} }'
    res = use_github(query_type="query", query=q, variables={}, label="poc")
    assert res["status"] == "error"
    assert "attacker-org" in res["content"][0]["text"]


def test_use_github_bare_cr_targetless_read_not_overblocked(monkeypatch, gh_settings):
    """A benign bare-CR-prefixed READ (no external node) is NOT over-blocked: it executes."""
    monkeypatch.setenv("STRANDLY_GITHUB_TOKEN", "t")
    monkeypatch.setattr(gh_tool, "resolve_node_owner", lambda node_id, token: "attacker-org")
    calls: list[dict[str, Any]] = []

    def _fake_graphql(query, variables, token):
        calls.append({"query": query})
        return {"data": {"viewer": {"login": "me"}}}

    monkeypatch.setattr(gh_tool, "_graphql", _fake_graphql)

    use_github = make_use_github(gh_settings)
    q = "# mutation cool\rquery{ viewer { login } }"
    res = use_github(query_type="query", query=q, variables={}, label="benign-read")
    assert res["status"] == "success"
    assert len(calls) == 1  # the read executed, not over-blocked
