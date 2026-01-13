#!/usr/bin/env -S uv run --script --prerelease=disallow
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "click>=8.3.1, <9",
#   "dycw-actions>=0.12.0,<1",
#   "dycw-utilities>=0.179.4, <1",
#   "rich>=14.2.0, <15",
#   "typed-settings[attrs,click]>=25.3.0, <26",
#
#   "pyright>=1.1.408, <2",
#   "pytest-xdist>=3.8.0, <4",
# ]
# ///
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import actions.logging
from actions.constants import PYPROJECT_TOML
from actions.pre_commit.conformalize_repo.lib import (
    add_ci_pull_request_yaml,
    add_ci_push_yaml,
)
from actions.pre_commit.utilities import (
    ensure_aot_contains,
    get_aot,
    get_table,
    yield_toml_doc,
)
from actions.utilities import LOADER
from click import command
from rich.pretty import pretty_repr
from tomlkit import table
from typed_settings import Secret, click_options, load_settings, option, settings
from utilities.click import CONTEXT_SETTINGS
from utilities.logging import basic_config
from utilities.os import is_pytest
from utilities.text import strip_and_dedent

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path

    from tomlkit.items import Table


__version__ = "0.2.11"
LOGGER = getLogger(__name__)
API_PACKAGES_QRT_PYPI = "api/packages/qrt/pypi"
ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105
PYPI_GITEA_USERNAME = "qrt-bot"
PYPI_GITEA_READ_TOKEN = "e43d1df41a3ecf96e4adbaf04e98cfaf094d253e"  # noqa: S105
PYPI_GITEA_READ_WRITE_TOKEN = "${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}"  # noqa: S105
PYPI_NANODE_USERNAME = "qrt"
PYPI_NANODE_PASSWORD = "${{secrets.PYPI_NANODE_PASSWORD}}"  # noqa: S105
SOPS_AGE_KEY = "${{secrets.SOPS_AGE_KEY}}"


@settings
class Settings:
    ci__pull_request__pre_commit: bool = option(
        default=False, help="Set up 'pull-request.yaml' pre-commit"
    )
    ci__pull_request__pre_commit__submodules: str | None = option(
        default=None, help="Set up CI 'pull-request.yaml' pre-commit with submodules"
    )
    ci__pull_request__pyright: bool = option(
        default=False, help="Set up 'pull-request.yaml' pyright"
    )
    ci__pull_request__pytest: bool = option(
        default=False, help="Set up 'pull-request.yaml' pytest"
    )
    ci__pull_request__pytest__all_versions: bool = option(
        default=False,
        help="Set up 'pull-request.yaml' pytest with the current version only",
    )
    ci__pull_request__pytest__sops_and_age: bool = option(
        default=False, help="Set up 'pull-request.yaml' pytest sops/age"
    )
    ci__pull_request__ruff: bool = option(
        default=False, help="Set up 'pull-request.yaml' ruff"
    )
    ci__push__pypi__gitea: bool = option(
        default=False, help="Set up 'push.yaml' with 'pypi-gitea'"
    )
    ci__push__pypi__nanode: bool = option(
        default=False, help="Set up 'push.yaml' with 'pypi-nanode'"
    )
    ci__push__tag: bool = option(default=False, help="Set up 'push.yaml' tagging")
    gitea_host: str = option(default="gitea.main", help="Gitea host")
    gitea_port: int = option(default=3000, help="Gitea port")
    pyproject: bool = option(default=False, help="Set up 'pyproject.toml'")
    pytest__timeout: int | None = option(
        default=None, help="Set up 'pytest.toml' timeout"
    )
    python_version: str = option(default="3.13", help="Python version")
    repo_name: str | None = option(default=None, help="Repo name")
    script: str | None = option(
        default=None, help="Set up a script instead of a package"
    )


SETTINGS = load_settings(Settings, [LOADER])


##


@command(**CONTEXT_SETTINGS)
@click_options(Settings, [LOADER], show_envvars_in_help=True)
def main(settings: Settings, /) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    basic_config(obj=actions.logging.LOGGER)
    LOGGER.info(
        strip_and_dedent("""
            Running 'conformalize' (version %s) with settings:
            %s
        """),
        __version__,
        pretty_repr(settings),
    )
    modifications: set[Path] = set()
    if (
        settings.ci__pull_request__pre_commit
        or settings.ci__pull_request__pyright
        or settings.ci__pull_request__pytest
        or settings.ci__pull_request__ruff
    ):
        add_ci_pull_request_yaml(
            gitea=True,
            modifications=modifications,
            certificates=True,
            pre_commit=settings.ci__pull_request__pre_commit,
            pre_commit__submodules=settings.ci__pull_request__pre_commit__submodules,
            pyright=settings.ci__pull_request__pyright,
            pytest__ubuntu=settings.ci__pull_request__pytest,
            pytest__all_versions=settings.ci__pull_request__pytest__all_versions,
            pytest__sops_age_key=Secret(SOPS_AGE_KEY)
            if settings.ci__pull_request__pytest__sops_and_age
            else None,
            pytest__timeout=settings.pytest__timeout,
            python_version=settings.python_version,
            repo_name=settings.repo_name,
            ruff=settings.ci__pull_request__ruff,
            script=settings.script,
            token_github=Secret(ACTION_TOKEN),
            uv__native_tls=True,
        )
    if (
        settings.ci__push__pypi__gitea
        or settings.ci__push__pypi__nanode
        or settings.ci__push__tag
    ):
        add_ci_push_yaml(
            gitea=True,
            modifications=modifications,
            certificates=True,
            publish__primary=settings.ci__push__pypi__gitea,
            publish__primary__job_name="gitea",
            publish__primary__username=PYPI_GITEA_USERNAME,
            publish__primary__password=Secret(PYPI_GITEA_READ_WRITE_TOKEN),
            publish__primary__publish_url=f"https://{settings.gitea_host}:{settings.gitea_port}/{API_PACKAGES_QRT_PYPI}",
            publish__secondary=settings.ci__push__pypi__nanode,
            publish__secondary__job_name="nanode",
            publish__secondary__username=PYPI_NANODE_USERNAME,
            publish__secondary__password=Secret(PYPI_NANODE_PASSWORD),
            publish__secondary__publish_url="https://pypi.queensberryresearch.com",
            tag=settings.ci__push__tag,
            token_github=Secret(ACTION_TOKEN),
            uv__native_tls=True,
        )
    if settings.pyproject:
        add_pyproject_toml(
            modifications=modifications,
            gitea_host=settings.gitea_host,
            gitea_port=settings.gitea_port,
        )


##


def add_pyproject_toml(
    *,
    modifications: MutableSet[Path] | None = None,
    gitea_host: str = SETTINGS.gitea_host,
    gitea_port: int = SETTINGS.gitea_port,
) -> None:
    with yield_toml_doc(PYPROJECT_TOML, modifications=modifications) as doc:
        tool = get_table(doc, "tool")
        uv = get_table(tool, "uv")
        index = get_aot(uv, "index")
        ensure_aot_contains(
            index, _add_pyproject_toml_index(host=gitea_host, port=gitea_port)
        )


def _add_pyproject_toml_index(
    *, host: str = SETTINGS.gitea_host, port: int = SETTINGS.gitea_port
) -> Table:
    tab = table()
    tab["explicit"] = True
    tab["name"] = "gitea"
    tab["url"] = (
        f"https://{PYPI_GITEA_USERNAME}:{PYPI_GITEA_READ_TOKEN}@{host}:{port}/{API_PACKAGES_QRT_PYPI}/simple"
    )
    return tab


if __name__ == "__main__":
    main()
