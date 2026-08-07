"""CLI and installed-version coverage for PDFCAB."""

from __future__ import annotations

import json
from importlib.metadata import version as distribution_version

import pytest

from pdfcab import __version__
from pdfcab.cli import main


def test_cli_version_matches_installed_distribution(capsys):
    installed_version = distribution_version("pdf-change-benchmark")

    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert __version__ == installed_version
    assert capsys.readouterr().out == f"pdfcab {installed_version}\n"


def test_verify_and_build_commands_emit_public_json(tmp_path, capsys):
    assert main(["verify"]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["fixture_count"] == 154

    destination = tmp_path / "built"
    assert main(["build", str(destination)]) == 0
    built = json.loads(capsys.readouterr().out)
    assert built["fixture_count"] == 154
    assert (destination / "manifest.jsonl").is_file()
    assert "PDFCAB_INERT" not in json.dumps(built)
