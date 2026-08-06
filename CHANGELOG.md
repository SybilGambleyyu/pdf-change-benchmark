# Changelog

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
