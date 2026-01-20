from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITEA_PULL_REQUEST_YAML

from qrt_pre_commit_hooks.hooks.modify_ci_pull_request import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyCIPullRequest:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PULL_REQUEST_YAML
        for i in range(2):
            result = _run(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
