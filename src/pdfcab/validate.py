"""Strict validation of PDFCAB's public fixture contract."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Final

from pdfcab.build import FIXTURE_SCHEMA_VERSION, FIXTURE_SPECS
from pdfcab.errors import FixtureError
from pdfcab.models import FixtureTruth

_MAX_TRUTH_BYTES: Final = 16 * 1024
_MAX_MANIFEST_BYTES: Final = 128 * 1024
_KNOWN_CHANGE_KINDS: Final = frozenset(
    {
        "active_content_action_sequence_changed",
        "active_content_inventory_changed",
        "active_content_execution_order_changed",
        "active_content_payload_changed",
        "embedded_content_inventory_changed",
        "encryption_state_changed",
        "format_version_changed",
        "inspection_state_changed",
        "interactive_feature_inventory_changed",
        "metadata_inventory_changed",
        "optional_content_inventory_changed",
        "page_count_changed",
        "reachable_object_count_changed",
        "revision_chain_changed",
        "signature_byte_range_coverage_changed",
        "signature_structure_inventory_changed",
        "stored_pdf_bytes_changed",
    }
)
_KNOWN_POLICY_RULE_IDS: Final = frozenset(
    {
        "PFP001",
        "PFP002",
        "PFP003",
        "PFP004",
        "PFP005",
        "PFP006",
        "PFP007",
        "PFP008",
        "PFP009",
        "PFP010",
        "PFP011",
    }
)


def verify_fixture_tree(root: str | Path) -> tuple[FixtureTruth, ...]:
    """Validate fixture membership, PDFs, and public truth against the spec."""

    fixture_root = _regular_directory(root)
    expected_truths = {
        spec.fixture_id: spec.truth().public_dict() for spec in FIXTURE_SPECS
    }
    manifest_truths = _load_manifest(fixture_root / "manifest.jsonl")
    if {truth.fixture_id for truth in manifest_truths} != set(expected_truths):
        raise FixtureError("fixture manifest does not match the supported fixture set")

    for truth in manifest_truths:
        if truth.public_dict() != expected_truths[truth.fixture_id]:
            raise FixtureError("fixture truth does not match the supported contract")
        _verify_fixture_directory(fixture_root / truth.fixture_id, truth)

    expected_entries = {truth.fixture_id for truth in manifest_truths} | {
        "manifest.jsonl"
    }
    actual_entries = {entry.name for entry in fixture_root.iterdir()}
    if actual_entries != expected_entries:
        raise FixtureError("fixture tree contains unexpected entries")
    return tuple(sorted(manifest_truths, key=lambda value: value.fixture_id))


def _regular_directory(root: str | Path) -> Path:
    try:
        path = Path(root)
        if path.is_symlink() or not path.is_dir():
            raise FixtureError("fixture root must be a directory")
        return path
    except FixtureError:
        raise
    except (OSError, TypeError, ValueError):
        raise FixtureError("fixture root cannot be inspected") from None


def _load_manifest(path: Path) -> tuple[FixtureTruth, ...]:
    source = _read_regular_file(path, _MAX_MANIFEST_BYTES)
    try:
        records = [json.loads(line) for line in source.decode("utf-8").splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise FixtureError("fixture manifest is invalid") from None
    if not records:
        raise FixtureError("fixture manifest is invalid")
    truths = tuple(_truth_from_document(record) for record in records)
    identifiers = tuple(truth.fixture_id for truth in truths)
    if identifiers != tuple(sorted(identifiers)) or len(set(identifiers)) != len(
        identifiers
    ):
        raise FixtureError("fixture manifest is invalid")
    return truths


def _verify_fixture_directory(path: Path, expected: FixtureTruth) -> None:
    try:
        if path.is_symlink() or not path.is_dir():
            raise FixtureError("fixture directory is invalid")
        expected_entries = {"baseline.pdf", "candidate.pdf", "truth.json"}
        if {entry.name for entry in path.iterdir()} != expected_entries:
            raise FixtureError("fixture directory is invalid")
    except FixtureError:
        raise
    except (OSError, TypeError, ValueError):
        raise FixtureError("fixture directory is invalid") from None

    for filename in ("baseline.pdf", "candidate.pdf"):
        source = _read_regular_file(path / filename, 128 * 1024 * 1024)
        if not source.startswith(b"%PDF-"):
            raise FixtureError("fixture PDF is invalid")
    truth_source = _read_regular_file(path / "truth.json", _MAX_TRUTH_BYTES)
    try:
        actual = _truth_from_document(json.loads(truth_source.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise FixtureError("fixture truth is invalid") from None
    if actual != expected:
        raise FixtureError("fixture truth does not match its manifest entry")


def _read_regular_file(path: Path, maximum_bytes: int) -> bytes:
    try:
        if path.is_symlink():
            raise FixtureError("fixture file must be regular")
        source_stat = path.stat()
        if not stat.S_ISREG(source_stat.st_mode) or source_stat.st_size > maximum_bytes:
            raise FixtureError("fixture file is invalid")
        return path.read_bytes()
    except FixtureError:
        raise
    except (OSError, TypeError, ValueError):
        raise FixtureError("fixture file cannot be read") from None


def _truth_from_document(document: object) -> FixtureTruth:
    if not isinstance(document, dict) or set(document) != {
        "schema_version",
        "id",
        "category",
        "description",
        "expected_change_kinds",
        "expected_policy_rule_ids",
    }:
        raise FixtureError("fixture truth is invalid")
    schema_version = document["schema_version"]
    fixture_id = document["id"]
    category = document["category"]
    description = document["description"]
    change_kinds = document["expected_change_kinds"]
    policy_rule_ids = document["expected_policy_rule_ids"]
    if (
        type(schema_version) is not int
        or schema_version != FIXTURE_SCHEMA_VERSION
        or not isinstance(fixture_id, str)
        or not fixture_id
        or not isinstance(category, str)
        or not category
        or not isinstance(description, str)
        or not description
        or not _sorted_string_tuple(change_kinds, _KNOWN_CHANGE_KINDS)
        or not _sorted_string_tuple(policy_rule_ids, _KNOWN_POLICY_RULE_IDS)
    ):
        raise FixtureError("fixture truth is invalid")
    return FixtureTruth(
        schema_version=schema_version,
        fixture_id=fixture_id,
        category=category,
        description=description,
        expected_change_kinds=tuple(change_kinds),
        expected_policy_rule_ids=tuple(policy_rule_ids),
    )


def _sorted_string_tuple(value: object, allowed: frozenset[str]) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and item in allowed for item in value)
        and value == sorted(set(value))
    )
