# Changelog

## 1.21.0 (2026-08-06)

- Add an own-revision semantic-signature control: both ranges are stale with
  respect to later current file ends, but only the baseline reaches its
  signature's own incremental-revision footer. Its generic own-revision event
  requires PFP013 without treating a correct historical signature as a
  current-file boundary.
- Increase the deterministic fixture set from 157 to 158 pairs.

## 1.20.0 (2026-08-06)

- Add a semantic-signature direct-value control whose current ByteRange and
  exact direct `/Contents` boundary remain intact while one top-level signature
  value becomes indirect. Its generic direct-value change requires PFP012;
  PFP009 through PFP011 remain quiet.
- Increase the deterministic fixture set from 156 to 157 pairs.

## 1.19.0 (2026-08-06)

- Add a semantic signature control where both ByteRanges still reach the
  current physical end, while the candidate's sole gap is one byte wider than
  its direct `/Contents` token. Its generic coverage change requires PFP011,
  while PFP009 and PFP010 correctly remain quiet.
- Correct the prior synthetic signature helpers so their baseline ByteRanges
  exclude the actual signature `/Contents` token rather than an earlier PDF
  token. No fixture truth discloses offsets, contents, certificates, or hashes.
- Increase the deterministic fixture set from 155 to 156 pairs.

## 1.18.0 (2026-08-06)

- Add a semantic-signature stale-boundary control whose baseline and candidate
  both have a well-formed ByteRange before the current physical file end. It
  requires PFP010 without a coverage-change event, proving that an adapter can
  enforce a current boundary even without a known-good baseline.
- Increase the deterministic fixture set from 154 to 155 pairs.

## 1.17.0 (2026-08-06)

- Add a semantic signature ByteRange control: a field-root range reaches the
  original file end, then a valid incremental update leaves that range at the
  prior revision. It requires the generic coverage event and PFP009 without
  publishing offsets, contents, certificates, or hashes.
- Add a private PieceInfo `/Type /Sig` and `/ByteRange` lookalike addition. It
  requires reachability plus stored bytes only, preventing an adapter from
  treating arbitrary private data as signature structure.
- Increase the deterministic fixture set from 152 to 154 pairs.

## 1.16.0 (2026-08-06)

- Add two private-inventory controls: one changes a PieceInfo action-shaped
  dictionary's subtype, and one adds a private additional-action container and
  action. Neither has a semantic action owner.
- Require the subtype rewrite to report stored bytes alone and the addition to
  report only reachability plus stored bytes. Both reject an active-content
  inventory signal without exposing an action value or private path.
- Increase the deterministic fixture set from 150 to 152 pairs.

## 1.15.0 (2026-08-06)

- Add five passive action-key controls: four catalog PieceInfo private values
  shaped like `/A`, `/AA`, `/NA`, or `/PA` triggers, plus a real Link
  annotation's archived Web Capture `/PA` URI. Each changes stored bytes alone.
- Add six positive URI-action roots through actual page additional-action,
  Link, AcroForm field, outline, and presentation-step `/NavNode` paths. They
  retain the public action inventory while requiring generic active-content
  evidence and PFP001.
- Increase the deterministic fixture set from 139 to 150 pairs. The new cases
  distinguish a semantic document path from an action-looking key name without
  exposing a URI, binding, payload, or private fingerprint.

## 1.14.0 (unreleased)

- Add eleven standard-form catalog PieceInfo negatives whose private data is
  shaped like Thread, URI, Sound, Movie, Hide, Named, SubmitForm, ResetForm,
  Rendition, Trans, or RichMediaExecute actions. Each rewrites a selected
  behavior-bearing field while no standard action root reaches it, requiring a
  stored-byte change alone.
- The controls increase the deterministic suite from 128 to 139 fixture pairs
  and prevent adapters from treating private application data as executable
  action behavior.

## 1.13.0 (unreleased)

- Add eleven direct document-action behavior-field regressions for `/Thread`,
  `/URI`, `/Sound`, `/Movie`, `/Hide`, `/Named`, `/SubmitForm`, `/ResetForm`,
  `/Rendition`, `/Trans`, and `/RichMediaExecute`. Each keeps the action type
  and public inventory fixed while changing one standardized behavior-bearing
  field, requiring `active_content_payload_changed` and PFP001.
- Cover raw stored bytes for the top-level `/Sound` stream without requiring a
  payload decoder. The fixtures increase the published suite from 117 to 128
  deterministic pairs.

