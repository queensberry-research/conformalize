from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import PYPROJECT_TOML, paths_argument
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_aot,
    get_set_table,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
)
from tomlkit import table
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks.constants import PYPI_GITEA_READ_URL

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYPROJECT_TOML)
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths_use]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        tool = get_set_table(doc, "tool")
        uv = get_set_table(tool, "uv")
        index = get_set_aot(uv, "index")
        tab = table()
        tab["explicit"] = True
        tab["name"] = "gitea"
        tab["url"] = PYPI_GITEA_READ_URL
        ensure_contains(index, tab)
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
