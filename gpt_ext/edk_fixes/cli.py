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


class CLI(typer.Typer):
    """The CLI for the extension."""

    edk_commands: t.Dict[str, tuple[t.Callable, list, dict]] = {}
    name = "Something"  # TODO: Fix me

    @classmethod
    @property
    def app(cls) -> typer.Typer:
        """The Typer app for the extension."""
        if not hasattr(cls, "_app"):
            cls._app = cls(
                name=cls.name,
                pretty_exceptions_enable=False,
            )
        return cls._app

    @classmethod
    def command(
        cls,
        *args: t.Any,
        allow_extra_args: bool | None = None,
        context_settings: dict | None = None,
        **kwargs: t.Any,
    ) -> t.Callable:
        """Decorator to register a command with the extension.

        Args:
            name: The name of the command.

        Returns:
            The decorator.
        """
        name: None | str = None
        if "name" in kwargs:
            name = kwargs.pop("name")

        if allow_extra_args is not None:
            context_settings = context_settings or {}
            context_settings["allow_extra_args"] = True

        if context_settings:
            kwargs["context_settings"] = context_settings

        def decorator(func: t.Callable) -> t.Callable:
            cls.edk_commands[name or func.__name__] = func, args, kwargs

        return decorator

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Initialize the CLI."""
        unsupported_commands = kwargs.pop("unsupported_commands", [])
        super().__init__(*args, **kwargs)
        for cmd in unsupported_commands:
            self.edk_commands.pop(cmd, None)

        for name, func_def in self.edk_commands.items():
            func, func_args, func_kwargs = func_def
            super().command(name, *func_args, **func_kwargs)(func)