## 1.12.0 (unreleased)

- Add four GoToE hierarchy-scope regressions for document-action roots and
  semantic action-chain members. They keep action fields fixed while rewriting
  a source EmbeddedFiles mapping for an external-root child or nested child;
  each requires stored_pdf_bytes_changed alone.
- The cases prevent a compatibility adapter from resolving every /T /R /C /N
  target through the source document's catalog. A same-root top-level mapping
  remains covered by the existing positive regressions, while other-document
  mappings must not generate a false active-content finding.

## 1.11.0 (unreleased)

- Add twelve GoToE FileAttachment-target regressions for document-action roots
  and semantic action-chain members. Eight positives cover numeric and named
  /P page selectors paired with numeric and NM /A annotation selectors. They
  keep the stored Target dictionary and public action inventory fixed while the
  selected attachment FileSpec is rebound, requiring the appropriate generic
  active-content signal and PFP001.
- Add selected FileSpec-description and annotation-Contents negatives at both
  roots. They require stored_pdf_bytes_changed alone, preventing adapters from
  passing via recursive hashes of descriptive FileSpec fields, FileAttachment
  metadata, or unrelated page annotations.

## 1.10.0 (unreleased)

- Add ten GoToE target-semantics regressions for document-action roots and
  semantic action-chain members. Selected catalog EmbeddedFiles rebinding and
  direct action FileSpec target rewrites require the appropriate generic
  active-content signal and PFP001 while public action inventory remains fixed.
- Keep selected and direct FileSpec descriptions, plus unrelated
  EmbeddedFiles-map rewrites, as stored-byte-only negatives. The pairs prevent
  a compatibility adapter from recursively hashing descriptive metadata or an
  entire name tree instead of the selected target.

## 1.9.0 (unreleased)

- Add eight GoTo3DView regressions for document-action roots and semantic
  action-chain members. Rebinding a page-attached 3D target or rewriting the
  selected view requires the corresponding generic active-content signal and
  PFP001 while public inventory remains fixed.
- Deliberately omit the optional annotation /P page reference in each target
  rebind pair, and keep the two target annotations otherwise indistinguishable.
  Fixed target metadata and target-page rotation remain stored-byte-only
  negatives, preventing broad recursive target hashes from passing the suite.

## 1.8.0 (unreleased)

- Add ten SetOCGState regressions for document-action roots and semantic
  action-chain members. Rebinding a selected catalog OCG, rewriting an ON/OFF
  operation, or changing PreserveRB requires the appropriate generic
  active-content signal and PFP001.
- Keep OCG Name and Usage metadata fixed as byte-only negatives, and normalize
  an omitted PreserveRB to its specified true default. These cases prevent an
  adapter from recursively hashing group metadata or falsely treating an
  explicit default as a semantic change.

## 1.7.0 (unreleased)

- Add six PDF 2.0 GoToDp regressions covering a document-action root and a
  semantic /Next member. The two rebind pairs require the corresponding
  generic active-content signal and PFP001 while their public action inventory
  remains fixed.
- Add fixed-target DPart-metadata and target-page-state negatives for each
  root. They require stored_pdf_bytes_changed alone, preventing an adapter
  from passing by recursively hashing DPart metadata or a referenced page
  instead of binding the selected DPart-tree position.

## 1.6.0 (unreleased)

- Add six PDF 2.0 remote-GoTo regressions for effective /SD precedence at a
  document-action root and a semantic /Next member. The remote /SD values use
  synthetic opaque byte-string identifiers and do not require opening a target
  document.
- Require stored_pdf_bytes_changed alone for overridden remote /D fallback
  rewrites; require the appropriate generic active-content signal and PFP001
  for remote /SD rebinds; and retain a no-/SD remote /D rewrite as an
  active-content regression. One rebind preserves the parser-decoded text while
  changing the original identifier bytes, guarding against parser-text
  collisions.

## 1.5.0 (unreleased)

- Add thirteen PDF 2.0 structure-destination regressions covering effective
  /SD precedence over /D in catalog GoTo actions, actionless document-open
  destinations, Link annotations, outline items, catalog named destinations,
  and semantic GoTo action chains. The five rebind pairs retain the stored
  root while moving only the selected structure-tree element, requiring the
  appropriate generic active-content signal and PFP001.
