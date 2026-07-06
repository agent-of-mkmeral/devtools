"""Sandbox selection — opinionated: AgentCore Code Interpreter if configured, else local.

The same ``strands.sandbox.Sandbox`` is injected into every file/exec tool, so all execution and
file access share one isolation boundary. ``local`` is named ``NotASandbox...`` upstream so "no
isolation" is never silent. ``agentcore`` is used only when ``AGENTCORE_CODE_INTERPRETER_ID`` is
configured (needs the ``agentcore`` extra) and shares the harness's AWS region.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from strandly_harness.core.config import Config

if TYPE_CHECKING:
    from strands.sandbox.base import Sandbox


def build_sandbox(config: Config) -> Sandbox:
    if config.use_agentcore_sandbox:
        from strandly_harness.sandbox.agentcore import (
            DEFAULT_IDENTIFIER,
            AgentCoreSandbox,
        )

        return AgentCoreSandbox(
            region=config.aws_region,
            identifier=config.code_interpreter_id or DEFAULT_IDENTIFIER,
        )
    from strands.sandbox.not_a_sandbox_local_environment import NotASandboxLocalEnvironment

    return NotASandboxLocalEnvironment()


__all__ = ["build_sandbox"]
