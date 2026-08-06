"""Installed fixture-resource access helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from importlib import resources
from pathlib import Path


@contextmanager
def fixture_root() -> Iterator[Path]:
    """Yield the installed fixture directory as a temporary concrete path."""

    resource = resources.files("pdfcab").joinpath("fixtures")
    with resources.as_file(resource) as path:
        yield path
