"""Process-bound PDFFence compatibility scoring."""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from pdfcab.errors import AdapterError
from pdfcab.models import FixtureScore, FixtureTruth, ScoreReport
from pdfcab.resources import fixture_root
from pdfcab.validate import verify_fixture_tree

_RULE_NAMES: Final = {
    "PFP001": "no_active_content_changes",
    "PFP002": "no_embedded_content_changes",
    "PFP003": "no_interactive_feature_changes",
    "PFP004": "no_signature_structure_changes",
    "PFP005": "require_unencrypted",
    "PFP006": "require_single_revision",
}
_COMMAND_TIMEOUT_SECONDS: Final = 30


def score_pdffence(
    executable: str | Path | Sequence[str | Path] = "pdffence",
    *,
    fixtures: str | Path | None = None,
) -> ScoreReport:
    """Score a PDFFence executable using only its public JSON CLI contract."""

    command = _command(executable)
    if fixtures is not None:
        return _score_fixture_root(command, Path(fixtures))
    with fixture_root() as installed_fixtures:
        return _score_fixture_root(command, installed_fixtures)


def _command(executable: str | Path | Sequence[str | Path]) -> tuple[str, ...]:
    if isinstance(executable, (str, Path)):
        return (str(executable),)
    command = tuple(str(item) for item in executable)
    if not command:
        raise AdapterError("PDFFence adapter could not be invoked")
    return command


def _score_fixture_root(executable: tuple[str, ...], fixtures: Path) -> ScoreReport:
    truths = verify_fixture_tree(fixtures)
    scores = tuple(
        _score_fixture(executable, fixtures / truth.fixture_id, truth)
        for truth in truths
    )
    return ScoreReport(fixture_scores=scores)


def _score_fixture(
    executable: tuple[str, ...], directory: Path, truth: FixtureTruth
) -> FixtureScore:
    baseline = directory / "baseline.pdf"
    candidate = directory / "candidate.pdf"
    report = _run_json(executable, "diff", baseline, candidate)
    observed_change_kinds = _change_kinds(report)
    observed_policy_rule_ids = _policy_rule_ids(
        executable,
        baseline,
        candidate,
        truth.expected_policy_rule_ids,
    )
    return FixtureScore(
        fixture_id=truth.fixture_id,
        expected_change_kinds=truth.expected_change_kinds,
        observed_change_kinds=observed_change_kinds,
        expected_policy_rule_ids=truth.expected_policy_rule_ids,
        observed_policy_rule_ids=observed_policy_rule_ids,
    )


def _policy_rule_ids(
    executable: tuple[str, ...],
    baseline: Path,
    candidate: Path,
    expected_rule_ids: tuple[str, ...],
) -> tuple[str, ...]:
    if not expected_rule_ids:
        return ()
    policy_source = _policy_source(expected_rule_ids)
    with tempfile.TemporaryDirectory(prefix="pdfcab-policy-") as temporary:
        policy = Path(temporary) / "policy.yml"
        policy.write_text(policy_source, encoding="utf-8", newline="\n")
        report = _run_json(executable, "check", baseline, candidate, "--policy", policy)
    findings = report.get("findings")
    if not isinstance(findings, list):
        raise AdapterError("PDFFence adapter returned invalid JSON")
    identifiers: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict) or not isinstance(finding.get("rule_id"), str):
            raise AdapterError("PDFFence adapter returned invalid JSON")
        identifiers.add(finding["rule_id"])
    return tuple(sorted(identifiers))


def _policy_source(rule_ids: tuple[str, ...]) -> str:
    try:
        rule_names = tuple(_RULE_NAMES[rule_id] for rule_id in rule_ids)
    except KeyError:
        raise AdapterError("fixture policy expectation is unsupported") from None
    return "version: 1\nrules:\n" + "".join(
        f"  {rule_name}: true\n" for rule_name in rule_names
    )


def _run_json(
    executable: tuple[str, ...],
    command: str,
    *arguments: Path | str,
) -> dict[str, object]:
    invocation = [*executable, command, *(str(argument) for argument in arguments)]
    try:
        completed = subprocess.run(
            invocation,
            check=False,
            capture_output=True,
            text=True,
            timeout=_COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise AdapterError("PDFFence adapter could not be invoked") from None
    if completed.returncode not in {0, 1}:
        raise AdapterError("PDFFence adapter returned an execution error")
    try:
        document = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise AdapterError("PDFFence adapter returned invalid JSON") from None
    if not isinstance(document, dict):
        raise AdapterError("PDFFence adapter returned invalid JSON")
    return document


def _change_kinds(report: dict[str, object]) -> tuple[str, ...]:
    changes = report.get("changes")
    if not isinstance(changes, list):
        raise AdapterError("PDFFence adapter returned invalid JSON")
    kinds: set[str] = set()
    for change in changes:
        if not isinstance(change, dict) or not isinstance(change.get("kind"), str):
            raise AdapterError("PDFFence adapter returned invalid JSON")
        kinds.add(change["kind"])
    return tuple(sorted(kinds))
