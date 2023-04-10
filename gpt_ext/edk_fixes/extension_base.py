import os
import sys
import typing as t

import structlog
import typer
import yaml
from devtools.prettier import pformat
from meltano.edk import models
from meltano.edk.extension import DescribeFormat
from meltano.edk.extension import ExtensionBase as _ExtensionBase
from meltano.edk.logging import (
    default_logging_config,
    parse_log_level,
    pass_through_logging_config,
)

from gpt_ext.edk_fixes.cli import CLI


class ExtensionBase(_ExtensionBase):
    """Refactored ExtensionBase class."""

    wrapped_exe: None | str = None
    supports_init_command = False
    supports_invoke_command = False

    def __init__(self) -> None:
        super().__init__()

        # Change the default logging config:
        pass_through_logging_config()
        self.passthrough_logger = structlog.getLogger("openai_invoker")

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get the logger for the extension.

        Returns:
            The logger.
        """
        return structlog.get_logger(self.name)

    @classmethod
    @property
    def name(cls) -> str:
        return cls.__name__

    @CLI.command()
    @staticmethod
    def init(
        ctx: typer.Context,
        force: bool = typer.Option(False, help="Force initialization (if supported)"),
    ) -> None:
        """Initialize the OpenAI plugin."""
        print("Hello")
        try:
            ctx.obj.initialize(force)
            ctx.obj.logger.info("initialized")
        except Exception:
            ctx.obj.logger.exception(
                "initialize failed with uncaught exception, please report to maintainer"
            )
            sys.exit(1)

    # @classmethod
    # @property
    # def commands(cls) -> t.List[models.ExtensionCommand]:
    #     """Get the commands for this extension.
    #
    #     Returns:
    #         The list of extension commands.
    #     """
    #     result = [
    #         models.ExtensionCommand(
    #             name="openai_extension", description="extension commands"
    #         ),
    #         models.InvokerCommand(
    #             name="openai_invoker", description="pass through invoker"
    #         ),
    #     ]
    #     if cls.wrapped_exe:
    #         result.append(
    #             models.InvokerCommand(
    #                 name="openai_invoker", description="pass through invoker"
    #             ),
    #         )
    #     return result

    @t.final
    @property
    def description(self) -> models.Describe:
        """Describe the extension.

        Returns:
            The extension description
        """
        return models.Describe(commands=self.edk_commands)

    def describe_formatted(  # type: ignore[return]
        self, output_format: DescribeFormat = DescribeFormat.text
    ) -> str:
        """Return a formatted description of the extensions commands and capabilities.

        Args:
            output_format: The output format to use.

        Returns:
            str: The formatted description.
        """
        if output_format == DescribeFormat.text:
            return pformat(self.description)
        elif output_format == DescribeFormat.json:
            return self.description.json(indent=2)
        elif output_format == DescribeFormat.yaml:
            # just calling description.dict() and dumping that to yaml yields a yaml that
            # is subtly different to the json variant in that it you have an additional
            # level of nesting.
            return yaml.dump(
                yaml.safe_load(self.description.json()), sort_keys=False, indent=2
            )

    @CLI.command()
    @staticmethod
    def describe(
        ctx: typer.Context,
        output_format: DescribeFormat = typer.Option(
            DescribeFormat.text, "--format", help="Output format"
        ),
    ) -> None:
        """Describe the available commands of this extension."""
        ext = ctx.obj
        try:
            typer.echo(ext.describe_formatted(output_format))
        except Exception:
            ext.logger.exception(
                "describe failed with uncaught exception, please report to maintainer"
            )
            sys.exit(1)

    @classmethod
    def cli(cls) -> typer.Typer:
        """Get the typer app for this extension.

        Returns:
            The typer app.
        """

        def main(
            ctx: typer.Context,
            log_level: str = typer.Option("INFO", envvar="LOG_LEVEL"),
            log_timestamps: bool = typer.Option(
                False, envvar="LOG_TIMESTAMPS", help="Show timestamp in logs"
            ),
            log_levels: bool = typer.Option(
                False, "--log-levels", envvar="LOG_LEVELS", help="Show log levels"
            ),
            meltano_log_json: bool = typer.Option(
                False,
                "--meltano-log-json",
                envvar="MELTANO_LOG_JSON",
                help="Log in the meltano JSON log format",
            ),
        ) -> None:
            """Simple Meltano extension that wraps the OpenAI CLI."""
            default_logging_config(
                level=parse_log_level(log_level),
                timestamps=log_timestamps,
                levels=log_levels,
                json_format=meltano_log_json,
            )

        extension = cls()

        unsupported_commands: list[str] = []
        if not extension.supports_init_command:
            unsupported_commands.append("init")

        if not extension.supports_invoke_command:
            unsupported_commands.append("invoke")

        cli = CLI(
            callback=main,
            context_settings={"obj": extension},
            unsupported_commands=unsupported_commands,
        )

        return cli

    @CLI.command(allow_extra_args=True)
    @staticmethod
    def invoke(ctx: typer.Context, *command_args: list[str]) -> None:
        """Invoke the underlying cli, that is being wrapped by this extension.

        Note: that if a command argument is a list, such as command_args,
        then unknown options are also included in the list and NOT stored in the
        context as usual.

        Args:
            command_name: The name of the command to invoke.
            command_args: The arguments to pass to the command.
        """
        ext = ctx.obj
        command_name, command_args = command_args[0], command_args[1:]
        ext.logger.debug(
            "called",
            command_name=command_name,
            command_args=command_args,
            env=os.environ,
        )
        pass_through_logging_config()
        ext.pass_through_invoker(
            structlog.getLogger("openai_invoker"),
            *sys.argv[1:] if len(sys.argv) > 1 else [],
        )
