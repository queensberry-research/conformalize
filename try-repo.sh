#!/usr/bin/env sh

PATH_DIR="$(
	cd -- "$(dirname "$0")" >/dev/null 2>&1 || exit
	pwd -P
)"
pre-commit try-repo --verbose --all-files "${PATH_DIR}" conformalize "$@"
