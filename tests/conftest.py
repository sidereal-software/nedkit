"""Shared fixtures.

Tests that need XNEdit are marked ``xnedit`` and skip when there is no usable
binary or display, so ``uv run pytest`` still does something useful on a
machine without XQuartz. Set ``NEDKIT_REQUIRE_XNEDIT=1`` to turn those skips
into failures, which is what you want if you are about to trust the result.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from nedkit import XNEditRunner, XNEditUnavailable, find_binary, library_files

REPO_ROOT = Path(__file__).resolve().parents[1]


def _unavailable(reason: str) -> None:
    if os.environ.get("NEDKIT_REQUIRE_XNEDIT"):
        pytest.fail(f"NEDKIT_REQUIRE_XNEDIT is set but {reason}")
    pytest.skip(reason)


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def xnedit_binary() -> Path:
    binary = find_binary()
    if binary is None:
        _unavailable(
            "no XNEdit found. Put it on $PATH or set NEDKIT_XNEDIT to the binary. "
            "There are no prebuilt macOS binaries; see the README for the build."
        )
    return binary


@pytest.fixture(scope="session")
def runner(
    xnedit_binary: Path, tmp_path_factory: pytest.TempPathFactory
) -> XNEditRunner:
    """XNEdit with an empty configuration and no macro libraries loaded."""
    root = tmp_path_factory.mktemp("xnedit-plain")
    instance = XNEditRunner(xnedit_binary, root / "home")
    try:
        instance.smoke_test(root / "smoke")
    except XNEditUnavailable as error:
        _unavailable(str(error))
    return instance


@pytest.fixture(scope="session")
def lib_runner(
    xnedit_binary: Path, tmp_path_factory: pytest.TempPathFactory
) -> XNEditRunner:
    """XNEdit with every macros/lib/ file loaded through autoload.nm."""
    root = tmp_path_factory.mktemp("xnedit-lib")
    autoload = "\n".join(
        path.read_text(encoding="utf-8") for path in library_files(REPO_ROOT)
    )
    instance = XNEditRunner(xnedit_binary, root / "home", autoload=autoload)
    try:
        instance.smoke_test(root / "smoke")
    except XNEditUnavailable as error:
        _unavailable(str(error))
    return instance
