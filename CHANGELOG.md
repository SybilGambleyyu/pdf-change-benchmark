# Changelog

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
