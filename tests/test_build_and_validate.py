"""Reproducible generation and public fixture-contract coverage."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pypdf import PdfReader
from pypdf.generic import ArrayObject, IndirectObject, NameObject, NumberObject

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


def test_signature_current_file_coverage_pair_retains_a_prior_byte_range(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.current_file_coverage_lost"

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    baseline = PdfReader(baseline_path, strict=True)
    candidate = PdfReader(candidate_path, strict=True)
    baseline_signature = baseline.root_object["/AcroForm"]["/Fields"][0]["/V"]
    candidate_signature = candidate.root_object["/AcroForm"]["/Fields"][0]["/V"]
    baseline_range = tuple(int(value) for value in baseline_signature["/ByteRange"])
    candidate_range = tuple(int(value) for value in candidate_signature["/ByteRange"])

    assert str(baseline_signature["/Type"]) == "/Sig"
    assert str(candidate_signature["/Type"]) == "/Sig"
    assert baseline_range == candidate_range
    assert baseline_range[0] == 0
    assert baseline_range[-2] + baseline_range[-1] == baseline_path.stat().st_size
    assert candidate_path.stat().st_size > baseline_path.stat().st_size
    assert candidate_range[-2] + candidate_range[-1] < candidate_path.stat().st_size


def test_signature_current_file_coverage_requirement_pair_is_stale_on_both_sides(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.current_file_coverage_required"

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    baseline = PdfReader(baseline_path, strict=True)
    candidate = PdfReader(candidate_path, strict=True)
    baseline_signature = baseline.root_object["/AcroForm"]["/Fields"][0]["/V"]
    candidate_signature = candidate.root_object["/AcroForm"]["/Fields"][0]["/V"]
    baseline_range = tuple(int(value) for value in baseline_signature["/ByteRange"])
    candidate_range = tuple(int(value) for value in candidate_signature["/ByteRange"])

    assert baseline_range == candidate_range
    assert baseline_range[0] == 0
    assert baseline_range[-2] + baseline_range[-1] < baseline_path.stat().st_size
    assert candidate_path.stat().st_size > baseline_path.stat().st_size
    assert candidate_range[-2] + candidate_range[-1] < candidate_path.stat().st_size


def test_signature_contents_bound_coverage_pair_has_one_wider_current_gap(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.contents_bound_current_coverage_required"

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    baseline = PdfReader(baseline_path, strict=True)
    candidate = PdfReader(candidate_path, strict=True)
    baseline_signature = baseline.root_object["/AcroForm"]["/Fields"][0]["/V"]
    candidate_signature = candidate.root_object["/AcroForm"]["/Fields"][0]["/V"]
    baseline_range = tuple(int(value) for value in baseline_signature["/ByteRange"])
    candidate_range = tuple(int(value) for value in candidate_signature["/ByteRange"])
    baseline_bytes = baseline_path.read_bytes()
    candidate_bytes = candidate_path.read_bytes()
    baseline_contents_key = baseline_bytes.rindex(b"/Contents ")
    candidate_contents_key = candidate_bytes.rindex(b"/Contents ")
    baseline_contents_start = baseline_bytes.index(b"<", baseline_contents_key)
    candidate_contents_start = candidate_bytes.index(b"<", candidate_contents_key)
    baseline_contents_end = baseline_bytes.index(b">", baseline_contents_start) + 1
    candidate_contents_end = candidate_bytes.index(b">", candidate_contents_start) + 1

    assert baseline_path.stat().st_size == candidate_path.stat().st_size
    assert baseline_range[-2] + baseline_range[-1] == baseline_path.stat().st_size
    assert candidate_range[-2] + candidate_range[-1] == candidate_path.stat().st_size
    assert baseline_range[1:3] == (baseline_contents_start, baseline_contents_end)
    assert candidate_range[1:3] == (
        candidate_contents_start - 1,
        candidate_contents_end,
    )


def test_signature_direct_value_pair_keeps_coverage_and_indirects_one_value(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.direct_byte_range_values_required"

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    baseline = PdfReader(baseline_path, strict=True)
    candidate = PdfReader(candidate_path, strict=True)
    baseline_signature = baseline.root_object["/AcroForm"]["/Fields"][0]["/V"]
    candidate_signature = candidate.root_object["/AcroForm"]["/Fields"][0]["/V"]

    assert not isinstance(baseline_signature.raw_get("/Reason"), IndirectObject)
    assert isinstance(candidate_signature.raw_get("/Reason"), IndirectObject)
    for path, signature in (
        (baseline_path, baseline_signature),
        (candidate_path, candidate_signature),
    ):
        byte_range = tuple(int(value) for value in signature["/ByteRange"])
        document = path.read_bytes()
        contents_key = document.rindex(b"/Contents ")
        contents_start = document.index(b"<", contents_key)
        contents_end = document.index(b">", contents_start) + 1

        assert byte_range[0] == 0
        assert byte_range[-2] + byte_range[-1] == path.stat().st_size
        assert byte_range[1:3] == (contents_start, contents_end)


def test_signature_own_revision_coverage_pair_is_stale_but_distinguishable(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.own_revision_coverage_required"

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    baseline = PdfReader(baseline_path, strict=True)
    candidate = PdfReader(candidate_path, strict=True)
    baseline_signature = baseline.root_object["/AcroForm"]["/Fields"][0]["/V"]
    candidate_signature = candidate.root_object["/AcroForm"]["/Fields"][0]["/V"]
    baseline_endpoint = sum(
        int(value) for value in baseline_signature["/ByteRange"][-2:]
    )
    candidate_endpoint = sum(
        int(value) for value in candidate_signature["/ByteRange"][-2:]
    )

    def footer_endpoints(path):
        source = path.read_bytes()
        return {
            match.end()
            for match in re.finditer(
                rb"startxref\s+\d+\s+%%EOF(?:\r\n|\r|\n)?",
                source,
            )
        }

    assert baseline_endpoint < baseline_path.stat().st_size
    assert candidate_endpoint < candidate_path.stat().st_size
    assert baseline_endpoint in footer_endpoints(baseline_path)
    assert candidate_endpoint not in footer_endpoints(candidate_path)


def test_signature_terminal_footer_pair_rejects_unlinked_trailing_bytes(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.terminal_footer_required"

    def signature_endpoint(path):
        reader = PdfReader(path, strict=True)
        signature = reader.root_object["/AcroForm"]["/Fields"][0]["/V"]
        byte_range = tuple(int(value) for value in signature["/ByteRange"])
        return sum(byte_range[-2:])

    def footer_endpoints(path):
        return {
            match.end()
            for match in re.finditer(
                rb"startxref\s+\d+\s+%%EOF(?:\r\n|\r|\n)?",
                path.read_bytes(),
            )
        }

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    baseline_footer_endpoints = footer_endpoints(baseline_path)
    candidate_footer_endpoints = footer_endpoints(candidate_path)

    assert signature_endpoint(baseline_path) < baseline_path.stat().st_size
    assert signature_endpoint(candidate_path) < candidate_path.stat().st_size
    assert signature_endpoint(baseline_path) in baseline_footer_endpoints
    assert signature_endpoint(candidate_path) in candidate_footer_endpoints
    assert max(baseline_footer_endpoints) == baseline_path.stat().st_size
    assert max(candidate_footer_endpoints) < candidate_path.stat().st_size
    assert candidate_path.read_bytes().endswith(b"UNLINKED_TRAILING_BYTES")


def test_terminal_revision_footer_pair_rejects_unlinked_trailing_bytes(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "review.terminal_footer_required"

    def footer_endpoints(path):
        return {
            match.end()
            for match in re.finditer(
                rb"startxref\s+\d+\s+%%EOF(?:\r\n|\r|\n)?",
                path.read_bytes(),
            )
        }

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    assert PdfReader(baseline_path, strict=True).pages
    assert PdfReader(candidate_path, strict=True).pages
    assert max(footer_endpoints(baseline_path)) == baseline_path.stat().st_size
    assert max(footer_endpoints(candidate_path)) < candidate_path.stat().st_size
    assert candidate_path.read_bytes().endswith(b"UNLINKED_TRAILING_BYTES")


def test_signature_contents_bound_own_revision_pair_is_stale_but_precise(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.contents_bound_own_revision_coverage_required"

    def signature_range(path):
        reader = PdfReader(path, strict=True)
        signature = reader.root_object["/AcroForm"]["/Fields"][0]["/V"]
        return tuple(int(value) for value in signature["/ByteRange"])

    def footer_endpoints(path):
        source = path.read_bytes()
        return {
            match.end()
            for match in re.finditer(
                rb"startxref\s+\d+\s+%%EOF(?:\r\n|\r|\n)?",
                source,
            )
        }

    baseline_path = fixture / "baseline.pdf"
    candidate_path = fixture / "candidate.pdf"
    baseline_range = signature_range(baseline_path)
    candidate_range = signature_range(candidate_path)
    baseline_bytes = baseline_path.read_bytes()
    candidate_bytes = candidate_path.read_bytes()
    baseline_contents_key = baseline_bytes.rindex(b"/Contents ")
    candidate_contents_key = candidate_bytes.rindex(b"/Contents ")
    baseline_contents_start = baseline_bytes.index(b"<", baseline_contents_key)
    candidate_contents_start = candidate_bytes.index(b"<", candidate_contents_key)
    baseline_contents_end = baseline_bytes.index(b">", baseline_contents_start) + 1
    candidate_contents_end = candidate_bytes.index(b">", candidate_contents_start) + 1
    baseline_endpoint = sum(baseline_range[-2:])
    candidate_endpoint = sum(candidate_range[-2:])

    assert baseline_endpoint < baseline_path.stat().st_size
    assert candidate_endpoint < candidate_path.stat().st_size
    assert baseline_endpoint in footer_endpoints(baseline_path)
    assert candidate_endpoint in footer_endpoints(candidate_path)
    assert baseline_range[1:3] == (baseline_contents_start, baseline_contents_end)
    assert candidate_range[1:3] == (
        candidate_contents_start - 1,
        candidate_contents_end,
    )


def test_private_signature_lookalike_pair_has_no_semantic_signature_owner(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "signature.private_piece_info_lookalike_added"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    assert "/AcroForm" not in baseline.root_object
    assert "/AcroForm" not in candidate.root_object
    assert "/Perms" not in baseline.root_object
    assert "/Perms" not in candidate.root_object
    baseline_private = baseline.root_object["/PieceInfo"]["/PDFCAB"]["/Private"]
    candidate_private = candidate.root_object["/PieceInfo"]["/PDFCAB"]["/Private"]
    assert "/Signature" not in baseline_private
    candidate_signature = candidate_private["/Signature"].get_object()
    assert str(candidate_signature["/Type"]) == "/Sig"
    assert tuple(int(value) for value in candidate_signature["/ByteRange"]) == (0, 1)


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


def test_document_part_destination_pairs_are_semantic(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)

    def action(reader: PdfReader, *, action_chain: bool):
        root_action = reader.root_object["/OpenAction"].get_object()
        if not action_chain:
            return root_action
        assert str(root_action["/S"]) == "/JavaScript"
        return root_action["/Next"].get_object()

    def targets(reader: PdfReader):
        document_part_root = reader.root_object["/DPartRoot"].get_object()
        root = document_part_root["/DPartRootNode"].get_object()
        group = root["/DParts"][0][0].get_object()
        leaves = (
            group["/DParts"][0][0],
            group["/DParts"][1][0],
        )
        assert str(document_part_root["/Type"]) == "/DPartRoot"
        assert str(root["/Type"]) == str(group["/Type"]) == "/DPart"
        assert all(
            str(leaf.get_object()["/Type"]) == "/DPart" for leaf in leaves
        )
        return leaves

    for fixture_id, action_chain in (
        ("active.goto_document_part_rebound", False),
        ("active.action_chain_document_part_rebound", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_targets = targets(baseline)
        candidate_targets = targets(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/GoToDp"
        assert baseline_action.raw_get(NameObject("/Dp")) == baseline_targets[0]
        assert candidate_action.raw_get(NameObject("/Dp")) == candidate_targets[1]

    for fixture_id, action_chain in (
        ("active.goto_document_part_target_metadata_rewritten", False),
        ("active.action_chain_document_part_target_metadata_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_targets = targets(baseline)
        candidate_targets = targets(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert baseline_action.raw_get(NameObject("/Dp")) == baseline_targets[0]
        assert candidate_action.raw_get(NameObject("/Dp")) == candidate_targets[0]
        assert (
            str(baseline_targets[0].get_object()["/DPM"]["/Private"])
            != str(candidate_targets[0].get_object()["/DPM"]["/Private"])
        )

    for fixture_id, action_chain in (
        ("active.goto_document_part_target_page_rotated", False),
        ("active.action_chain_document_part_target_page_rotated", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_targets = targets(baseline)
        candidate_targets = targets(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert baseline_action.raw_get(NameObject("/Dp")) == baseline_targets[0]
        assert candidate_action.raw_get(NameObject("/Dp")) == candidate_targets[0]
        assert int(baseline.pages[0]["/Rotate"]) == 0
        assert int(candidate.pages[0]["/Rotate"]) == 90


def test_goto_3d_view_pairs_are_semantic(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)

    def action(reader: PdfReader, *, action_chain: bool):
        root_action = reader.root_object["/OpenAction"].get_object()
        if not action_chain:
            return root_action
        assert str(root_action["/S"]) == "/JavaScript"
        return root_action["/Next"].get_object()

    def targets(reader: PdfReader, *, target_page_reference: bool = True):
        page = reader.pages[0]
        annotations = tuple(page["/Annots"])
        assert len(annotations) == 2
        for annotation in annotations:
            target = annotation.get_object()
            assert str(target["/Type"]) == "/Annot"
            assert str(target["/Subtype"]) == "/3D"
            if target_page_reference:
                assert target.raw_get(NameObject("/P")) == page.indirect_reference
            else:
                assert NameObject("/P") not in target
            model = target["/3DD"].get_object()
            assert str(model["/Type"]) == "/3D"
            assert str(model["/Subtype"]) == "/U3D"
        return annotations

    for fixture_id, action_chain in (
        ("active.goto_3d_view_target_rebound", False),
        ("active.action_chain_goto_3d_view_target_rebound", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_targets = targets(baseline, target_page_reference=False)
        candidate_targets = targets(candidate, target_page_reference=False)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert (
            str(baseline_action["/S"])
            == str(candidate_action["/S"])
            == "/GoTo3DView"
        )
        assert baseline_action.raw_get(NameObject("/TA")) == baseline_targets[0]
        assert candidate_action.raw_get(NameObject("/TA")) == candidate_targets[1]
        assert str(baseline_action["/V"]) == str(candidate_action["/V"]) == "/D"

    for fixture_id, action_chain in (
        ("active.goto_3d_view_view_rewritten", False),
        ("active.action_chain_goto_3d_view_view_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_targets = targets(baseline)
        candidate_targets = targets(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert baseline_action.raw_get(NameObject("/TA")) == baseline_targets[0]
        assert candidate_action.raw_get(NameObject("/TA")) == candidate_targets[0]
        assert str(baseline_action["/V"]) == "/D"
        assert str(candidate_action["/V"]) == "/F"

    for fixture_id, action_chain in (
        ("active.goto_3d_view_target_metadata_rewritten", False),
        ("active.action_chain_goto_3d_view_target_metadata_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_targets = targets(baseline)
        candidate_targets = targets(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert baseline_action.raw_get(NameObject("/TA")) == baseline_targets[0]
        assert candidate_action.raw_get(NameObject("/TA")) == candidate_targets[0]
        assert (
            baseline_targets[0].get_object()["/Contents"]
            != candidate_targets[0].get_object()["/Contents"]
        )

    for fixture_id, action_chain in (
        ("active.goto_3d_view_target_page_rotated", False),
        ("active.action_chain_goto_3d_view_target_page_rotated", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_targets = targets(baseline)
        candidate_targets = targets(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert baseline_action.raw_get(NameObject("/TA")) == baseline_targets[0]
        assert candidate_action.raw_get(NameObject("/TA")) == candidate_targets[0]
        assert int(baseline.pages[0]["/Rotate"]) == 0
        assert int(candidate.pages[0]["/Rotate"]) == 90


def test_embedded_goto_named_target_pairs_are_semantic(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)

    def action(reader: PdfReader, *, action_chain: bool):
        root_action = reader.root_object["/OpenAction"].get_object()
        if not action_chain:
            return root_action
        assert str(root_action["/S"]) == "/JavaScript"
        return root_action["/Next"].get_object()

    def named_file_specifications(reader: PdfReader) -> dict[str, object]:
        entries = reader.root_object["/Names"]["/EmbeddedFiles"]["/Names"]
        assert len(entries) == 4
        result: dict[str, object] = {}
        for index in range(0, len(entries), 2):
            file_specification = entries[index + 1]
            if isinstance(file_specification, IndirectObject):
                file_specification = file_specification.get_object()
            result[str(entries[index])] = file_specification
        return result

    def selected_file_specification(reader: PdfReader, goto: object) -> object:
        target = goto["/T"]
        assert str(target["/R"]) == "/C"
        return named_file_specifications(reader)[str(target["/N"])]

    def stored_embedded_file_data(file_specification: object) -> bytes:
        stream = file_specification["/EF"]["/F"]
        if isinstance(stream, IndirectObject):
            stream = stream.get_object()
        return bytes(stream._data)

    for fixture_id, action_chain in (
        ("active.embedded_goto_named_target_rebound", False),
        ("active.action_chain_embedded_goto_named_target_rebound", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/GoToE"
        assert str(baseline_action["/D"]) == str(candidate_action["/D"])
        assert str(baseline_action["/T"]["/N"]) == str(
            candidate_action["/T"]["/N"]
        )
        baseline_file = selected_file_specification(baseline, baseline_action)
        candidate_file = selected_file_specification(candidate, candidate_action)
        assert str(baseline_file["/F"]) == str(candidate_file["/F"])
        assert str(baseline_file["/Desc"]) == str(candidate_file["/Desc"])
        assert stored_embedded_file_data(baseline_file) != stored_embedded_file_data(
            candidate_file
        )

    for fixture_id, action_chain in (
        (
            "active.embedded_goto_selected_file_specification_metadata_rewritten",
            False,
        ),
        (
            "active.action_chain_embedded_goto_selected_file_specification_metadata_rewritten",
            True,
        ),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)
        baseline_file = selected_file_specification(baseline, baseline_action)
        candidate_file = selected_file_specification(candidate, candidate_action)

        assert str(baseline_file["/F"]) == str(candidate_file["/F"])
        assert str(baseline_file["/Desc"]) != str(candidate_file["/Desc"])

    for fixture_id, action_chain in (
        ("active.embedded_goto_unrelated_named_target_rewritten", False),
        ("active.action_chain_embedded_goto_unrelated_named_target_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)
        baseline_files = named_file_specifications(baseline)
        candidate_files = named_file_specifications(candidate)

        selected_name = str(baseline_action["/T"]["/N"])
        assert selected_name == str(candidate_action["/T"]["/N"])
        assert str(baseline_files[selected_name]["/F"]) == str(
            candidate_files[selected_name]["/F"]
        )
        assert str(baseline_files["PDFCAB_UNRELATED_CHILD"]["/F"]) != str(
            candidate_files["PDFCAB_UNRELATED_CHILD"]["/F"]
        )

    for fixture_id, action_chain in (
        ("active.embedded_goto_root_file_specification_metadata_rewritten", False),
        (
            "active.action_chain_embedded_goto_root_file_specification_metadata_rewritten",
            True,
        ),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_file = action(baseline, action_chain=action_chain)["/F"]
        candidate_file = action(candidate, action_chain=action_chain)["/F"]

        assert str(baseline_file["/F"]) == str(candidate_file["/F"])
        assert str(baseline_file["/Desc"]) != str(candidate_file["/Desc"])

    for fixture_id, action_chain in (
        ("active.embedded_goto_root_file_target_rewritten", False),
        ("active.action_chain_embedded_goto_root_file_target_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_file = action(baseline, action_chain=action_chain)["/F"]
        candidate_file = action(candidate, action_chain=action_chain)["/F"]

        assert str(baseline_file["/F"]) != str(candidate_file["/F"])
        assert str(baseline_file["/Desc"]) == str(candidate_file["/Desc"])


def test_embedded_goto_file_attachment_target_pairs_are_semantic(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)

    def action(reader: PdfReader, *, action_chain: bool):
        root_action = reader.root_object["/OpenAction"].get_object()
        if not action_chain:
            return root_action
        assert str(root_action["/S"]) == "/JavaScript"
        return root_action["/Next"].get_object()

    def selected_annotation(reader: PdfReader, goto: object) -> object:
        target = goto["/T"]
        page_selector = target["/P"]
        if isinstance(page_selector, NumberObject):
            page = reader.pages[int(page_selector)]
        else:
            entries = reader.root_object["/Names"]["/Dests"]["/Names"]
            destinations = {
                str(entries[index]): entries[index + 1]
                for index in range(0, len(entries), 2)
            }
            destination = destinations[str(page_selector)]
            page = destination[0].get_object()
        annotation_selector = target["/A"]
        annotations = page["/Annots"]
        if isinstance(annotation_selector, NumberObject):
            return annotations[int(annotation_selector)].get_object()
        matches = [
            candidate.get_object()
            for candidate in annotations
            if str(candidate.get_object()["/NM"]) == str(annotation_selector)
        ]
        assert len(matches) == 1
        return matches[0]

    def stored_embedded_file_data(annotation: object) -> bytes:
        file_specification = annotation["/FS"]
        stream = file_specification["/EF"]["/F"]
        if isinstance(stream, IndirectObject):
            stream = stream.get_object()
        return bytes(stream._data)

    for fixture_id, action_chain in (
        ("active.embedded_goto_file_attachment_index_target_rebound", False),
        (
            "active.action_chain_embedded_goto_file_attachment_index_target_rebound",
            True,
        ),
        (
            "active.embedded_goto_file_attachment_named_annotation_target_rebound",
            False,
        ),
        (
            "active.action_chain_embedded_goto_file_attachment_named_annotation_target_rebound",
            True,
        ),
        ("active.embedded_goto_file_attachment_named_page_target_rebound", False),
        (
            "active.action_chain_embedded_goto_file_attachment_named_page_target_rebound",
            True,
        ),
        ("active.embedded_goto_file_attachment_named_target_rebound", False),
        (
            "active.action_chain_embedded_goto_file_attachment_named_target_rebound",
            True,
        ),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)
        baseline_target = baseline_action["/T"]
        candidate_target = candidate_action["/T"]

        assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/GoToE"
        assert str(baseline_action["/D"]) == str(candidate_action["/D"])
        assert str(baseline_target["/R"]) == str(candidate_target["/R"]) == "/C"
        assert NameObject("/N") not in baseline_target
        assert NameObject("/N") not in candidate_target
        assert str(baseline_target["/P"]) == str(candidate_target["/P"])
        assert str(baseline_target["/A"]) == str(candidate_target["/A"])

        baseline_annotation = selected_annotation(baseline, baseline_action)
        candidate_annotation = selected_annotation(candidate, candidate_action)
        assert str(baseline_annotation["/Subtype"]) == "/FileAttachment"
        assert str(candidate_annotation["/Subtype"]) == "/FileAttachment"
        assert str(baseline_annotation["/FS"]["/F"]) == str(
            candidate_annotation["/FS"]["/F"]
        )
        assert str(baseline_annotation["/FS"]["/Desc"]) == str(
            candidate_annotation["/FS"]["/Desc"]
        )
        assert stored_embedded_file_data(
            baseline_annotation
        ) != stored_embedded_file_data(candidate_annotation)

    for fixture_id, action_chain in (
        (
            "active.embedded_goto_file_attachment_file_specification_metadata_rewritten",
            False,
        ),
        (
            "active.action_chain_embedded_goto_file_attachment_file_specification_metadata_rewritten",
            True,
        ),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_annotation = selected_annotation(
            baseline,
            action(baseline, action_chain=action_chain),
        )
        candidate_annotation = selected_annotation(
            candidate,
            action(candidate, action_chain=action_chain),
        )

        assert str(baseline_annotation["/FS"]["/F"]) == str(
            candidate_annotation["/FS"]["/F"]
        )
        assert str(baseline_annotation["/FS"]["/Desc"]) != str(
            candidate_annotation["/FS"]["/Desc"]
        )

    for fixture_id, action_chain in (
        (
            "active.embedded_goto_file_attachment_annotation_metadata_rewritten",
            False,
        ),
        (
            "active.action_chain_embedded_goto_file_attachment_annotation_metadata_rewritten",
            True,
        ),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_annotation = selected_annotation(
            baseline,
            action(baseline, action_chain=action_chain),
        )
        candidate_annotation = selected_annotation(
            candidate,
            action(candidate, action_chain=action_chain),
        )

        assert str(baseline_annotation["/Contents"]) != str(
            candidate_annotation["/Contents"]
        )
        assert stored_embedded_file_data(
            baseline_annotation
        ) == stored_embedded_file_data(candidate_annotation)


def test_embedded_goto_other_document_name_tree_pairs_are_semantic(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)

    def action(reader: PdfReader, *, action_chain: bool):
        root_action = reader.root_object["/OpenAction"].get_object()
        if not action_chain:
            return root_action
        assert str(root_action["/S"]) == "/JavaScript"
        return root_action["/Next"].get_object()

    def named_file_specifications(reader: PdfReader) -> dict[str, object]:
        entries = reader.root_object["/Names"]["/EmbeddedFiles"]["/Names"]
        result: dict[str, object] = {}
        for index in range(0, len(entries), 2):
            file_specification = entries[index + 1]
            if isinstance(file_specification, IndirectObject):
                file_specification = file_specification.get_object()
            result[str(entries[index])] = file_specification
        return result

    def stored_embedded_file_data(file_specification: object) -> bytes:
        stream = file_specification["/EF"]["/F"]
        if isinstance(stream, IndirectObject):
            stream = stream.get_object()
        return bytes(stream._data)

    for fixture_id, action_chain, nested in (
        ("active.embedded_goto_external_root_named_target_rewritten", False, False),
        (
            "active.action_chain_embedded_goto_external_root_named_target_rewritten",
            True,
            False,
        ),
        ("active.embedded_goto_nested_named_target_rewritten", False, True),
        (
            "active.action_chain_embedded_goto_nested_named_target_rewritten",
            True,
            True,
        ),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)
        baseline_target = baseline_action["/T"]
        candidate_target = candidate_action["/T"]

        assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/GoToE"
        assert str(baseline_action["/D"]) == str(candidate_action["/D"])
        assert str(baseline_target["/R"]) == str(candidate_target["/R"]) == "/C"
        assert str(baseline_target["/N"]) == str(candidate_target["/N"])

        baseline_files = named_file_specifications(baseline)
        candidate_files = named_file_specifications(candidate)
        if nested:
            assert str(baseline_target["/N"]) == "PDFCAB_EMBEDDED_PARENT"
            assert str(candidate_target["/N"]) == "PDFCAB_EMBEDDED_PARENT"
            assert str(baseline_target["/T"]["/N"]) == str(
                candidate_target["/T"]["/N"]
            )
            assert stored_embedded_file_data(
                baseline_files["PDFCAB_EMBEDDED_PARENT"]
            ) == stored_embedded_file_data(
                candidate_files["PDFCAB_EMBEDDED_PARENT"]
            )
            changed_name = "PDFCAB_EMBEDDED_NESTED_CHILD"
        else:
            assert "/F" in baseline_action
            assert "/F" in candidate_action
            assert str(baseline_action["/F"]["/F"]) == str(
                candidate_action["/F"]["/F"]
            )
            changed_name = str(baseline_target["/N"])
        assert stored_embedded_file_data(
            baseline_files[changed_name]
        ) != stored_embedded_file_data(candidate_files[changed_name])


def test_set_ocg_state_pairs_are_semantic(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)

    def action(reader: PdfReader, *, action_chain: bool):
        root_action = reader.root_object["/OpenAction"].get_object()
        if not action_chain:
            return root_action
        assert str(root_action["/S"]) == "/JavaScript"
        return root_action["/Next"].get_object()

    def groups(reader: PdfReader):
        properties = reader.root_object["/OCProperties"]
        catalog_groups = tuple(properties["/OCGs"])
        radio_button_groups = properties["/D"]["/RBGroups"]
        assert len(catalog_groups) == 2
        assert len(radio_button_groups) == 1
        assert tuple(radio_button_groups[0]) == catalog_groups
        assert all(
            str(group.get_object()["/Type"]) == "/OCG"
            for group in catalog_groups
        )
        return catalog_groups

    for fixture_id, action_chain in (
        ("active.set_ocg_state_group_rebound", False),
        ("active.action_chain_set_ocg_state_group_rebound", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_groups = groups(baseline)
        candidate_groups = groups(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert str(baseline_action["/S"]) == "/SetOCGState"
        assert str(candidate_action["/S"]) == "/SetOCGState"
        assert str(baseline_action["/State"][0]) == "/ON"
        assert str(candidate_action["/State"][0]) == "/ON"
        assert baseline_action["/State"][1] == baseline_groups[0]
        assert candidate_action["/State"][1] == candidate_groups[1]

    for fixture_id, action_chain in (
        ("active.set_ocg_state_operation_rewritten", False),
        ("active.action_chain_set_ocg_state_operation_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_groups = groups(baseline)
        candidate_groups = groups(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert str(baseline_action["/State"][0]) == "/ON"
        assert str(candidate_action["/State"][0]) == "/OFF"
        assert baseline_action["/State"][1] == baseline_groups[0]
        assert candidate_action["/State"][1] == candidate_groups[0]

    for fixture_id, action_chain in (
        ("active.set_ocg_state_preserve_rb_rewritten", False),
        ("active.action_chain_set_ocg_state_preserve_rb_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert str(baseline_action["/PreserveRB"]).lower() == "true"
        assert str(candidate_action["/PreserveRB"]).lower() == "false"

    for fixture_id, action_chain in (
        ("active.set_ocg_state_group_metadata_rewritten", False),
        ("active.action_chain_set_ocg_state_group_metadata_rewritten", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_groups = groups(baseline)
        candidate_groups = groups(candidate)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert baseline_action["/State"][1] == baseline_groups[0]
        assert candidate_action["/State"][1] == candidate_groups[0]
        assert str(baseline_groups[0].get_object()["/Name"]) != str(
            candidate_groups[0].get_object()["/Name"]
        )

    for fixture_id, action_chain in (
        ("active.set_ocg_state_preserve_rb_explicit_default", False),
        ("active.action_chain_set_ocg_state_preserve_rb_explicit_default", True),
    ):
        fixture = generated / fixture_id
        baseline = PdfReader(fixture / "baseline.pdf", strict=True)
        candidate = PdfReader(fixture / "candidate.pdf", strict=True)
        baseline_action = action(baseline, action_chain=action_chain)
        candidate_action = action(candidate, action_chain=action_chain)

        assert "/PreserveRB" not in baseline_action
        assert str(candidate_action["/PreserveRB"]).lower() == "true"


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


def test_remote_goto_structure_destination_pairs_preserve_sd_precedence(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    rebound = generated / "active.remote_goto_structure_destination_rebound"
    fallback = (
        generated / "active.remote_goto_structure_destination_fallback_rewritten"
    )
    reencoded = generated / "active.remote_goto_structure_destination_reencoded"
    destination = generated / "active.remote_goto_destination_rewritten"

    before = PdfReader(rebound / "baseline.pdf", strict=True)
    after = PdfReader(rebound / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"].get_object()
    after_action = after.root_object["/OpenAction"].get_object()
    assert str(before_action["/S"]) == str(after_action["/S"]) == "/GoToR"
    assert str(before_action["/F"]["/Type"]) == "/Filespec"
    assert str(after_action["/F"]["/Type"]) == "/Filespec"
    assert before_action["/D"][0] == after_action["/D"][0] == 0
    assert before_action["/SD"][0].original_bytes == b"PDFCAB_REMOTE_STRUCTURE_A"
    assert after_action["/SD"][0].original_bytes == b"PDFCAB_REMOTE_STRUCTURE_B"
    assert str(before_action["/SD"][1]) == str(after_action["/SD"][1]) == "/Fit"

    before = PdfReader(reencoded / "baseline.pdf", strict=True)
    after = PdfReader(reencoded / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"].get_object()
    after_action = after.root_object["/OpenAction"].get_object()
    assert str(before_action["/SD"][0]) == str(after_action["/SD"][0]) == "A"
    assert before_action["/SD"][0].original_bytes == b"\xfe\xff\x00A"
    assert after_action["/SD"][0].original_bytes == b"\xff\xfeA\x00"

    before = PdfReader(fallback / "baseline.pdf", strict=True)
    after = PdfReader(fallback / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"].get_object()
    after_action = after.root_object["/OpenAction"].get_object()
    assert before_action["/D"][0] == 0
    assert after_action["/D"][0] == 1
    assert (
        before_action["/SD"][0].original_bytes
        == after_action["/SD"][0].original_bytes
    )

    before = PdfReader(destination / "baseline.pdf", strict=True)
    after = PdfReader(destination / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"].get_object()
    after_action = after.root_object["/OpenAction"].get_object()
    assert "/SD" not in before_action
    assert "/SD" not in after_action
    assert before_action["/D"][0] == 0
    assert after_action["/D"][0] == 1


def test_remote_goto_structure_destination_action_chain_pairs_are_semantic(
    tmp_path,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    rebound = (
        generated / "active.action_chain_remote_goto_structure_destination_rebound"
    )
    fallback = generated / (
        "active.action_chain_remote_goto_structure_destination_fallback_rewritten"
    )

    before = PdfReader(rebound / "baseline.pdf", strict=True)
    after = PdfReader(rebound / "candidate.pdf", strict=True)
    before_root = before.root_object["/OpenAction"].get_object()
    after_root = after.root_object["/OpenAction"].get_object()
    before_action = before_root["/Next"].get_object()
    after_action = after_root["/Next"].get_object()
    assert str(before_root["/S"]) == str(after_root["/S"]) == "/JavaScript"
    assert str(before_action["/S"]) == str(after_action["/S"]) == "/GoToR"
    assert before_action["/D"][0] == after_action["/D"][0] == 0
    assert before_action["/SD"][0].original_bytes == b"PDFCAB_REMOTE_STRUCTURE_A"
    assert after_action["/SD"][0].original_bytes == b"PDFCAB_REMOTE_STRUCTURE_B"

    before = PdfReader(fallback / "baseline.pdf", strict=True)
    after = PdfReader(fallback / "candidate.pdf", strict=True)
    before_action = before.root_object["/OpenAction"]["/Next"].get_object()
    after_action = after.root_object["/OpenAction"]["/Next"].get_object()
    assert before_action["/D"][0] == 0
    assert after_action["/D"][0] == 1
    assert (
        before_action["/SD"][0].original_bytes
        == after_action["/SD"][0].original_bytes
    )


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
    ("fixture_id", "action_type"),
    (
        ("active.thread_destination_rewritten", "/Thread"),
        ("active.uri_is_map_rewritten", "/URI"),
        ("active.sound_stream_rewritten", "/Sound"),
        ("active.movie_title_rewritten", "/Movie"),
        ("active.hide_target_rewritten", "/Hide"),
        ("active.named_action_rewritten", "/Named"),
        ("active.submit_form_charset_rewritten", "/SubmitForm"),
        ("active.reset_form_fields_rewritten", "/ResetForm"),
        ("active.rendition_javascript_rewritten", "/Rendition"),
        ("active.transition_rewritten", "/Trans"),
        ("active.rich_media_command_rewritten", "/RichMediaExecute"),
    ),
)
def test_direct_action_field_pairs_rewrite_selected_semantics(
    tmp_path,
    fixture_id,
    action_type,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_action = baseline.root_object["/OpenAction"].get_object()
    candidate_action = candidate.root_object["/OpenAction"].get_object()

    assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == action_type
    assert _direct_action_behavior_value(
        baseline_action,
        action_type,
    ) != _direct_action_behavior_value(candidate_action, action_type)


@pytest.mark.parametrize(
    ("fixture_id", "action_type"),
    (
        ("active.passive_piece_info_thread_destination_rewritten", "/Thread"),
        ("active.passive_piece_info_uri_is_map_rewritten", "/URI"),
        ("active.passive_piece_info_sound_stream_rewritten", "/Sound"),
        ("active.passive_piece_info_movie_title_rewritten", "/Movie"),
        ("active.passive_piece_info_hide_target_rewritten", "/Hide"),
        ("active.passive_piece_info_named_action_rewritten", "/Named"),
        ("active.passive_piece_info_submit_form_charset_rewritten", "/SubmitForm"),
        ("active.passive_piece_info_reset_form_fields_rewritten", "/ResetForm"),
        ("active.passive_piece_info_rendition_javascript_rewritten", "/Rendition"),
        ("active.passive_piece_info_transition_rewritten", "/Trans"),
        (
            "active.passive_piece_info_rich_media_command_rewritten",
            "/RichMediaExecute",
        ),
    ),
)
def test_piece_info_action_field_pairs_keep_behavior_passive(
    tmp_path,
    fixture_id,
    action_type,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    assert "/OpenAction" not in baseline.root_object
    assert "/OpenAction" not in candidate.root_object
    baseline_action = baseline.root_object["/PieceInfo"]["/PDFCAB"]["/Private"][
        "/Action"
    ].get_object()
    candidate_action = candidate.root_object["/PieceInfo"]["/PDFCAB"]["/Private"][
        "/Action"
    ].get_object()

    assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == action_type
    assert _direct_action_behavior_value(
        baseline_action,
        action_type,
    ) != _direct_action_behavior_value(candidate_action, action_type)


@pytest.mark.parametrize(
    ("fixture_id", "trigger"),
    (
        ("active.passive_piece_info_direct_action_rewritten", "/A"),
        ("active.passive_piece_info_additional_action_rewritten", "/AA"),
        ("active.passive_piece_info_navigation_next_action_rewritten", "/NA"),
        (
            "active.passive_piece_info_navigation_previous_action_rewritten",
            "/PA",
        ),
    ),
)
def test_piece_info_action_trigger_lookalike_pairs_stay_off_execution_paths(
    tmp_path,
    fixture_id,
    trigger,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    assert "/OpenAction" not in baseline.root_object
    assert "/OpenAction" not in candidate.root_object
    baseline_private = baseline.root_object["/PieceInfo"]["/PDFCAB"]["/Private"]
    candidate_private = candidate.root_object["/PieceInfo"]["/PDFCAB"]["/Private"]
    if trigger == "/AA":
        baseline_action = baseline_private["/AA"]["/O"].get_object()
        candidate_action = candidate_private["/AA"]["/O"].get_object()
    else:
        baseline_action = baseline_private[trigger].get_object()
        candidate_action = candidate_private[trigger].get_object()

    assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/URI"
    assert _direct_action_behavior_value(
        baseline_action,
        "/URI",
    ) != _direct_action_behavior_value(candidate_action, "/URI")
    if trigger == "/A":
        assert str(baseline_private["/Type"]) == "/Annot"
        assert str(baseline_private["/Subtype"]) == "/Link"
    elif trigger in {"/NA", "/PA"}:
        assert str(baseline_private["/Type"]) == "/NavNode"


@pytest.mark.parametrize(
    ("fixture_id", "location", "baseline_action", "candidate_action"),
    (
        (
            "active.passive_piece_info_action_inventory_rewritten",
            "action",
            "/URI",
            "/JavaScript",
        ),
        (
            "active.passive_piece_info_additional_action_inventory_added",
            "additional",
            None,
            "/URI",
        ),
    ),
)
def test_piece_info_action_inventory_pairs_stay_outside_semantic_roots(
    tmp_path,
    fixture_id,
    location,
    baseline_action,
    candidate_action,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    assert "/OpenAction" not in baseline.root_object
    assert "/OpenAction" not in candidate.root_object
    baseline_private = baseline.root_object["/PieceInfo"]["/PDFCAB"]["/Private"]
    candidate_private = candidate.root_object["/PieceInfo"]["/PDFCAB"]["/Private"]
    if location == "action":
        baseline_value = baseline_private["/Action"].get_object()
        candidate_value = candidate_private["/Action"].get_object()
        assert str(baseline_value["/S"]) == baseline_action
    else:
        assert "/AA" not in baseline_private
        candidate_value = candidate_private["/AA"]["/O"].get_object()
    assert str(candidate_value["/S"]) == candidate_action


def test_link_archived_uri_action_pair_is_not_a_navigation_node_trigger(tmp_path):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / "active.link_archived_uri_action_rewritten"

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    baseline_annotation = baseline.pages[0]["/Annots"][0].get_object()
    candidate_annotation = candidate.pages[0]["/Annots"][0].get_object()
    assert "/A" not in baseline_annotation
    assert "/A" not in candidate_annotation
    baseline_action = baseline_annotation["/PA"].get_object()
    candidate_action = candidate_annotation["/PA"].get_object()

    assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/URI"
    assert str(baseline_action["/URI"]) != str(candidate_action["/URI"])


@pytest.mark.parametrize(
    ("fixture_id", "root"),
    (
        ("active.page_additional_uri_rewritten", "page_additional"),
        ("active.link_direct_uri_rewritten", "link_direct"),
        ("active.field_additional_uri_rewritten", "field_additional"),
        ("active.outline_direct_uri_rewritten", "outline_direct"),
        ("active.navigation_node_next_uri_rewritten", "navigation_next"),
        (
            "active.navigation_node_previous_uri_rewritten",
            "navigation_previous",
        ),
    ),
)
def test_semantic_uri_action_root_pairs_use_standard_execution_paths(
    tmp_path,
    fixture_id,
    root,
):
    generated = tmp_path / "generated"
    build_fixture_tree(generated)
    fixture = generated / fixture_id

    baseline = PdfReader(fixture / "baseline.pdf", strict=True)
    candidate = PdfReader(fixture / "candidate.pdf", strict=True)
    assert "/OpenAction" not in baseline.root_object
    assert "/OpenAction" not in candidate.root_object
    if root == "page_additional":
        baseline_action = baseline.pages[0]["/AA"]["/O"].get_object()
        candidate_action = candidate.pages[0]["/AA"]["/O"].get_object()
    elif root == "link_direct":
        baseline_action = (
            baseline.pages[0]["/Annots"][0].get_object()["/A"].get_object()
        )
        candidate_action = (
            candidate.pages[0]["/Annots"][0].get_object()["/A"].get_object()
        )
    elif root == "field_additional":
        baseline_action = baseline.root_object["/AcroForm"]["/Fields"][
            0
        ].get_object()["/AA"]["/K"].get_object()
        candidate_action = candidate.root_object["/AcroForm"]["/Fields"][
            0
        ].get_object()["/AA"]["/K"].get_object()
    elif root == "outline_direct":
        baseline_action = baseline.root_object["/Outlines"]["/First"].get_object()[
            "/A"
        ].get_object()
        candidate_action = candidate.root_object["/Outlines"]["/First"].get_object()[
            "/A"
        ].get_object()
    else:
        key = "/NA" if root == "navigation_next" else "/PA"
        baseline_action = baseline.pages[0]["/PresSteps"].get_object()[
            key
        ].get_object()
        candidate_action = candidate.pages[0]["/PresSteps"].get_object()[
            key
        ].get_object()

    assert str(baseline_action["/S"]) == str(candidate_action["/S"]) == "/URI"
    assert str(baseline_action["/URI"]) != str(candidate_action["/URI"])


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


def _direct_action_behavior_value(action: object, action_type: str) -> object:
    if action_type == "/Thread":
        return str(action["/D"])
    if action_type in {"/Movie", "/Hide"}:
        return str(action["/T"])
    if action_type == "/URI":
        return str(action["/IsMap"])
    if action_type == "/Sound":
        return action["/Sound"].get_object().get_data()
    if action_type == "/Named":
        return str(action["/N"])
    if action_type == "/SubmitForm":
        return str(action["/CharSet"])
    if action_type == "/ResetForm":
        return str(action["/Fields"][0])
    if action_type == "/Rendition":
        return str(action["/JS"])
    if action_type == "/Trans":
        return str(action["/Trans"]["/S"])
    if action_type == "/RichMediaExecute":
        return str(action["/CMD"]["/C"])
    raise AssertionError("unsupported direct action field")


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
