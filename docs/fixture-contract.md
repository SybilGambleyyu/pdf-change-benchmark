# Fixture contract

Each fixture directory contains a baseline PDF, a candidate PDF, and a public
truth JSON document. Fixture bytes are deterministically generated from
src/pdfcab/build.py using pypdf 6.15.0.

All pairs start from a single blank page. Stored markers are synthetic and
inert. URI-like action values use the reserved example.invalid domain. The
benchmark never opens, renders, executes, follows, decrypts, or interprets a
stored payload.

Truth documents are intentionally incomplete descriptions of PDFs. They state
which public PDFFence change kinds and policy rule IDs are expected; they do
not contain the underlying source values. The benchmark is therefore useful
for static-signal regressions without becoming a data-exfiltration corpus.

An adapter must compare the exact set of PDFFence change kinds for every
fixture. This is a product-specific compatibility contract, not an assertion
that another tool should expose the same result or that an uncatalogued PDF
surface is safe.

The optional-content fixture covers only catalog-declared groups and
configuration topology. It does not claim that a viewer displays a particular
layer state or that page content uses the declared groups.

The GoTo-to-embedded-GoTo fixture keeps the action dictionary count fixed and
retains an embedded child PDF in both files. Only the candidate action adds a
structurally shaped target for that child while changing the fixed action type.
It tests that an action inventory does not collapse ordinary navigation and
navigation into embedded documents.

The GoTo3DView-to-GoToDp fixture keeps a page-attached 3D annotation and a
catalog document-part hierarchy on both sides. The baseline action references
the 3D annotation; the candidate action references the document part. It tests
that an inventory does not collapse those two standard action types while
keeping their surrounding targets reachable and unchanged.

The JavaScript and URI payload-rewrite fixtures keep their respective action
types and public inventory fixed while changing only inert stored payload
material. The JavaScript stream pair retains exactly the same raw stream bytes
while changing its ASCII-hex decoding configuration; each side remains a
syntactically valid JavaScript stream with different decoded material. Their
truth records require a generic active-content payload-change signal and the
existing active-content policy ID, never a source value or digest.

The JavaScript trigger-rebinding fixture retains the same two inert script
values and action inventory while exchanging their document-open and
catalog-will-close bindings. Its generic truth distinguishes evidence of
execution-context reassignment from an ordinary payload rewrite without
identifying either script or a private digest.

The JavaScript action-chain fixtures retain a document-open JavaScript action
and exchange the positions of two successor actions in its stored /Next array.
The shared-array variant also retains a non-executing stored reference to that
same indirect array. Both fixtures require a generic private payload-change
signal and PFP001, without publishing a script, sequence position, or digest.

The action-subtype chain fixtures retain the same JavaScript root and
aggregate action inventory while exchanging GoTo and SetOCGState successors.
The shared-array variant also retains a non-executing stored reference to the
same indirect successor array. Their public truth requires only the generic
active-content execution-order change and PFP001; it contains no action type,
position, trigger, or private signature.

The same-subtype chain fixtures retain the same JavaScript root, two GoTo
successors, and public action inventory while exchanging distinct valid page
destinations. The second page is physically present in both PDFs, and the
shared-array variant also retains a non-executing stored reference to the same
indirect successor array. Their public truth requires only the generic
active-content action-sequence change and PFP001; it contains no destination,
action value, position, trigger, or private signature.

The Launch, remote- and embedded-GoTo, SubmitForm, and ImportData
target-rewrite fixtures also retain their action type and public inventory.
They alter only inert file or endpoint targets, including direct and FileSpec
representations. Their truth remains generic so an adapter must report a
private payload-change signal, rather than exposing a file name or endpoint.

The Associated Files fixture holds the embedded stream and file specification
constant, then adds a document-level association. It tests association topology
without exposing the file name, payload, or relationship value in public truth.
