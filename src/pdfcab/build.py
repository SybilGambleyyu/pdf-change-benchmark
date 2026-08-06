"""Deterministic source for PDFCAB's synthetic paired-PDF fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass
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
_URI = "https://example.invalid/pdfcab"
_PASSWORD = "pdfcab-inert-password"


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
        "active.javascript_payload_rewritten",
        "active_content",
        "A JavaScript payload changes while its public action inventory is fixed.",
        "javascript_payload_rewritten",
        ("stored_pdf_bytes_changed",),
        (),
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
    elif mutation == "javascript_payload_rewritten":
        _write(_writer(javascript=_MARKER_A), baseline)
        _write(_writer(javascript=_MARKER_B), candidate)
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
    embedded_file: bool = False,
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
        action_reference = writer._add_object(_action(action))
        writer._root_object[NameObject("/OpenAction")] = action_reference
    if embedded_file:
        writer.add_attachment(f"{_MARKER_A}.txt", _MARKER_A.encode("utf-8"))
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


def _increment(source: Path, destination: Path) -> None:
    reader = PdfReader(source, strict=True)
    writer = PdfWriter(reader, incremental=True)
    writer.add_metadata({"/Subject": _MARKER_A})
    _write(writer, destination)


def _action(kind: str) -> DictionaryObject:
    action = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Action"),
            NameObject("/S"): NameObject(kind),
        }
    )
    if kind == "/URI":
        action[NameObject("/URI")] = TextStringObject(_URI)
    elif kind == "/Launch":
        action[NameObject("/F")] = TextStringObject(_MARKER_A)
    elif kind == "/SetOCGState":
        action[NameObject("/State")] = ArrayObject()
    return action


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
