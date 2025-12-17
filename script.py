#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "click",
#   "dycw-utilities",
#   "pytest-xdist",
#   "typed-settings[attrs, click]",
# ]
# ///
from __future__ import annotations

from logging import getLogger

from click import command
from typed_settings import click_options, option, settings
from utilities.click import CONTEXT_SETTINGS_HELP_OPTION_NAMES
from utilities.logging import basic_config

_LOGGER = getLogger(__name__)


@settings
class Settings:
    dry_run: bool = option(default=False, help="Dry run the CLI")


@command(**CONTEXT_SETTINGS_HELP_OPTION_NAMES)
@click_options(Settings, "app", show_envvars_in_help=True)
def main(settings: Settings, /) -> None:
    if settings.dry_run:
        _LOGGER.info("Dry run; exiting...")
        return
    _LOGGER.info("Running...")


if __name__ == "__main__":
    basic_config(obj=__name__)
    main()
