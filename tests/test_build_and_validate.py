"""Reproducible generation and public fixture-contract coverage."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pypdf import PdfReader
from pypdf.generic import ArrayObject, NameObject

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


def test_named_destination_rebind_pair_keeps_the_action_chain_fixed(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.named_destination_rebound"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_successor = baseline_primary["/Next"][0].get_object()
    candidate_successor = candidate_primary["/Next"][0].get_object()
    baseline_pairs = _destination_name_tree_pairs(baseline)
    candidate_pairs = _destination_name_tree_pairs(candidate)

    assert list(baseline.root_object).index(NameObject("/Names")) < list(
        baseline.root_object
    ).index(NameObject("/OpenAction"))
    assert str(baseline_successor["/S"]) == str(candidate_successor["/S"]) == "/GoTo"
    assert str(baseline_successor["/D"]) == str(candidate_successor["/D"])
    assert baseline_pairs[0] == baseline_successor["/D"]
    assert candidate_pairs[0] == candidate_successor["/D"]
    assert baseline_pairs[1].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[1].get_object()[0] == candidate.pages[1].indirect_reference


def test_named_destination_target_page_rotation_keeps_mapping_fixed(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.named_destination_target_page_rotated"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_successor = baseline_primary["/Next"][0].get_object()
    candidate_successor = candidate_primary["/Next"][0].get_object()
    baseline_pairs = _destination_name_tree_pairs(baseline)
    candidate_pairs = _destination_name_tree_pairs(candidate)

    assert str(baseline_successor["/D"]) == str(candidate_successor["/D"])
    assert baseline_pairs[1].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[1].get_object()[0] == candidate.pages[0].indirect_reference
    assert int(baseline.pages[0]["/Rotate"]) == 0
    assert int(candidate.pages[0]["/Rotate"]) == 90


def test_named_destination_pair_changes_only_an_unrelated_mapping(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.named_destination_unrelated_mapping_rewritten"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_primary = baseline.root_object["/OpenAction"].get_object()
    candidate_primary = candidate.root_object["/OpenAction"].get_object()
    baseline_successor = baseline_primary["/Next"][0].get_object()
    candidate_successor = candidate_primary["/Next"][0].get_object()
    baseline_pairs = _destination_name_tree_pairs(baseline)
    candidate_pairs = _destination_name_tree_pairs(candidate)

    assert str(baseline_successor["/D"]) == str(candidate_successor["/D"])
    assert baseline_pairs[0] == baseline_successor["/D"]
    assert candidate_pairs[0] == candidate_successor["/D"]
    assert baseline_pairs[1].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[1].get_object()[0] == candidate.pages[0].indirect_reference
    assert baseline_pairs[2] == candidate_pairs[2]
    assert baseline_pairs[3].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[3].get_object()[0] == candidate.pages[1].indirect_reference


def test_root_named_destination_rebind_pair_keeps_the_action_fixed(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.goto_root_named_destination_rebound"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()
    baseline_pairs = _destination_name_tree_pairs(baseline)
    candidate_pairs = _destination_name_tree_pairs(candidate)

    assert list(baseline.root_object).index(NameObject("/Names")) < list(
        baseline.root_object
    ).index(NameObject("/OpenAction"))
    assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/GoTo"
    assert "/Next" not in baseline_action
    assert "/Next" not in candidate_action
    assert str(baseline_action["/D"]) == str(candidate_action["/D"])
    assert baseline_pairs[0] == baseline_action["/D"]
    assert candidate_pairs[0] == candidate_action["/D"]
    assert baseline_pairs[1].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[1].get_object()[0] == candidate.pages[1].indirect_reference


def test_root_named_destination_target_page_rotation_keeps_mapping_fixed(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.goto_root_named_destination_target_page_rotated"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()
    baseline_pairs = _destination_name_tree_pairs(baseline)
    candidate_pairs = _destination_name_tree_pairs(candidate)

    assert str(baseline_action["/D"]) == str(candidate_action["/D"])
    assert baseline_pairs[1].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[1].get_object()[0] == candidate.pages[0].indirect_reference
    assert int(baseline.pages[0]["/Rotate"]) == 0
    assert int(candidate.pages[0]["/Rotate"]) == 90


def test_root_named_destination_pair_changes_only_an_unrelated_mapping(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = (
        generated / "active.goto_root_named_destination_unrelated_mapping_rewritten"
    )

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()
    baseline_pairs = _destination_name_tree_pairs(baseline)
    candidate_pairs = _destination_name_tree_pairs(candidate)

    assert str(baseline_action["/D"]) == str(candidate_action["/D"])
    assert baseline_pairs[0] == baseline_action["/D"]
    assert candidate_pairs[0] == candidate_action["/D"]
    assert baseline_pairs[1].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[1].get_object()[0] == candidate.pages[0].indirect_reference
    assert baseline_pairs[2] == candidate_pairs[2]
    assert baseline_pairs[3].get_object()[0] == baseline.pages[0].indirect_reference
    assert candidate_pairs[3].get_object()[0] == candidate.pages[1].indirect_reference


def test_open_destination_pairs_keep_the_catalog_action_entry_direct(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    rebound = generated / "active.open_destination_rebound"
    rotated = generated / "active.open_destination_target_page_rotated"

    before = PdfReader(rebound / "baseline.pdf", strict=True)
    after = PdfReader(rebound / "candidate.pdf", strict=True)
    before_open = before.root_object["/OpenAction"]
    after_open = after.root_object["/OpenAction"]

    assert isinstance(before_open, ArrayObject)
    assert isinstance(after_open, ArrayObject)
    assert len(before_open) == len(after_open) == 2
    assert str(before_open[1]) == str(after_open[1]) == "/Fit"
    assert before_open[0] == before.pages[0].indirect_reference
    assert after_open[0] == after.pages[1].indirect_reference

    before = PdfReader(rotated / "baseline.pdf", strict=True)
    after = PdfReader(rotated / "candidate.pdf", strict=True)
    assert before.root_object["/OpenAction"][0] == before.pages[0].indirect_reference
    assert after.root_object["/OpenAction"][0] == after.pages[0].indirect_reference
    assert int(before.pages[0]["/Rotate"]) == 0
    assert int(after.pages[0]["/Rotate"]) == 90


def test_named_link_destination_pairs_keep_the_link_and_mapping_fixed(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    rebound = generated / "active.link_named_destination_rebound"
    rotated = generated / "active.link_named_destination_target_page_rotated"
    unrelated = (
        generated / "active.link_named_destination_unrelated_mapping_rewritten"
    )

    before = PdfReader(rebound / "baseline.pdf", strict=True)
    after = PdfReader(rebound / "candidate.pdf", strict=True)
    before_link = before.pages[0]["/Annots"][0].get_object()
    after_link = after.pages[0]["/Annots"][0].get_object()
    assert str(before_link["/Subtype"]) == str(after_link["/Subtype"]) == "/Link"
    assert "/A" not in before_link
    assert "/A" not in after_link
    assert before_link["/Dest"] == after_link["/Dest"]
    assert _legacy_destination(before, before_link["/Dest"])[0] == before.pages[
        0
    ].indirect_reference
    assert _legacy_destination(after, after_link["/Dest"])[0] == after.pages[
        1
    ].indirect_reference

    before = PdfReader(rotated / "baseline.pdf", strict=True)
    after = PdfReader(rotated / "candidate.pdf", strict=True)
    before_link = before.pages[0]["/Annots"][0].get_object()
    after_link = after.pages[0]["/Annots"][0].get_object()
    assert before_link["/Dest"] == after_link["/Dest"]
    assert _legacy_destination(before, before_link["/Dest"])[0] == before.pages[
        0
    ].indirect_reference
    assert _legacy_destination(after, after_link["/Dest"])[0] == after.pages[
        0
    ].indirect_reference
    assert int(before.pages[0]["/Rotate"]) == 0
    assert int(after.pages[0]["/Rotate"]) == 90

    before = PdfReader(unrelated / "baseline.pdf", strict=True)
    after = PdfReader(unrelated / "candidate.pdf", strict=True)
    before_link = before.pages[0]["/Annots"][0].get_object()
    after_link = after.pages[0]["/Annots"][0].get_object()
    assert before_link["/Dest"] == after_link["/Dest"]
    assert _legacy_destination(before, before_link["/Dest"])[0] == before.pages[
        0
    ].indirect_reference
    assert _legacy_destination(after, after_link["/Dest"])[0] == after.pages[
        0
    ].indirect_reference
    before_unrelated = _unrelated_legacy_destination(before, before_link["/Dest"])
    after_unrelated = _unrelated_legacy_destination(after, after_link["/Dest"])
    assert before_unrelated[0] == before.pages[
        0
    ].indirect_reference
    assert after_unrelated[0] == after.pages[
        1
    ].indirect_reference


def test_named_outline_destination_pairs_keep_the_item_and_mapping_fixed(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    rebound = generated / "active.outline_named_destination_rebound"
    rotated = generated / "active.outline_named_destination_target_page_rotated"
    unrelated = (
        generated / "active.outline_named_destination_unrelated_mapping_rewritten"
    )

    before = PdfReader(rebound / "baseline.pdf", strict=True)
    after = PdfReader(rebound / "candidate.pdf", strict=True)
    before_item = before.root_object["/Outlines"]["/First"].get_object()
    after_item = after.root_object["/Outlines"]["/First"].get_object()
    assert before_item["/Dest"] == after_item["/Dest"]
    assert "/A" not in before_item
    assert "/A" not in after_item
    assert _legacy_destination(before, before_item["/Dest"])[0] == before.pages[
        0
    ].indirect_reference
    assert _legacy_destination(after, after_item["/Dest"])[0] == after.pages[
        1
    ].indirect_reference

    before = PdfReader(rotated / "baseline.pdf", strict=True)
    after = PdfReader(rotated / "candidate.pdf", strict=True)
    before_item = before.root_object["/Outlines"]["/First"].get_object()
    after_item = after.root_object["/Outlines"]["/First"].get_object()
    assert before_item["/Dest"] == after_item["/Dest"]
    assert _legacy_destination(before, before_item["/Dest"])[0] == before.pages[
        0
    ].indirect_reference
    assert _legacy_destination(after, after_item["/Dest"])[0] == after.pages[
        0
    ].indirect_reference
    assert int(before.pages[0]["/Rotate"]) == 0
    assert int(after.pages[0]["/Rotate"]) == 90

    before = PdfReader(unrelated / "baseline.pdf", strict=True)
    after = PdfReader(unrelated / "candidate.pdf", strict=True)
    before_item = before.root_object["/Outlines"]["/First"].get_object()
    after_item = after.root_object["/Outlines"]["/First"].get_object()
    assert before_item["/Dest"] == after_item["/Dest"]
    assert _legacy_destination(before, before_item["/Dest"])[0] == before.pages[
        0
    ].indirect_reference
    assert _legacy_destination(after, after_item["/Dest"])[0] == after.pages[
        0
    ].indirect_reference
    before_unrelated = _unrelated_legacy_destination(before, before_item["/Dest"])
    after_unrelated = _unrelated_legacy_destination(after, after_item["/Dest"])
    assert before_unrelated[0] == before.pages[
        0
    ].indirect_reference
    assert after_unrelated[0] == after.pages[
        1
    ].indirect_reference


def _open_destination(reader: PdfReader) -> ArrayObject:
    value = reader.root_object["/OpenAction"]
    assert isinstance(value, ArrayObject)
    return value


def _link_destination(reader: PdfReader) -> ArrayObject:
    link = reader.pages[0]["/Annots"][0].get_object()
    assert "/A" not in link
    value = link["/Dest"]
    assert isinstance(value, ArrayObject)
    return value


def _outline_destination(reader: PdfReader) -> ArrayObject:
    item = reader.root_object["/Outlines"]["/First"].get_object()
    assert "/A" not in item
    value = item["/Dest"]
    assert isinstance(value, ArrayObject)
    return value


def _assert_structure_target(
    reader: PdfReader,
    destination: ArrayObject,
    expected_index: int,
):
    assert len(destination) == 2
    assert str(destination[1]) == "/Fit"
    targets = reader.root_object["/StructTreeRoot"]["/K"]
    assert destination[0] == targets[expected_index]
    target = destination[0].get_object()
    assert str(target["/Type"]) == "/StructElem"
    return target


def _named_link_destination_map(reader: PdfReader):
    link = reader.pages[0]["/Annots"][0].get_object()
    assert "/A" not in link
    return reader.root_object["/Dests"][link["/Dest"]]


def test_goto_structure_destination_pairs_preserve_sd_precedence(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    rebound = generated / "active.goto_structure_destination_rebound"
    fallback = generated / "active.goto_structure_destination_fallback_rewritten"
    metadata = (
        generated / "active.goto_structure_destination_target_metadata_rewritten"
    )

    before = PdfReader(rebound / "baseline.pdf", strict=True)
    after = PdfReader(rebound / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"].get_object()
    after_action = after.root_object["/OpenAction"].get_object()
    assert str(before_action["/S"]) == str(after_action["/S"]) == "/GoTo"
    assert before_action["/D"][0] == before.pages[0].indirect_reference
    assert after_action["/D"][0] == after.pages[0].indirect_reference
    _assert_structure_target(before, before_action["/SD"], 0)
    _assert_structure_target(after, after_action["/SD"], 1)

    before = PdfReader(fallback / "baseline.pdf", strict=True)
    after = PdfReader(fallback / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"].get_object()
    after_action = after.root_object["/OpenAction"].get_object()
    assert before_action["/D"][0] == before.pages[0].indirect_reference
    assert after_action["/D"][0] == after.pages[1].indirect_reference
    _assert_structure_target(before, before_action["/SD"], 0)
    _assert_structure_target(after, after_action["/SD"], 0)

    before = PdfReader(metadata / "baseline.pdf", strict=True)
    after = PdfReader(metadata / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"].get_object()
    after_action = after.root_object["/OpenAction"].get_object()
    before_target = _assert_structure_target(before, before_action["/SD"], 0)
    after_target = _assert_structure_target(after, after_action["/SD"], 0)
    assert str(before_target["/Alt"]) != str(after_target["/Alt"])


@pytest.mark.parametrize(
    ("rebound_id", "metadata_id", "destination"),
    (
        (
            "active.open_structure_destination_rebound",
            "active.open_structure_destination_target_metadata_rewritten",
            _open_destination,
        ),
        (
            "active.link_structure_destination_rebound",
            "active.link_structure_destination_target_metadata_rewritten",
            _link_destination,
        ),
        (
            "active.outline_structure_destination_rebound",
            "active.outline_structure_destination_target_metadata_rewritten",
            _outline_destination,
        ),
    ),
)
def test_direct_structure_destination_pairs_keep_the_root_fixed(
    tmp_path,
    rebound_id,
    metadata_id,
    destination,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)

    before = PdfReader(generated / rebound_id / "baseline.pdf", strict=True)
    after = PdfReader(generated / rebound_id / "candidate.pdf", strict=True)
    before_target = _assert_structure_target(before, destination(before), 0)
    after_target = _assert_structure_target(after, destination(after), 1)
    assert str(before_target["/Type"]) == str(after_target["/Type"]) == "/StructElem"

    before = PdfReader(generated / metadata_id / "baseline.pdf", strict=True)
    after = PdfReader(generated / metadata_id / "candidate.pdf", strict=True)
    before_target = _assert_structure_target(before, destination(before), 0)
    after_target = _assert_structure_target(after, destination(after), 0)
    assert str(before_target["/Alt"]) != str(after_target["/Alt"])


def test_named_and_action_chain_structure_destination_pairs_are_semantic(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    named_rebound = generated / "active.link_named_structure_destination_rebound"
    named_fallback = (
        generated / "active.link_named_structure_destination_fallback_rewritten"
    )
    chain_rebound = generated / "active.action_chain_structure_destination_rebound"
    chain_metadata = (
        generated
        / "active.action_chain_structure_destination_target_metadata_rewritten"
    )

    before = PdfReader(named_rebound / "baseline.pdf", strict=True)
    after = PdfReader(named_rebound / "candidate.pdf", strict=True)
    before_map = _named_link_destination_map(before)
    after_map = _named_link_destination_map(after)
    assert before_map["/D"][0] == before.pages[0].indirect_reference
    assert after_map["/D"][0] == after.pages[0].indirect_reference
    _assert_structure_target(before, before_map["/SD"], 0)
    _assert_structure_target(after, after_map["/SD"], 1)

    before = PdfReader(named_fallback / "baseline.pdf", strict=True)
    after = PdfReader(named_fallback / "candidate.pdf", strict=True)
    before_map = _named_link_destination_map(before)
    after_map = _named_link_destination_map(after)
    assert before_map["/D"][0] == before.pages[0].indirect_reference
    assert after_map["/D"][0] == after.pages[1].indirect_reference
    _assert_structure_target(before, before_map["/SD"], 0)
    _assert_structure_target(after, after_map["/SD"], 0)

    before = PdfReader(chain_rebound / "baseline.pdf", strict=True)
    after = PdfReader(chain_rebound / "candidate.pdf", strict=True)
    before_successor = before.root_object["/OpenAction"]["/Next"].get_object()
    after_successor = after.root_object["/OpenAction"]["/Next"].get_object()
    _assert_structure_target(before, before_successor["/SD"], 0)
    _assert_structure_target(after, after_successor["/SD"], 1)

    before = PdfReader(chain_metadata / "baseline.pdf", strict=True)
    after = PdfReader(chain_metadata / "candidate.pdf", strict=True)
    before_successor = before.root_object["/OpenAction"]["/Next"].get_object()
    after_successor = after.root_object["/OpenAction"]["/Next"].get_object()
    before_target = _assert_structure_target(before, before_successor["/SD"], 0)
    after_target = _assert_structure_target(after, after_successor["/SD"], 0)
    assert str(before_target["/Alt"]) != str(after_target["/Alt"])


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


def _legacy_destination(reader: PdfReader, name: object):
    return reader.root_object["/Dests"][name].get_object()


def _unrelated_legacy_destination(reader: PdfReader, selected_name: object):
    destinations = reader.root_object["/Dests"]
    name = next(name for name in destinations if name != selected_name)
    return destinations[name].get_object()


def _destination_name_tree_pairs(reader: PdfReader):
    """Return the one leaf's alternating name/destination entries."""

    tree = reader.root_object["/Names"]["/Dests"]
    return tree["/Kids"][0].get_object()["/Names"]
