"""Reproducible generation and public fixture-contract coverage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pypdf import PdfReader

from pdfcab.build import FIXTURE_SPECS, build_fixture_tree
from pdfcab.errors import FixtureError
from pdfcab.resources import fixture_root
from pdfcab.validate import verify_fixture_tree


def test_generated_tree_matches_packaged_fixture_bytes(tmp_path):
    generated = tmp_path / "generated"

    built_truths = build_fixture_tree(generated)
    verified_truths = verify_fixture_tree(generated)

    assert verified_truths == built_truths
    assert len(verified_truths) == len(FIXTURE_SPECS)
    with fixture_root() as packaged:
        assert _tree_bytes(generated) == _tree_bytes(packaged)


def test_build_refuses_to_replace_a_nonempty_destination(tmp_path):
    destination = tmp_path / "existing"
    destination.mkdir()
    (destination / "keep.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(FixtureError, match="empty"):
        build_fixture_tree(destination)


def test_validation_rejects_schema_tampering(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    truth_path = generated / "active.javascript_added" / "truth.json"
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    del truth["schema_version"]
    truth_path.write_text(json.dumps(truth), encoding="utf-8")

    with pytest.raises(FixtureError, match="truth"):
        verify_fixture_tree(generated)


def test_public_truth_has_no_inert_payload_marker():
    with fixture_root() as packaged:
        public_truth = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(packaged.rglob("*.json"))
        )

    assert "PDFCAB_INERT" not in public_truth
    assert "example.invalid" not in public_truth
    assert "pdfcab-inert-password" not in public_truth


def test_action_subtype_pair_retains_an_embedded_child_target(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.goto_to_embedded_goto"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)

    for reader in (baseline, candidate):
        names = reader.root_object["/Names"]
        embedded_files = names["/EmbeddedFiles"]["/Names"]
        assert len(embedded_files) == 2

    action = candidate.root_object["/OpenAction"].get_object()
    target = action["/T"]
    assert str(action["/S"]) == "/GoToE"
    assert str(target["/R"]) == "/C"
    assert str(target["/N"]) == "PDFCAB_CHILD.pdf"


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
