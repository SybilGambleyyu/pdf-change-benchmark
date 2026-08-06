# Changelog

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
