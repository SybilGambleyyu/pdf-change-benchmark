"""Deterministic source for PDFCAB's synthetic paired-PDF fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    IndirectObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

from pdfcab.errors import FixtureError
from pdfcab.models import FixtureTruth

FIXTURE_SCHEMA_VERSION = 1
_MARKER_A = "PDFCAB_INERT_A"
_MARKER_B = "PDFCAB_INERT_B"
_MARKER_C = "PDFCAB_INERT_C"
_URI = "https://example.invalid/pdfcab"
_URI_B = "https://example.invalid/pdfcab-b"
_JAVASCRIPT_STREAM_RAW = b"41>0"
_JAVASCRIPT_STREAM_FILTER = "/ASCIIHexDecode"
_LAUNCH_TARGET_A = "PDFCAB_LAUNCH_A.txt"
_LAUNCH_TARGET_B = "PDFCAB_LAUNCH_B.txt"
_REMOTE_GOTO_TARGET_A = "PDFCAB_REMOTE_A.pdf"
_REMOTE_GOTO_TARGET_B = "PDFCAB_REMOTE_B.pdf"
_EMBEDDED_GOTO_TARGET_A = "PDFCAB_EMBEDDED_A.pdf"
_EMBEDDED_GOTO_TARGET_B = "PDFCAB_EMBEDDED_B.pdf"
_SUBMIT_TARGET_A = "https://example.invalid/pdfcab-submit-a"
_SUBMIT_TARGET_B = "https://example.invalid/pdfcab-submit-b"
_IMPORT_TARGET_A = "PDFCAB_IMPORT_A.fdf"
_IMPORT_TARGET_B = "PDFCAB_IMPORT_B.fdf"
_PASSWORD = "pdfcab-inert-password"
_CHILD_DOCUMENT_NAME = "PDFCAB_CHILD.pdf"


@dataclass(frozen=True)
class FixtureSpec:
    """One deterministic pair plus its public static-analysis expectation."""

    fixture_id: str
    category: str
    description: str
    mutation: str
    expected_change_kinds: tuple[str, ...]
    expected_policy_rule_ids: tuple[str, ...]

    def truth(self) -> FixtureTruth:
        """Return the public fixture truth document."""

        return FixtureTruth(
            schema_version=FIXTURE_SCHEMA_VERSION,
            fixture_id=self.fixture_id,
            category=self.category,
            description=self.description,
            expected_change_kinds=self.expected_change_kinds,
            expected_policy_rule_ids=self.expected_policy_rule_ids,
        )


FIXTURE_SPECS = (
    FixtureSpec(
        "active.javascript_added",
        "active_content",
        "A stored JavaScript name-tree action is added.",
        "javascript_added",
        (
            "active_content_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.uri_action_added",
        "active_content",
        "A stored URI action is added at the document catalog.",
        "uri_action_added",
        (
            "active_content_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.launch_action_added",
        "active_content",
        "A stored launch action is added at the document catalog.",
        "launch_action_added",
        (
            "active_content_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.set_ocg_state_action_added",
        "active_content",
        "A stored SetOCGState action is added at the document catalog.",
        "set_ocg_state_action_added",
        (
            "active_content_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.goto_to_embedded_goto",
        "active_content",
        "A local GoTo action is replaced with an embedded-document GoTo action.",
        "goto_to_embedded_goto",
        (
            "active_content_inventory_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.goto_root_named_destination_rebound",
        "active_content",
        (
            "A document-open named local GoTo target is rebound to a different "
            "page while the stored action remains fixed."
        ),
        "goto_root_named_destination_rebound",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.goto_root_named_destination_target_page_rotated",
        "active_content",
        (
            "A document-open named local GoTo target page state changes while "
            "its name-tree mapping and stored action remain fixed."
        ),
        "goto_root_named_destination_target_page_rotated",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.goto_root_named_destination_unrelated_mapping_rewritten",
        "active_content",
        (
            "An unrelated destination name-tree mapping changes while a "
            "document-open GoTo target remains fixed."
        ),
        "goto_root_named_destination_unrelated_mapping_rewritten",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.link_named_destination_rebound",
        "active_content",
        (
            "A Link annotation's named local destination is rebound to a "
            "different page while its stored annotation remains fixed."
        ),
        "link_named_destination_rebound",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.link_named_destination_target_page_rotated",
        "active_content",
        (
            "A Link annotation's named local destination page state changes "
            "while its stored annotation and mapping remain fixed."
        ),
        "link_named_destination_target_page_rotated",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.link_named_destination_unrelated_mapping_rewritten",
        "active_content",
        (
            "An unrelated legacy destination mapping changes while a Link "
            "annotation's named target remains fixed."
        ),
        "link_named_destination_unrelated_mapping_rewritten",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.open_destination_rebound",
        "active_content",
        (
            "A document-open explicit destination moves to a different page "
            "without adding an action dictionary."
        ),
        "open_destination_rebound",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.open_destination_target_page_rotated",
        "active_content",
        (
            "A document-open explicit destination page state changes while "
            "the stored destination remains fixed."
        ),
        "open_destination_target_page_rotated",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.outline_named_destination_rebound",
        "active_content",
        (
            "An outline item's named local destination is rebound to a "
            "different page while its stored outline item remains fixed."
        ),
        "outline_named_destination_rebound",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.outline_named_destination_target_page_rotated",
        "active_content",
        (
            "An outline item's named local destination page state changes "
            "while its stored outline item and mapping remain fixed."
        ),
        "outline_named_destination_target_page_rotated",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.outline_named_destination_unrelated_mapping_rewritten",
        "active_content",
        (
            "An unrelated legacy destination mapping changes while an outline "
            "item's named target remains fixed."
        ),
        "outline_named_destination_unrelated_mapping_rewritten",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.goto_3d_view_to_document_part",
        "active_content",
        (
            "A GoTo3DView action is replaced with a PDF 2.0 document-part "
            "GoTo action while both target structures remain present."
        ),
        "goto_3d_view_to_document_part",
        (
            "active_content_inventory_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.uri_payload_rewritten",
        "active_content",
        "A URI action payload changes while its public action inventory is fixed.",
        "uri_payload_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.javascript_payload_rewritten",
        "active_content",
        "A JavaScript payload changes while its public action inventory is fixed.",
        "javascript_payload_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.javascript_trigger_rebound",
        "active_content",
        (
            "Two JavaScript payloads exchange document-open and document-close "
            "bindings while their public action inventory is fixed."
        ),
        "javascript_trigger_rebound",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.javascript_action_chain_reordered",
        "active_content",
        (
            "Two JavaScript actions exchange positions in a stored action chain "
            "while their public action inventory is fixed."
        ),
        "javascript_action_chain_reordered",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.javascript_action_chain_reordered_shared_array",
        "active_content",
        (
            "JavaScript actions exchange positions in a shared stored action "
            "chain that is also reachable outside the execution trigger."
        ),
        "javascript_action_chain_reordered_shared_array",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.action_chain_action_types_reordered",
        "active_content",
        (
            "Two non-payload action types exchange positions in a stored action "
            "chain while their public action inventory is fixed."
        ),
        "action_chain_action_types_reordered",
        (
            "active_content_execution_order_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.action_chain_action_types_reordered_shared_array",
        "active_content",
        (
            "Two non-payload action types exchange positions in a shared stored "
            "action chain that is also reachable outside the execution trigger."
        ),
        "action_chain_action_types_reordered_shared_array",
        (
            "active_content_execution_order_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.action_chain_same_type_reordered",
        "active_content",
        (
            "Two same-type action successors exchange positions in a stored "
            "action chain while their public action inventory is fixed."
        ),
        "action_chain_same_type_reordered",
        (
            "active_content_action_sequence_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.action_chain_same_type_reordered_shared_array",
        "active_content",
        (
            "Same-type action successors exchange positions in a shared stored "
            "action chain that is also reachable outside the execution trigger."
        ),
        "action_chain_same_type_reordered_shared_array",
        (
            "active_content_action_sequence_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.action_chain_destination_page_rotated",
        "active_content",
        (
            "A destination page state changes while its stored action chain "
            "remains fixed."
        ),
        "action_chain_destination_page_rotated",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.named_destination_rebound",
        "active_content",
        (
            "A named local GoTo target is rebound to a different page while "
            "the stored action chain remains fixed."
        ),
        "named_destination_rebound",
        (
            "active_content_action_sequence_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.named_destination_target_page_rotated",
        "active_content",
        (
            "A named local GoTo target page state changes while its name-tree "
            "mapping and stored action chain remain fixed."
        ),
        "named_destination_target_page_rotated",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.named_destination_unrelated_mapping_rewritten",
        "active_content",
        (
            "An unrelated destination name-tree mapping changes while the "
            "stored GoTo target remains fixed."
        ),
        "named_destination_unrelated_mapping_rewritten",
        ("stored_pdf_bytes_changed",),
        (),
    ),
    FixtureSpec(
        "active.javascript_stream_filter_rewritten",
        "active_content",
        (
            "A JavaScript stream decoding configuration changes while its raw "
            "stored bytes and public action inventory remain fixed."
        ),
        "javascript_stream_filter_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.launch_target_rewritten",
        "active_content",
        "A Launch action target changes while its public action inventory is fixed.",
        "launch_target_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.remote_goto_target_rewritten",
        "active_content",
        (
            "A remote GoTo action file target changes while its public action "
            "inventory is fixed."
        ),
        "remote_goto_target_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.embedded_goto_target_rewritten",
        "active_content",
        (
            "An embedded GoTo action file target changes while its public "
            "action inventory is fixed."
        ),
        "embedded_goto_target_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.submit_form_target_rewritten",
        "active_content",
        (
            "A SubmitForm endpoint changes while its public action inventory "
            "is fixed."
        ),
        "submit_form_target_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "active.import_data_target_rewritten",
        "active_content",
        (
            "An ImportData file target changes while its public action "
            "inventory is fixed."
        ),
        "import_data_target_rewritten",
        (
            "active_content_payload_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP001",),
    ),
    FixtureSpec(
        "embedded.file_added",
        "embedded_content",
        "A stored embedded-file stream and file specification are added.",
        "embedded_file_added",
        (
            "embedded_content_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP002",),
    ),
    FixtureSpec(
        "embedded.associated_file_association_added",
        "embedded_content",
        (
            "A document-level Associated Files link is added for an existing "
            "embedded file."
        ),
        "associated_file_association_added",
        (
            "embedded_content_inventory_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP002",),
    ),
    FixtureSpec(
        "interaction.form_field_added",
        "interactive_feature",
        "A stored text form field is added.",
        "form_field_added",
        (
            "interactive_feature_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP003",),
    ),
    FixtureSpec(
        "interaction.link_annotation_added",
        "interactive_feature",
        "A stored link annotation is added without a target action.",
        "link_annotation_added",
        (
            "interactive_feature_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP003",),
    ),
    FixtureSpec(
        "review.xfa_added",
        "interactive_feature",
        "An AcroForm XFA declaration is added.",
        "xfa_added",
        ("interactive_feature_inventory_changed", "stored_pdf_bytes_changed"),
        ("PFP003",),
    ),
    FixtureSpec(
        "review.collection_added",
        "interactive_feature",
        "A document collection declaration is added.",
        "collection_added",
        ("interactive_feature_inventory_changed", "stored_pdf_bytes_changed"),
        ("PFP003",),
    ),
    FixtureSpec(
        "review.optional_content_added",
        "optional_content",
        "Catalog optional-content group and configuration topology is added.",
        "optional_content_added",
        (
            "optional_content_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP007", "PFP008"),
    ),
    FixtureSpec(
        "signature.structure_added",
        "signature_structure",
        "A static signature dictionary and signature field are added.",
        "signature_added",
        (
            "interactive_feature_inventory_changed",
            "reachable_object_count_changed",
            "signature_structure_inventory_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP004",),
    ),
    FixtureSpec(
        "metadata.xmp_added",
        "metadata",
        "A stored XMP metadata stream is added.",
        "xmp_added",
        (
            "metadata_inventory_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        (),
    ),
    FixtureSpec(
        "review.incremental_update_added",
        "revision_chain",
        "A valid incremental cross-reference revision is appended.",
        "incremental_update_added",
        ("revision_chain_changed", "stored_pdf_bytes_changed"),
        ("PFP006",),
    ),
    FixtureSpec(
        "review.encryption_enabled",
        "encryption",
        "A PDF becomes encrypted and therefore remains uninspected.",
        "encryption_enabled",
        (
            "encryption_state_changed",
            "inspection_state_changed",
            "page_count_changed",
            "reachable_object_count_changed",
            "stored_pdf_bytes_changed",
        ),
        ("PFP005",),
    ),
    FixtureSpec(
        "metadata.information_value_rewritten",
        "metadata",
        "An information-dictionary value changes while its public presence is fixed.",
        "information_value_rewritten",
        ("stored_pdf_bytes_changed",),
        (),
    ),
)


def build_fixture_tree(destination: str | Path) -> tuple[FixtureTruth, ...]:
    """Build all fixtures into an absent or empty directory."""

    target = _empty_destination(destination)
    truths: list[FixtureTruth] = []
    for spec in FIXTURE_SPECS:
        fixture_directory = target / spec.fixture_id
        fixture_directory.mkdir()
        baseline = fixture_directory / "baseline.pdf"
        candidate = fixture_directory / "candidate.pdf"
        _build_pair(spec.mutation, baseline, candidate)
        truth = spec.truth()
        (fixture_directory / "truth.json").write_text(
            json.dumps(truth.public_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        truths.append(truth)
    (target / "manifest.jsonl").write_text(
        "".join(
            json.dumps(truth.public_dict(), sort_keys=True) + "\n"
            for truth in sorted(truths, key=lambda value: value.fixture_id)
        ),
        encoding="utf-8",
        newline="\n",
    )
    return tuple(sorted(truths, key=lambda value: value.fixture_id))


def _empty_destination(destination: str | Path) -> Path:
    try:
        target = Path(destination)
        if target.exists():
            if target.is_symlink() or not target.is_dir():
                raise FixtureError("fixture destination must be an empty directory")
            if any(target.iterdir()):
                raise FixtureError("fixture destination must be empty")
        else:
            target.mkdir(parents=True)
        return target
    except FixtureError:
        raise
    except (OSError, TypeError, ValueError):
        raise FixtureError("fixture destination cannot be prepared") from None


def _build_pair(mutation: str, baseline: Path, candidate: Path) -> None:
    if mutation == "javascript_added":
        _write(_writer(), baseline)
        _write(_writer(javascript=_MARKER_A), candidate)
    elif mutation == "uri_action_added":
        _write(_writer(), baseline)
        _write(_writer(action="/URI"), candidate)
    elif mutation == "launch_action_added":
        _write(_writer(), baseline)
        _write(_writer(action="/Launch"), candidate)
    elif mutation == "set_ocg_state_action_added":
        _write(_writer(), baseline)
        _write(_writer(action="/SetOCGState"), candidate)
    elif mutation == "goto_to_embedded_goto":
        _write(
            _writer(
                action="/GoTo",
                embedded_child_document=True,
            ),
            baseline,
        )
        _write(
            _writer(
                action="/GoToE",
                embedded_child_document=True,
            ),
            candidate,
        )
    elif mutation == "goto_root_named_destination_rebound":
        _write(
            _catalog_named_destination_root_goto_writer(destination=0),
            baseline,
        )
        _write(
            _catalog_named_destination_root_goto_writer(destination=1),
            candidate,
        )
    elif mutation == "goto_root_named_destination_target_page_rotated":
        _write(
            _catalog_named_destination_root_goto_writer(
                destination=0,
                page_rotation=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_root_goto_writer(
                destination=0,
                page_rotation=90,
            ),
            candidate,
        )
    elif mutation == "goto_root_named_destination_unrelated_mapping_rewritten":
        _write(
            _catalog_named_destination_root_goto_writer(
                destination=0,
                unrelated_destination=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_root_goto_writer(
                destination=0,
                unrelated_destination=1,
            ),
            candidate,
        )
    elif mutation == "link_named_destination_rebound":
        _write(
            _catalog_named_destination_link_writer(destination=0),
            baseline,
        )
        _write(
            _catalog_named_destination_link_writer(destination=1),
            candidate,
        )
    elif mutation == "link_named_destination_target_page_rotated":
        _write(
            _catalog_named_destination_link_writer(
                destination=0,
                page_rotation=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_link_writer(
                destination=0,
                page_rotation=90,
            ),
            candidate,
        )
    elif mutation == "link_named_destination_unrelated_mapping_rewritten":
        _write(
            _catalog_named_destination_link_writer(
                destination=0,
                unrelated_destination=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_link_writer(
                destination=0,
                unrelated_destination=1,
            ),
            candidate,
        )
    elif mutation == "open_destination_rebound":
        _write(_catalog_open_destination_writer(destination=0), baseline)
        _write(_catalog_open_destination_writer(destination=1), candidate)
    elif mutation == "open_destination_target_page_rotated":
        _write(
            _catalog_open_destination_writer(destination=0, page_rotation=0),
            baseline,
        )
        _write(
            _catalog_open_destination_writer(destination=0, page_rotation=90),
            candidate,
        )
    elif mutation == "outline_named_destination_rebound":
        _write(
            _catalog_named_destination_outline_writer(destination=0),
            baseline,
        )
        _write(
            _catalog_named_destination_outline_writer(destination=1),
            candidate,
        )
    elif mutation == "outline_named_destination_target_page_rotated":
        _write(
            _catalog_named_destination_outline_writer(
                destination=0,
                page_rotation=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_outline_writer(
                destination=0,
                page_rotation=90,
            ),
            candidate,
        )
    elif mutation == "outline_named_destination_unrelated_mapping_rewritten":
        _write(
            _catalog_named_destination_outline_writer(
                destination=0,
                unrelated_destination=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_outline_writer(
                destination=0,
                unrelated_destination=1,
            ),
            candidate,
        )
    elif mutation == "goto_3d_view_to_document_part":
        _write(_writer(action="/GoTo3DView"), baseline)
        _write(_writer(action="/GoToDp"), candidate)
    elif mutation == "uri_payload_rewritten":
        _write(_writer(action="/URI", uri=_URI), baseline)
        _write(_writer(action="/URI", uri=_URI_B), candidate)
    elif mutation == "javascript_payload_rewritten":
        _write(_writer(javascript=_MARKER_A), baseline)
        _write(_writer(javascript=_MARKER_B), candidate)
    elif mutation == "javascript_trigger_rebound":
        _write(
            _catalog_javascript_trigger_writer(
                open_payload=_MARKER_A,
                will_close_payload=_MARKER_B,
            ),
            baseline,
        )
        _write(
            _catalog_javascript_trigger_writer(
                open_payload=_MARKER_B,
                will_close_payload=_MARKER_A,
            ),
            candidate,
        )
    elif mutation == "javascript_action_chain_reordered":
        _write(
            _catalog_javascript_action_chain_writer(
                first_next_payload=_MARKER_B,
                second_next_payload=_MARKER_C,
            ),
            baseline,
        )
        _write(
            _catalog_javascript_action_chain_writer(
                first_next_payload=_MARKER_C,
                second_next_payload=_MARKER_B,
            ),
            candidate,
        )
    elif mutation == "javascript_action_chain_reordered_shared_array":
        _write(
            _catalog_javascript_action_chain_writer(
                first_next_payload=_MARKER_B,
                second_next_payload=_MARKER_C,
                previsit_successors=True,
            ),
            baseline,
        )
        _write(
            _catalog_javascript_action_chain_writer(
                first_next_payload=_MARKER_C,
                second_next_payload=_MARKER_B,
                previsit_successors=True,
            ),
            candidate,
        )
    elif mutation == "action_chain_action_types_reordered":
        _write(
            _catalog_action_type_chain_writer(
                first_successor="/SetOCGState",
                second_successor="/GoTo",
            ),
            baseline,
        )
        _write(
            _catalog_action_type_chain_writer(
                first_successor="/GoTo",
                second_successor="/SetOCGState",
            ),
            candidate,
        )
    elif mutation == "action_chain_action_types_reordered_shared_array":
        _write(
            _catalog_action_type_chain_writer(
                first_successor="/SetOCGState",
                second_successor="/GoTo",
                previsit_successors=True,
            ),
            baseline,
        )
        _write(
            _catalog_action_type_chain_writer(
                first_successor="/GoTo",
                second_successor="/SetOCGState",
                previsit_successors=True,
            ),
            candidate,
        )
    elif mutation == "action_chain_same_type_reordered":
        _write(
            _catalog_same_type_action_chain_writer(
                first_destination=0,
                second_destination=1,
            ),
            baseline,
        )
        _write(
            _catalog_same_type_action_chain_writer(
                first_destination=1,
                second_destination=0,
            ),
            candidate,
        )
    elif mutation == "action_chain_same_type_reordered_shared_array":
        _write(
            _catalog_same_type_action_chain_writer(
                first_destination=0,
                second_destination=1,
                previsit_successors=True,
            ),
            baseline,
        )
        _write(
            _catalog_same_type_action_chain_writer(
                first_destination=1,
                second_destination=0,
                previsit_successors=True,
            ),
            candidate,
        )
    elif mutation == "action_chain_destination_page_rotated":
        _write(
            _catalog_destination_page_rotation_writer(page_rotation=0),
            baseline,
        )
        _write(
            _catalog_destination_page_rotation_writer(page_rotation=90),
            candidate,
        )
    elif mutation == "named_destination_rebound":
        _write(
            _catalog_named_destination_writer(destination=0),
            baseline,
        )
        _write(
            _catalog_named_destination_writer(destination=1),
            candidate,
        )
    elif mutation == "named_destination_target_page_rotated":
        _write(
            _catalog_named_destination_writer(
                destination=0,
                page_rotation=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_writer(
                destination=0,
                page_rotation=90,
            ),
            candidate,
        )
    elif mutation == "named_destination_unrelated_mapping_rewritten":
        _write(
            _catalog_named_destination_writer(
                destination=0,
                unrelated_destination=0,
            ),
            baseline,
        )
        _write(
            _catalog_named_destination_writer(
                destination=0,
                unrelated_destination=1,
            ),
            candidate,
        )
    elif mutation == "javascript_stream_filter_rewritten":
        _write(
            _writer(
                action="/JavaScript",
                javascript_stream_payload=_JAVASCRIPT_STREAM_RAW,
            ),
            baseline,
        )
        _write(
            _writer(
                action="/JavaScript",
                javascript_stream_payload=_JAVASCRIPT_STREAM_RAW,
                javascript_stream_filter=_JAVASCRIPT_STREAM_FILTER,
            ),
            candidate,
        )
    elif mutation == "launch_target_rewritten":
        _write(_writer(action="/Launch", action_target=_LAUNCH_TARGET_A), baseline)
        _write(_writer(action="/Launch", action_target=_LAUNCH_TARGET_B), candidate)
    elif mutation == "remote_goto_target_rewritten":
        _write(
            _writer(
                action="/GoToR",
                action_target=_REMOTE_GOTO_TARGET_A,
                action_target_as_file_specification=True,
            ),
            baseline,
        )
        _write(
            _writer(
                action="/GoToR",
                action_target=_REMOTE_GOTO_TARGET_B,
                action_target_as_file_specification=True,
            ),
            candidate,
        )
    elif mutation == "embedded_goto_target_rewritten":
        _write(
            _writer(
                action="/GoToE",
                embedded_goto_target=_EMBEDDED_GOTO_TARGET_A,
                embedded_goto_target_as_file_specification=True,
            ),
            baseline,
        )
        _write(
            _writer(
                action="/GoToE",
                embedded_goto_target=_EMBEDDED_GOTO_TARGET_B,
                embedded_goto_target_as_file_specification=True,
            ),
            candidate,
        )
    elif mutation == "submit_form_target_rewritten":
        _write(
            _writer(action="/SubmitForm", action_target=_SUBMIT_TARGET_A),
            baseline,
        )
        _write(
            _writer(action="/SubmitForm", action_target=_SUBMIT_TARGET_B),
            candidate,
        )
    elif mutation == "import_data_target_rewritten":
        _write(
            _writer(
                action="/ImportData",
                action_target=_IMPORT_TARGET_A,
                action_target_as_file_specification=True,
            ),
            baseline,
        )
        _write(
            _writer(
                action="/ImportData",
                action_target=_IMPORT_TARGET_B,
                action_target_as_file_specification=True,
            ),
            candidate,
        )
    elif mutation == "embedded_file_added":
        _write(_writer(), baseline)
        _write(_writer(embedded_file=True), candidate)
    elif mutation == "associated_file_association_added":
        _write(_writer(associated_file=True), baseline)
        _write(
            _writer(
                associated_file=True,
                associate_embedded_file=True,
            ),
            candidate,
        )
    elif mutation == "form_field_added":
        _write(_writer(), baseline)
        _write(_writer(form_field=True), candidate)
    elif mutation == "link_annotation_added":
        _write(_writer(), baseline)
        _write(_writer(link_annotation=True), candidate)
    elif mutation == "xfa_added":
        _write(_writer(), baseline)
        _write(_writer(xfa=True), candidate)
    elif mutation == "collection_added":
        _write(_writer(), baseline)
        _write(_writer(collection=True), candidate)
    elif mutation == "optional_content_added":
        _write(_writer(), baseline)
        _write(_writer(optional_content=True), candidate)
    elif mutation == "signature_added":
        _write(_writer(), baseline)
        _write(_writer(signature=True), candidate)
    elif mutation == "xmp_added":
        _write(_writer(), baseline)
        _write(_writer(xmp=True), candidate)
    elif mutation == "incremental_update_added":
        _write(_writer(), baseline)
        _increment(baseline, candidate)
    elif mutation == "encryption_enabled":
        _write(_writer(), baseline)
        _write(_writer(encrypted=True), candidate)
    elif mutation == "information_value_rewritten":
        _write(_writer(title=_MARKER_A), baseline)
        _write(_writer(title=_MARKER_B), candidate)
    else:
        raise FixtureError("fixture mutation is unsupported")


def _writer(
    *,
    title: str = _MARKER_A,
    javascript: str | None = None,
    action: str | None = None,
    uri: str = _URI,
    action_target: str = _MARKER_A,
    action_target_as_file_specification: bool = False,
    embedded_goto_target: str | None = None,
    embedded_goto_target_as_file_specification: bool = False,
    javascript_stream_payload: bytes | None = None,
    javascript_stream_filter: str | None = None,
    embedded_file: bool = False,
    embedded_child_document: bool = False,
    form_field: bool = False,
    link_annotation: bool = False,
    xfa: bool = False,
    collection: bool = False,
    signature: bool = False,
    xmp: bool = False,
    optional_content: bool = False,
    associated_file: bool = False,
    associate_embedded_file: bool = False,
    encrypted: bool = False,
) -> PdfWriter:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.add_metadata({"/Title": title})
    if javascript is not None:
        _add_javascript(writer, javascript)
    if action is not None:
        three_d_annotation: IndirectObject | None = None
        document_part: IndirectObject | None = None
        javascript_stream: IndirectObject | None = None
        if action in {"/GoTo3DView", "/GoToDp"}:
            three_d_annotation, document_part = _add_navigation_targets(writer)
        if javascript_stream_payload is not None:
            if action != "/JavaScript":
                raise FixtureError("JavaScript stream requires a JavaScript action")
            stream = DecodedStreamObject()
            stream.set_data(javascript_stream_payload)
            if javascript_stream_filter is not None:
                stream[NameObject("/Filter")] = NameObject(javascript_stream_filter)
            javascript_stream = writer._add_object(stream)
        elif javascript_stream_filter is not None:
            raise FixtureError("JavaScript stream filter requires stream bytes")
        action_reference = writer._add_object(
            _action(
                action,
                three_d_annotation=three_d_annotation,
                document_part=document_part,
                uri=uri,
                action_target=action_target,
                action_target_as_file_specification=(
                    action_target_as_file_specification
                ),
                embedded_goto_target=embedded_goto_target,
                embedded_goto_target_as_file_specification=(
                    embedded_goto_target_as_file_specification
                ),
                javascript_stream=javascript_stream,
            )
        )
        writer._root_object[NameObject("/OpenAction")] = action_reference
    if embedded_file:
        writer.add_attachment(f"{_MARKER_A}.txt", _MARKER_A.encode("utf-8"))
    if embedded_child_document:
        writer.add_attachment(_CHILD_DOCUMENT_NAME, _child_document_bytes())
    if form_field or xfa or signature:
        _add_acroform(
            writer,
            form_field=form_field,
            xfa=xfa,
            signature=signature,
        )
    if link_annotation:
        _add_link_annotation(writer)
    if collection:
        writer._root_object[NameObject("/Collection")] = DictionaryObject()
    if xmp:
        metadata = DecodedStreamObject()
        metadata[NameObject("/Type")] = NameObject("/Metadata")
        metadata.set_data(_MARKER_A.encode("utf-8"))
        writer._root_object[NameObject("/Metadata")] = writer._add_object(metadata)
    if optional_content:
        _add_optional_content(writer)
    if associated_file:
        associated_file_reference = _add_associated_file(writer)
        if associate_embedded_file:
            writer._root_object[NameObject("/AF")] = ArrayObject(
                [associated_file_reference]
            )
    if encrypted:
        writer.encrypt(_PASSWORD)
    return writer


def _write(writer: PdfWriter, path: Path) -> None:
    with path.open("wb") as stream:
        writer.write(stream)


def _catalog_javascript_trigger_writer(
    *,
    open_payload: str,
    will_close_payload: str,
) -> PdfWriter:
    """Build a catalog with distinct document-open and will-close scripts."""

    writer = _writer()

    def javascript_action(payload: str) -> IndirectObject:
        return writer._add_object(
            DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Action"),
                    NameObject("/S"): NameObject("/JavaScript"),
                    NameObject("/JS"): TextStringObject(payload),
                }
            )
        )

    writer._root_object[NameObject("/OpenAction")] = javascript_action(open_payload)
    writer._root_object[NameObject("/AA")] = DictionaryObject(
        {NameObject("/WC"): javascript_action(will_close_payload)}
    )
    return writer


def _catalog_javascript_action_chain_writer(
    *,
    first_next_payload: str,
    second_next_payload: str,
    previsit_successors: bool = False,
) -> PdfWriter:
    """Build a document-open script with an ordered two-action successor list."""

    writer = _writer()

    def javascript_action(payload: str) -> IndirectObject:
        return writer._add_object(
            DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Action"),
                    NameObject("/S"): NameObject("/JavaScript"),
                    NameObject("/JS"): TextStringObject(payload),
                }
            )
        )

    primary = javascript_action(_MARKER_A)
    successors = ArrayObject(
        [
            javascript_action(first_next_payload),
            javascript_action(second_next_payload),
        ]
    )
    if previsit_successors:
        shared_successors = writer._add_object(successors)
        writer._root_object[NameObject("/PieceInfo")] = DictionaryObject(
            {
                NameObject("/PDFCAB"): DictionaryObject(
                    {NameObject("/Shared"): shared_successors}
                )
            }
        )
        primary.get_object()[NameObject("/Next")] = shared_successors
    else:
        primary.get_object()[NameObject("/Next")] = successors
    writer._root_object[NameObject("/OpenAction")] = primary
    return writer


def _catalog_action_type_chain_writer(
    *,
    first_successor: str,
    second_successor: str,
    previsit_successors: bool = False,
) -> PdfWriter:
    """Build a document-open action with ordered non-payload successors."""

    writer = _writer()
    optional_content_group = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/OCG"),
                NameObject("/Name"): TextStringObject(_MARKER_A),
            }
        )
    )
    writer._root_object[NameObject("/OCProperties")] = DictionaryObject(
        {
            NameObject("/OCGs"): ArrayObject([optional_content_group]),
            NameObject("/D"): DictionaryObject(),
        }
    )

    def successor(kind: str) -> IndirectObject:
        action = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject(kind),
            }
        )
        if kind == "/SetOCGState":
            action[NameObject("/State")] = ArrayObject(
                [NameObject("/ON"), optional_content_group]
            )
        elif kind == "/GoTo":
            action[NameObject("/D")] = ArrayObject(
                [writer.pages[0].indirect_reference, NameObject("/Fit")]
            )
        else:
            raise FixtureError("action-chain successor is unsupported")
        return writer._add_object(action)

    primary = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(_MARKER_A),
            }
        )
    )
    successors = ArrayObject(
        [successor(first_successor), successor(second_successor)]
    )
    if previsit_successors:
        shared_successors = writer._add_object(successors)
        writer._root_object[NameObject("/PieceInfo")] = DictionaryObject(
            {
                NameObject("/PDFCAB"): DictionaryObject(
                    {NameObject("/Shared"): shared_successors}
                )
            }
        )
        primary.get_object()[NameObject("/Next")] = shared_successors
    else:
        primary.get_object()[NameObject("/Next")] = successors
    writer._root_object[NameObject("/OpenAction")] = primary
    return writer


def _catalog_same_type_action_chain_writer(
    *,
    first_destination: int,
    second_destination: int,
    previsit_successors: bool = False,
) -> PdfWriter:
    """Build a document-open action with two GoTo successors for real pages."""

    writer = _writer()
    second_page = writer.add_blank_page(width=72, height=72)
    destinations = (
        writer.pages[0].indirect_reference,
        second_page.indirect_reference,
    )
    primary = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(_MARKER_A),
            }
        )
    )

    def successor(destination: int) -> IndirectObject:
        return writer._add_object(
            DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Action"),
                    NameObject("/S"): NameObject("/GoTo"),
                    NameObject("/D"): ArrayObject(
                        [destinations[destination], NameObject("/Fit")]
                    ),
                }
            )
        )

    successors = ArrayObject(
        [successor(first_destination), successor(second_destination)]
    )
    if previsit_successors:
        shared_successors = writer._add_object(successors)
        writer._root_object[NameObject("/PieceInfo")] = DictionaryObject(
            {
                NameObject("/PDFCAB"): DictionaryObject(
                    {NameObject("/Shared"): shared_successors}
                )
            }
        )
        primary.get_object()[NameObject("/Next")] = shared_successors
    else:
        primary.get_object()[NameObject("/Next")] = successors
    writer._root_object[NameObject("/OpenAction")] = primary
    return writer


def _catalog_destination_page_rotation_writer(*, page_rotation: int) -> PdfWriter:
    """Build a GoTo successor whose referenced page has fixed action data."""

    writer = _writer()
    page = writer.pages[0]
    page[NameObject("/Rotate")] = NumberObject(page_rotation)
    primary = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(_MARKER_A),
            }
        )
    )
    successor = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/GoTo"),
                NameObject("/D"): ArrayObject(
                    [page.indirect_reference, NameObject("/Fit")]
                ),
            }
        )
    )
    primary.get_object()[NameObject("/Next")] = ArrayObject([successor])
    writer._root_object[NameObject("/OpenAction")] = primary
    return writer


def _catalog_named_destination_writer(
    *,
    destination: int,
    page_rotation: int = 0,
    unrelated_destination: int | None = None,
) -> PdfWriter:
    """Build a GoTo successor that resolves through a Dests name tree."""

    writer = _writer()
    first_page = writer.pages[0]
    first_page[NameObject("/Rotate")] = NumberObject(page_rotation)
    second_page = writer.add_blank_page(width=72, height=72)
    pages = (first_page, second_page)

    def explicit_destination(page: int) -> IndirectObject:
        return writer._add_object(
            ArrayObject([pages[page].indirect_reference, NameObject("/Fit")])
        )

    entries = ArrayObject(
        [TextStringObject(_MARKER_B), explicit_destination(destination)]
    )
    if unrelated_destination is not None:
        entries.extend(
            [
                TextStringObject(_MARKER_C),
                explicit_destination(unrelated_destination),
            ]
        )
    leaf = writer._add_object(
        DictionaryObject({NameObject("/Names"): entries})
    )
    tree = writer._add_object(
        DictionaryObject({NameObject("/Kids"): ArrayObject([leaf])})
    )
    writer._root_object[NameObject("/Names")] = DictionaryObject(
        {NameObject("/Dests"): tree}
    )

    primary = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(_MARKER_A),
            }
        )
    )
    successor = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/GoTo"),
                NameObject("/D"): TextStringObject(_MARKER_B),
            }
        )
    )
    primary.get_object()[NameObject("/Next")] = ArrayObject([successor])
    writer._root_object[NameObject("/OpenAction")] = primary
    return writer


def _catalog_named_destination_root_goto_writer(
    *,
    destination: int,
    page_rotation: int = 0,
    unrelated_destination: int | None = None,
) -> PdfWriter:
    """Build a document-open GoTo action resolved through a Dests name tree."""

    writer = _writer()
    first_page = writer.pages[0]
    first_page[NameObject("/Rotate")] = NumberObject(page_rotation)
    second_page = writer.add_blank_page(width=72, height=72)
    pages = (first_page, second_page)

    def explicit_destination(page: int) -> IndirectObject:
        return writer._add_object(
            ArrayObject([pages[page].indirect_reference, NameObject("/Fit")])
        )

    chapter_destination = explicit_destination(destination)
    writer._root_object[NameObject("/PieceInfo")] = DictionaryObject(
        {
            NameObject("/PDFCAB"): DictionaryObject(
                {NameObject("/ReservedDestination"): chapter_destination}
            )
        }
    )
    entries = ArrayObject([TextStringObject(_MARKER_B), chapter_destination])
    if unrelated_destination is not None:
        entries.extend(
            [
                TextStringObject(_MARKER_C),
                explicit_destination(unrelated_destination),
            ]
        )
    leaf = writer._add_object(
        DictionaryObject({NameObject("/Names"): entries})
    )
    tree = writer._add_object(
        DictionaryObject({NameObject("/Kids"): ArrayObject([leaf])})
    )
    writer._root_object[NameObject("/Names")] = DictionaryObject(
        {NameObject("/Dests"): tree}
    )
    writer._root_object[NameObject("/OpenAction")] = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/GoTo"),
                NameObject("/D"): TextStringObject(_MARKER_B),
            }
        )
    )
    return writer


def _catalog_open_destination_writer(
    *,
    destination: int,
    page_rotation: int = 0,
) -> PdfWriter:
    """Build a document-open explicit destination without an action dictionary."""

    writer = _writer()
    first_page = writer.pages[0]
    first_page[NameObject("/Rotate")] = NumberObject(page_rotation)
    second_page = writer.add_blank_page(width=72, height=72)
    pages = (first_page, second_page)
    writer._root_object[NameObject("/OpenAction")] = ArrayObject(
        [pages[destination].indirect_reference, NameObject("/Fit")]
    )
    return writer


def _catalog_named_destination_link_writer(
    *,
    destination: int,
    page_rotation: int = 0,
    unrelated_destination: int | None = None,
) -> PdfWriter:
    """Build a Link Dest name resolved through the legacy catalog map."""

    writer = _writer()
    first_page = writer.pages[0]
    first_page[NameObject("/Rotate")] = NumberObject(page_rotation)
    second_page = writer.add_blank_page(width=72, height=72)
    pages = (first_page, second_page)

    def explicit_destination(page: int) -> IndirectObject:
        return writer._add_object(
            ArrayObject([pages[page].indirect_reference, NameObject("/Fit")])
        )

    destination_name = NameObject(f"/{_MARKER_B}")
    destinations = DictionaryObject(
        {destination_name: explicit_destination(destination)}
    )
    if unrelated_destination is not None:
        destinations[NameObject(f"/{_MARKER_C}")] = explicit_destination(
            unrelated_destination
        )
    writer._root_object[NameObject("/Dests")] = destinations
    annotation = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject(
                    [
                        NumberObject(0),
                        NumberObject(0),
                        NumberObject(12),
                        NumberObject(12),
                    ]
                ),
                NameObject("/Border"): ArrayObject(
                    [NumberObject(0), NumberObject(0), NumberObject(0)]
                ),
                NameObject("/Dest"): destination_name,
            }
        )
    )
    first_page[NameObject("/Annots")] = ArrayObject([annotation])
    return writer


def _catalog_named_destination_outline_writer(
    *,
    destination: int,
    page_rotation: int = 0,
    unrelated_destination: int | None = None,
) -> PdfWriter:
    """Build an outline Dest name resolved through the legacy catalog map."""

    writer = _writer()
    first_page = writer.pages[0]
    first_page[NameObject("/Rotate")] = NumberObject(page_rotation)
    second_page = writer.add_blank_page(width=72, height=72)
    pages = (first_page, second_page)

    def explicit_destination(page: int) -> IndirectObject:
        return writer._add_object(
            ArrayObject([pages[page].indirect_reference, NameObject("/Fit")])
        )

    destination_name = NameObject(f"/{_MARKER_B}")
    destinations = DictionaryObject(
        {destination_name: explicit_destination(destination)}
    )
    if unrelated_destination is not None:
        destinations[NameObject(f"/{_MARKER_C}")] = explicit_destination(
            unrelated_destination
        )
    writer._root_object[NameObject("/Dests")] = destinations
    outlines = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Outlines"),
                NameObject("/Count"): NumberObject(1),
            }
        )
    )
    item = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Title"): TextStringObject(_MARKER_A),
                NameObject("/Parent"): outlines,
                NameObject("/Dest"): destination_name,
            }
        )
    )
    outlines.get_object()[NameObject("/First")] = item
    outlines.get_object()[NameObject("/Last")] = item
    writer._root_object[NameObject("/Outlines")] = outlines
    return writer


def _increment(source: Path, destination: Path) -> None:
    reader = PdfReader(source, strict=True)
    writer = PdfWriter(reader, incremental=True)
    writer.add_metadata({"/Subject": _MARKER_A})
    _write(writer, destination)


def _action(
    kind: str,
    *,
    three_d_annotation: IndirectObject | None = None,
    document_part: IndirectObject | None = None,
    uri: str = _URI,
    action_target: str = _MARKER_A,
    action_target_as_file_specification: bool = False,
    embedded_goto_target: str | None = None,
    embedded_goto_target_as_file_specification: bool = False,
    javascript_stream: IndirectObject | None = None,
) -> DictionaryObject:
    action = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Action"),
            NameObject("/S"): NameObject(kind),
        }
    )
    if kind == "/URI":
        action[NameObject("/URI")] = TextStringObject(uri)
    elif kind == "/JavaScript":
        if javascript_stream is None:
            raise FixtureError("JavaScript action requires a stream")
        action[NameObject("/JS")] = javascript_stream
    elif kind == "/Launch":
        action[NameObject("/F")] = _file_target(
            action_target,
            as_file_specification=action_target_as_file_specification,
        )
    elif kind == "/GoToR":
        action[NameObject("/F")] = _file_target(
            action_target,
            as_file_specification=action_target_as_file_specification,
        )
        action[NameObject("/D")] = TextStringObject(_MARKER_A)
    elif kind == "/SubmitForm":
        action[NameObject("/F")] = _file_target(
            action_target,
            as_file_specification=action_target_as_file_specification,
        )
    elif kind == "/ImportData":
        action[NameObject("/F")] = _file_target(
            action_target,
            as_file_specification=action_target_as_file_specification,
        )
    elif kind == "/SetOCGState":
        action[NameObject("/State")] = ArrayObject()
    elif kind == "/GoTo":
        action[NameObject("/D")] = TextStringObject(_MARKER_A)
    elif kind == "/GoToE":
        action[NameObject("/D")] = TextStringObject(_MARKER_A)
        action[NameObject("/T")] = DictionaryObject(
            {
                NameObject("/R"): NameObject("/C"),
                NameObject("/N"): TextStringObject(_CHILD_DOCUMENT_NAME),
            }
        )
        if embedded_goto_target is not None:
            action[NameObject("/F")] = _file_target(
                embedded_goto_target,
                as_file_specification=embedded_goto_target_as_file_specification,
            )
    elif kind == "/GoTo3DView":
        if three_d_annotation is None:
            raise FixtureError("GoTo3DView action requires a target annotation")
        action[NameObject("/TA")] = three_d_annotation
        action[NameObject("/V")] = NameObject("/D")
    elif kind == "/GoToDp":
        if document_part is None:
            raise FixtureError("GoToDp action requires a document-part target")
        action[NameObject("/Dp")] = document_part
    return action


def _file_target(target: str, *, as_file_specification: bool) -> object:
    if not as_file_specification:
        return TextStringObject(target)
    return DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Filespec"),
            NameObject("/F"): TextStringObject(target),
        }
    )


def _add_navigation_targets(writer: PdfWriter) -> tuple[IndirectObject, IndirectObject]:
    """Add reachable 3D and document-part targets for paired navigation actions."""

    page = writer.pages[0]
    page_reference = page.indirect_reference
    if page_reference is None:
        raise FixtureError("fixture page cannot be referenced")

    three_d_stream = DecodedStreamObject()
    three_d_stream[NameObject("/Type")] = NameObject("/3D")
    three_d_stream[NameObject("/Subtype")] = NameObject("/U3D")
    three_d_stream.set_data(b"")
    three_d_stream_reference = writer._add_object(three_d_stream)
    three_d_annotation = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/3D"),
                NameObject("/Rect"): ArrayObject(
                    [
                        NumberObject(0),
                        NumberObject(0),
                        NumberObject(10),
                        NumberObject(10),
                    ]
                ),
                NameObject("/3DD"): three_d_stream_reference,
            }
        )
    )
    page[NameObject("/Annots")] = ArrayObject([three_d_annotation])

    document_part = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/DPart"),
                NameObject("/Start"): page_reference,
            }
        )
    )
    document_part_root = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/DPartRoot"),
                NameObject("/DPartRootNode"): document_part,
            }
        )
    )
    document_part.get_object()[NameObject("/Parent")] = document_part_root
    page[NameObject("/DPart")] = document_part
    writer._root_object[NameObject("/DPartRoot")] = document_part_root
    return three_d_annotation, document_part


def _child_document_bytes() -> bytes:
    child = PdfWriter()
    child.add_blank_page(width=72, height=72)
    stream = BytesIO()
    child.write(stream)
    return stream.getvalue()


def _add_javascript(writer: PdfWriter, javascript: str) -> None:
    action = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Action"),
                NameObject("/S"): NameObject("/JavaScript"),
                NameObject("/JS"): TextStringObject(javascript),
            }
        )
    )
    names = DictionaryObject()
    names[NameObject("/JavaScript")] = DictionaryObject(
        {
            NameObject("/Names"): ArrayObject(
                [TextStringObject("PDFCABScript"), action]
            )
        }
    )
    writer._root_object[NameObject("/Names")] = names


def _add_acroform(
    writer: PdfWriter, *, form_field: bool, xfa: bool, signature: bool
) -> None:
    fields = ArrayObject()
    if form_field:
        fields.append(
            writer._add_object(
                DictionaryObject(
                    {
                        NameObject("/FT"): NameObject("/Tx"),
                        NameObject("/T"): TextStringObject(_MARKER_A),
                        NameObject("/V"): TextStringObject(_MARKER_A),
                    }
                )
            )
        )
    if signature:
        signature_value = writer._add_object(
            DictionaryObject(
                {
                    NameObject("/Type"): NameObject("/Sig"),
                    NameObject("/ByteRange"): ArrayObject(
                        [
                            NumberObject(0),
                            NumberObject(0),
                            NumberObject(0),
                            NumberObject(0),
                        ]
                    ),
                    NameObject("/Contents"): TextStringObject(_MARKER_A),
                }
            )
        )
        fields.append(
            writer._add_object(
                DictionaryObject(
                    {
                        NameObject("/FT"): NameObject("/Sig"),
                        NameObject("/T"): TextStringObject(_MARKER_A),
                        NameObject("/V"): signature_value,
                    }
                )
            )
        )
    acroform = DictionaryObject({NameObject("/Fields"): fields})
    if xfa:
        acroform[NameObject("/XFA")] = TextStringObject(_MARKER_A)
    writer._root_object[NameObject("/AcroForm")] = acroform


def _add_link_annotation(writer: PdfWriter) -> None:
    annotation = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): ArrayObject(
                    [
                        NumberObject(0),
                        NumberObject(0),
                        NumberObject(10),
                        NumberObject(10),
                    ]
                ),
                NameObject("/Contents"): TextStringObject(_MARKER_A),
            }
        )
    )
    writer.pages[0][NameObject("/Annots")] = ArrayObject([annotation])


def _add_optional_content(writer: PdfWriter) -> None:
    on_group = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/OCG"),
                NameObject("/Name"): TextStringObject(_MARKER_A),
            }
        )
    )
    off_group = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/OCG"),
                NameObject("/Name"): TextStringObject(_MARKER_B),
            }
        )
    )
    configuration = DictionaryObject(
        {
            NameObject("/ON"): ArrayObject([on_group]),
            NameObject("/OFF"): ArrayObject([off_group]),
            NameObject("/BaseState"): NameObject("/Unchanged"),
        }
    )
    writer._root_object[NameObject("/OCProperties")] = DictionaryObject(
        {
            NameObject("/OCGs"): ArrayObject([on_group, off_group]),
            NameObject("/D"): configuration,
        }
    )


def _add_associated_file(writer: PdfWriter) -> IndirectObject:
    embedded_file = DecodedStreamObject()
    embedded_file[NameObject("/Type")] = NameObject("/EmbeddedFile")
    embedded_file.set_data(_MARKER_A.encode("utf-8"))
    embedded_file_reference = writer._add_object(embedded_file)
    file_specification = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Filespec"),
            NameObject("/F"): TextStringObject(_MARKER_A),
            NameObject("/EF"): DictionaryObject(
                {NameObject("/F"): embedded_file_reference}
            ),
            NameObject("/AFRelationship"): NameObject("/Data"),
        }
    )
    file_specification_reference = writer._add_object(file_specification)
    writer._root_object[NameObject("/Names")] = DictionaryObject(
        {
            NameObject("/EmbeddedFiles"): DictionaryObject(
                {
                    NameObject("/Names"): ArrayObject(
                        [
                            TextStringObject("PDFCABAssociated"),
                            file_specification_reference,
                        ]
                    )
                }
            )
        }
    )
    return file_specification_reference
