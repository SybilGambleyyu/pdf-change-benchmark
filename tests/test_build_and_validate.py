"""Reproducible generation and public fixture-contract coverage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pypdf import PdfReader
from pypdf.generic import NameObject

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


def test_action_subtype_pair_retains_3d_and_document_part_targets(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.goto_3d_view_to_document_part"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)

    for reader in (baseline, candidate):
        page = reader.pages[0]
        document_part = page["/DPart"].get_object()
        document_part_root = reader.root_object["/DPartRoot"].get_object()
        annotations = page["/Annots"]

        assert str(document_part["/Type"]) == "/DPart"
        assert document_part["/Parent"] == reader.root_object["/DPartRoot"]
        assert document_part_root["/DPartRootNode"] == page["/DPart"]
        assert len(annotations) == 1
        assert str(annotations[0].get_object()["/Subtype"]) == "/3D"

    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()

    assert str(baseline_action["/S"]) == "/GoTo3DView"
    assert str(baseline_action["/TA"].get_object()["/Subtype"]) == "/3D"
    assert str(candidate_action["/S"]) == "/GoToDp"
    assert str(candidate_action["/Dp"].get_object()["/Type"]) == "/DPart"


def test_uri_payload_rewrite_pair_keeps_the_action_inventory_fixed(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.uri_payload_rewritten"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()

    assert str(baseline_action["/S"]) == "/URI"
    assert str(candidate_action["/S"]) == "/URI"
    assert str(baseline_action["/URI"]) != str(candidate_action["/URI"])


def test_javascript_trigger_rebound_pair_exchanges_trigger_bindings(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.javascript_trigger_rebound"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_open = baseline.root_object["/OpenAction"].get_object()
    candidate_open = candidate.root_object["/OpenAction"].get_object()
    baseline_will_close = baseline.root_object["/AA"]["/WC"].get_object()
    candidate_will_close = candidate.root_object["/AA"]["/WC"].get_object()

    for action in (
        baseline_open,
        candidate_open,
        baseline_will_close,
        candidate_will_close,
    ):
        assert str(action["/S"]) == "/JavaScript"
    assert str(baseline_open["/JS"]) == str(candidate_will_close["/JS"])
    assert str(baseline_will_close["/JS"]) == str(candidate_open["/JS"])
    assert str(baseline_open["/JS"]) != str(baseline_will_close["/JS"])


def test_javascript_action_chain_pair_exchanges_successor_order(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.javascript_action_chain_reordered"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_next = [
        action.get_object() for action in baseline_primary["/Next"]
    ]
    candidate_next = [
        action.get_object() for action in candidate_primary["/Next"]
    ]

    assert str(baseline_primary["/S"]) == "/JavaScript"
    assert str(candidate_primary["/S"]) == "/JavaScript"
    assert len(baseline_next) == len(candidate_next) == 2
    assert all(str(action["/S"]) == "/JavaScript" for action in baseline_next)
    assert all(str(action["/S"]) == "/JavaScript" for action in candidate_next)
    assert str(baseline_next[0]["/JS"]) == str(candidate_next[1]["/JS"])
    assert str(baseline_next[1]["/JS"]) == str(candidate_next[0]["/JS"])
    assert str(baseline_next[0]["/JS"]) != str(baseline_next[1]["/JS"])


def test_javascript_action_chain_shared_array_pair_is_previsited(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.javascript_action_chain_reordered_shared_array"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_piece = baseline.root_object["/PieceInfo"]["/PDFCAB"]
    candidate_piece = candidate.root_object["/PieceInfo"]["/PDFCAB"]

    assert baseline_primary.raw_get(NameObject("/Next")) == baseline_piece.raw_get(
        NameObject("/Shared")
    )
    assert candidate_primary.raw_get(NameObject("/Next")) == candidate_piece.raw_get(
        NameObject("/Shared")
    )
    baseline_next = [
        action.get_object() for action in baseline_primary["/Next"]
    ]
    candidate_next = [
        action.get_object() for action in candidate_primary["/Next"]
    ]
    assert str(baseline_next[0]["/JS"]) == str(candidate_next[1]["/JS"])
    assert str(baseline_next[1]["/JS"]) == str(candidate_next[0]["/JS"])


@pytest.mark.parametrize(
    ("fixture_id", "shared"),
    (
        ("active.action_chain_action_types_reordered", False),
        ("active.action_chain_action_types_reordered_shared_array", True),
    ),
)
def test_action_chain_type_pair_exchanges_successor_order(
    tmp_path,
    fixture_id,
    shared,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_next = [
        action.get_object() for action in baseline_primary["/Next"]
    ]
    candidate_next = [
        action.get_object() for action in candidate_primary["/Next"]
    ]

    assert str(baseline_primary["/S"]) == "/JavaScript"
    assert str(candidate_primary["/S"]) == "/JavaScript"
    assert [str(action["/S"]) for action in baseline_next] == [
        "/SetOCGState",
        "/GoTo",
    ]
    assert [str(action["/S"]) for action in candidate_next] == [
        "/GoTo",
        "/SetOCGState",
    ]
    for reader, actions in (
        (baseline, baseline_next),
        (candidate, candidate_next),
    ):
        group = reader.root_object["/OCProperties"]["/OCGs"][0]
        set_state = next(
            action for action in actions if str(action["/S"]) == "/SetOCGState"
        )
        goto = next(action for action in actions if str(action["/S"]) == "/GoTo")
        assert str(set_state["/State"][0]) == "/ON"
        assert set_state["/State"][1] == group
        assert goto["/D"][0] == reader.pages[0].indirect_reference
        assert str(goto["/D"][1]) == "/Fit"
    if shared:
        baseline_piece = baseline.root_object["/PieceInfo"]["/PDFCAB"]
        candidate_piece = candidate.root_object["/PieceInfo"]["/PDFCAB"]
        assert baseline_primary.raw_get(
            NameObject("/Next")
        ) == baseline_piece.raw_get(NameObject("/Shared"))
        assert candidate_primary.raw_get(
            NameObject("/Next")
        ) == candidate_piece.raw_get(NameObject("/Shared"))


@pytest.mark.parametrize(
    ("fixture_id", "shared"),
    (
        ("active.action_chain_same_type_reordered", False),
        ("active.action_chain_same_type_reordered_shared_array", True),
    ),
)
def test_action_chain_same_type_pair_exchanges_real_page_destinations(
    tmp_path,
    fixture_id,
    shared,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_next = [
        action.get_object() for action in baseline_primary["/Next"]
    ]
    candidate_next = [
        action.get_object() for action in candidate_primary["/Next"]
    ]

    assert len(baseline.pages) == len(candidate.pages) == 2
    assert all(str(action["/S"]) == "/GoTo" for action in baseline_next)
    assert all(str(action["/S"]) == "/GoTo" for action in candidate_next)
    assert [action["/D"][0] for action in baseline_next] == [
        baseline.pages[0].indirect_reference,
        baseline.pages[1].indirect_reference,
    ]
    assert [action["/D"][0] for action in candidate_next] == [
        candidate.pages[1].indirect_reference,
        candidate.pages[0].indirect_reference,
    ]
    assert all(str(action["/D"][1]) == "/Fit" for action in baseline_next)
    assert all(str(action["/D"][1]) == "/Fit" for action in candidate_next)
    if shared:
        baseline_piece = baseline.root_object["/PieceInfo"]["/PDFCAB"]
        candidate_piece = candidate.root_object["/PieceInfo"]["/PDFCAB"]
        assert baseline_primary.raw_get(
            NameObject("/Next")
        ) == baseline_piece.raw_get(NameObject("/Shared"))
        assert candidate_primary.raw_get(
            NameObject("/Next")
        ) == candidate_piece.raw_get(NameObject("/Shared"))


def test_action_chain_destination_page_rotation_keeps_action_data_fixed(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.action_chain_destination_page_rotated"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_successor = baseline_primary["/Next"][0].get_object()
    candidate_successor = candidate_primary["/Next"][0].get_object()

    assert str(baseline_successor["/S"]) == "/GoTo"
    assert str(candidate_successor["/S"]) == "/GoTo"
    assert baseline_successor["/D"][0] == baseline.pages[0].indirect_reference
    assert candidate_successor["/D"][0] == candidate.pages[0].indirect_reference
    assert str(baseline_successor["/D"][1]) == "/Fit"
    assert str(candidate_successor["/D"][1]) == "/Fit"
    assert int(baseline.pages[0]["/Rotate"]) == 0
    assert int(candidate.pages[0]["/Rotate"]) == 90


def test_javascript_stream_filter_pair_keeps_raw_bytes_fixed(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.javascript_stream_filter_rewritten"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()
    baseline_stream = baseline_action["/JS"].get_object()
    candidate_stream = candidate_action["/JS"].get_object()

    assert str(baseline_action["/S"]) == "/JavaScript"
    assert str(candidate_action["/S"]) == "/JavaScript"
    assert baseline_stream._data == candidate_stream._data == b"41>0"
    assert "/Filter" not in baseline_stream
    assert str(candidate_stream["/Filter"]) == "/ASCIIHexDecode"
    assert baseline_stream.get_data() == b"41>0"
    assert candidate_stream.get_data() == b"A"


@pytest.mark.parametrize(
    ("fixture_id", "action_type", "as_file_specification"),
    (
        ("active.launch_target_rewritten", "/Launch", False),
        ("active.remote_goto_target_rewritten", "/GoToR", True),
        ("active.embedded_goto_target_rewritten", "/GoToE", True),
        ("active.submit_form_target_rewritten", "/SubmitForm", False),
        ("active.import_data_target_rewritten", "/ImportData", True),
    ),
)
def test_external_action_target_pairs_keep_the_action_inventory_fixed(
    tmp_path,
    fixture_id,
    action_type,
    as_file_specification,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()
    baseline_target = baseline_action["/F"]
    candidate_target = candidate_action["/F"]

    assert str(baseline_action["/S"]) == action_type
    assert str(candidate_action["/S"]) == action_type
    if as_file_specification:
        assert str(baseline_target["/Type"]) == "/Filespec"
        assert str(candidate_target["/Type"]) == "/Filespec"
        baseline_target = baseline_target["/F"]
        candidate_target = candidate_target["/F"]
    assert str(baseline_target) != str(candidate_target)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
