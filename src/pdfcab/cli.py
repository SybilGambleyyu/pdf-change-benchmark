"""Command-line interface for PDFCAB."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from pdfcab import __version__
from pdfcab.build import build_fixture_tree
from pdfcab.errors import OutputError, PdfCabError
from pdfcab.output import render_score, render_verification
from pdfcab.resources import fixture_root
from pdfcab.score import score_pdffence
from pdfcab.validate import verify_fixture_tree


def main(argv: Sequence[str] | None = None) -> int:
    """Run PDFCAB and return its documented process status."""

    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "build":
            truths = build_fixture_tree(arguments.destination)
            _write_output(
                render_verification(truths, arguments.format),
                arguments.output,
            )
            return 0
        if arguments.command == "verify":
            if arguments.fixtures is None:
                with fixture_root() as path:
                    truths = verify_fixture_tree(path)
            else:
                truths = verify_fixture_tree(arguments.fixtures)
            _write_output(
                render_verification(truths, arguments.format),
                arguments.output,
            )
            return 0
        if arguments.command == "score":
            report = score_pdffence(
                arguments.pdffence,
                fixtures=arguments.fixtures,
            )
            _write_output(render_score(report, arguments.format), arguments.output)
            return 0 if report.passed_count == len(report.fixture_scores) else 1
    except PdfCabError as error:
        print(f"pdfcab: {error}", file=sys.stderr)
        return 2
    parser.error("a command is required")
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdfcab",
        description="Reproducible paired-PDF static change-assurance fixtures.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="build into an empty directory")
    build.add_argument("destination")
    build.add_argument("--format", choices=("json", "markdown"), default="json")
    build.add_argument("--output", help="write atomically to this path")

    verify = commands.add_parser("verify", help="verify a fixture tree")
    verify.add_argument("--fixtures", help="use this fixture directory")
    verify.add_argument("--format", choices=("json", "markdown"), default="json")
    verify.add_argument("--output", help="write atomically to this path")

    score = commands.add_parser("score", help="score a PDFFence executable")
    score.add_argument("--pdffence", default="pdffence")
    score.add_argument("--fixtures", help="use this fixture directory")
    score.add_argument("--format", choices=("json", "markdown"), default="json")
    score.add_argument("--output", help="write atomically to this path")
    return parser


def _write_output(content: str, destination: str | None) -> None:
    if destination is None:
        sys.stdout.write(content)
        return
    temporary_path: Path | None = None
    try:
        target = Path(destination)
        if target.exists() and target.is_symlink():
            raise OutputError("output destination must not be a symbolic link")
        if not target.parent.is_dir():
            raise OutputError("output directory does not exist")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".pdfcab-",
            dir=target.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, target)
        temporary_path = None
    except OutputError:
        raise
    except (OSError, TypeError, ValueError):
        raise OutputError("output cannot be written") from None
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
