"""Meltano OpenAI extension."""
from __future__ import annotations

import os
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import structlog
from meltano.edk import models
from meltano.edk.extension import ExtensionBase
from meltano.edk.process import Invoker, log_subprocess_error

log = structlog.get_logger()


class OpenAI(ExtensionBase):
    """Extension implementing the ExtensionBase interface."""

    def __init__(self) -> None:
        """Initialize the extension."""
        self.openai_bin = "OpenAI"  # verify this is the correct name
        self.openai_invoker = Invoker(self.openai_bin)

    # def invoke(self, command_name: str | None, *command_args: Any) -> None:
    #     """Invoke the underlying cli, that is being wrapped by this extension.

    #     Args:
    #         command_name: The name of the command to invoke.
    #         command_args: The arguments to pass to the command.
    #     """
    #     try:
    #         self.openai_invoker.run_and_log(command_name, *command_args)
    #     except subprocess.CalledProcessError as err:
    #         log_subprocess_error(
    #             f"openai {command_name}", err, "OpenAI invocation failed"
    #         )
    #         sys.exit(err.returncode)

    def describe(self) -> models.Describe:
        """Describe the extension.

        Returns:
            The extension description
        """
        # TODO: could we auto-generate all or portions of this from typer instead?
        return models.Describe(
            commands=[
                models.ExtensionCommand(
                    name="openai_extension", description="extension commands"
                ),
                models.InvokerCommand(
                    name="openai_invoker", description="pass through invoker"
                ),
            ]
        )
