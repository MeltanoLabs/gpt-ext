"""Passthrough shim for OpenAI extension."""
import sys

import structlog
from meltano.edk.logging import pass_through_logging_config
from openai_ext.extension import OpenAI


def pass_through_cli() -> None:
    """Pass through CLI entry point."""
    pass_through_logging_config()
    ext = OpenAI()
    ext.pass_through_invoker(
        structlog.getLogger("openai_invoker"),
        *sys.argv[1:] if len(sys.argv) > 1 else []
    )