- Add target-element-metadata and overridden-fallback negatives. They require
  only stored_pdf_bytes_changed, preventing broad recursive hashes of a
  structure element or its target page, and preventing an adapter from treating
  an inactive /D fallback as the effective PDF 2.0 destination.

## 1.4.0 (unreleased)

- Add eight direct-navigation regressions for an actionless document-open
  destination, a Link Dest entry, and an outline Dest entry. The three rebind
  pairs retain the stored root and public inventory while moving only the
  selected target, requiring generic active_content_payload_changed and
  PFP001.
- Add target-page-state and unrelated-legacy-mapping negatives for the Link
  and outline roots, plus a target-page-state negative for document open. They
  require only stored_pdf_bytes_changed, preventing broad page or map hashes
  from passing the rebind cases.

## 1.3.0 (unreleased)

- Add a document-open named local-GoTo rebind pair. Its stored action and
  public action inventory remain fixed while the matching catalog name-tree
  value moves to a different real page. It requires the generic
  active_content_payload_changed signal and PFP001 without exposing a target.
- Add root-action target-page-state and unrelated-name-tree negatives. Both
  require only stored_pdf_bytes_changed, preventing broad recursive target or
  whole-tree fingerprints from passing the rebind case.

## 1.2.0 (unreleased)

- Add a named local-GoTo destination rebind pair. The action's stored D value,
  public action inventory, selected payload evidence, and successor order all
  remain fixed while its catalog name-tree mapping moves to another real page.
  It requires the generic active_content_action_sequence_changed signal and
  PFP001 without disclosing a destination name or target.
- Add two selectivity regressions: a changed target page rotation and a changed
  unrelated name-tree mapping. Both require only stored_pdf_bytes_changed, so
  an adapter cannot pass by recursively hashing target pages or the entire
  destination name tree.

## 1.1.0 (unreleased)

- Add normal and shared-array same-subtype action-chain order pairs. Their two
  GoTo successors point at distinct real pages and exchange positions while
  public action inventory, selected payload evidence, and subtype-order
  evidence remain fixed. They require the generic
  active_content_action_sequence_changed signal plus PFP001.
- Add a destination-page-state regression that changes only the referenced
  page's rotation. It requires only the stored-byte signal, preventing an
  adapter from misattributing a target page's own representation to a fixed
  action-chain member.

## 1.0.0 (unreleased)

- Add normal and shared-array action-subtype order pairs. They exchange GoTo
  and SetOCGState successors while retaining fixed action inventory and
  selected payload evidence, requiring the generic
  active_content_execution_order_changed signal plus PFP001.

## 0.9.0 (unreleased)

- Add normal and shared-array JavaScript action-chain reorder pairs. Both keep
  their public action inventory fixed while switching successor positions and
  require the generic private active-content signal plus PFP001.

## 0.8.0 (unreleased)

- Add a fixed-inventory JavaScript trigger-rebinding pair. The pair exchanges
  document-open and document-close script bindings and requires the generic
  active-content payload-change signal and PFP001 without exposing a script or
  digest in fixture truth.

## 0.7.0 (unreleased)

- Add fixed-inventory target-rewrite pairs for Launch, remote and embedded
  GoTo, SubmitForm, and ImportData actions. They require the generic
  active-content payload change and PFP001 without exposing a target in
  fixture truth.

## 0.6.0 (unreleased)

- Add URI, JavaScript text, and JavaScript stream-decoding-configuration
  rewrite pairs. Each requires a generic active-content payload change plus
  PFP001 while keeping public action inventory fixed.

## 0.5.0 (unreleased)

- Add a paired GoTo3DView-to-GoToDp regression fixture. Both sides retain a
  reachable 3D annotation and document-part hierarchy so it isolates the
  action-type substitution.

## 0.4.0 (unreleased)

- Add an action-subtype swap pair: an ordinary GoTo action is replaced by an
  embedded-document GoTo action while the action dictionary count remains
  fixed.

## 0.3.0 (unreleased)

- Add an association-only Associated Files pair that holds the embedded stream
  and file specification fixed while adding the document-level link.

## 0.2.0 (unreleased)

- Add a catalog optional-content topology fixture with public expectations for
  PDFFence policy rules PFP007 and PFP008.
- Add a SetOCGState action fixture to distinguish it from generic known
  actions.
- Extend the process-bound PDFFence adapter contract for optional-content
  change and policy identifiers.
