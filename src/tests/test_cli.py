from __future__ import annotations

from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML, PYPROJECT_TOML
from pytest import mark, param
from utilities.constants import HOUR
from utilities.pytest import throttle_test
from utilities.subprocess import run


class TestCLI:
    @mark.parametrize(
        ("hook", "args"),
        [
            param("modify-ci-pull-request", [PRE_COMMIT_CONFIG_YAML]),
            param("modify-ci-push", [PRE_COMMIT_CONFIG_YAML]),
            param("modify-pre-commit", [PRE_COMMIT_CONFIG_YAML]),
            param("modify-pyproject", [PYPROJECT_TOML]),
        ],
    )
    @throttle_test(duration=HOUR)
    def test_main(self, *, hook: str, args: list[str]) -> None:
        run(hook, *args)
