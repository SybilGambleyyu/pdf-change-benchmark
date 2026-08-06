"""Deterministic public-safe benchmark renderers."""

from __future__ import annotations

import json

from pdfcab.models import FixtureTruth, ScoreReport


def render_verification(truths: tuple[FixtureTruth, ...], output_format: str) -> str:
    """Render a successful fixture verification summary."""

    document = {
        "fixture_count": len(truths),
        "fixtures": [truth.public_dict() for truth in truths],
    }
    if output_format == "json":
        return _json(document)
    if output_format == "markdown":
        lines = ["# PDFCAB verification", "", f"Verified {len(truths)} fixtures.", ""]
        lines.extend(["| Fixture | Category |", "| --- | --- |"])
        lines.extend(f"| {truth.fixture_id} | {truth.category} |" for truth in truths)
        return "\n".join(lines) + "\n"
    raise ValueError("verification output format is unsupported")


def render_score(report: ScoreReport, output_format: str) -> str:
    """Render a public-safe adapter score report."""

    if output_format == "json":
        return _json(report.public_dict())
    if output_format == "markdown":
        lines = [
            "# PDFCAB score",
            "",
            f"Passed {report.passed_count} of {len(report.fixture_scores)} fixtures.",
            "",
            "| Fixture | Passed |",
            "| --- | --- |",
        ]
        lines.extend(
            f"| {score.fixture_id} | {'true' if score.passed else 'false'} |"
            for score in report.fixture_scores
        )
        return "\n".join(lines) + "\n"
    raise ValueError("score output format is unsupported")


def _json(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"
