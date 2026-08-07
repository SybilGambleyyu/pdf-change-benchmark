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
destinations. Both pages deliberately use the same stored geometry, so an
adapter must retain private page identity rather than infer it from page
contents. The second page is physically present in both PDFs, and the
shared-array variant also retains a non-executing stored reference to the same
indirect successor array. Their public truth requires only the generic
active-content action-sequence change and PFP001; it contains no destination,
action value, position, trigger, or private signature.

The destination-page-state fixture keeps a single GoTo successor and its page
reference fixed while changing only the referenced page's /Rotate value. Its
truth requires only the stored-byte change. This prevents an adapter from
mistaking recursive inspection of an action target's page representation for a
rewrite of the action itself.

The named-destination rebind fixture keeps a document-open JavaScript root and
one local GoTo successor fixed. The successor's D value is a stored string;
the catalog's Names/Dests name tree is inserted before the execution trigger
and maps that same string to a different real page in the candidate. Its truth
requires the generic active-content action-sequence change and PFP001, without
publishing the name, destination, mapping, page, position, or digest.

The two paired named-destination negatives hold that action and its matching
mapping fixed. One changes only the resolved target page's /Rotate value; the
other changes only a different entry in the same destination name tree. Both
require only the stored-byte change. They prevent a compatibility adapter from
mistaking page state or the full shared name tree for the selected GoTo target.

The document-open named-destination fixtures use the same stored name-tree
structure but place the local GoTo action directly in the catalog OpenAction
entry, with no /Next member. The rebind pair requires the generic
active-content payload change and PFP001. Its two paired negatives change only
the resolved target page's /Rotate value or another name-tree mapping, and
therefore require only the stored-byte change. Together they distinguish root
action target evidence from ordinary action-chain evidence without publishing
a name, target, mapping, trigger, or digest.

The direct-navigation fixtures cover three standard roots that do not require a
GoTo action dictionary: a catalog OpenAction explicit destination, a Link
annotation's Dest entry, and an outline item's Dest entry. The Link and outline
rebind pairs keep their stored root and legacy catalog destination name fixed
while moving only that mapping to another real page. The document-open rebind
keeps its actionless explicit destination shape while changing its referenced
page. All three rebinds require the generic active-content payload change and
PFP001. Their paired negatives retain the selected target while changing only
the target page's Rotate state or an unrelated legacy mapping, requiring only
the stored-byte change. They prevent a compatibility adapter from passing by
hashing a target page or the whole destination dictionary, and they never
publish a root, target, mapping, position, or digest.

The PDF 2.0 structure-destination fixtures cover a GoTo action's effective
/SD value, actionless document-open destinations, Link and outline Dest
entries, a legacy and a string-keyed catalog named destination, and a semantic
GoTo action-chain member. Each structure tree has two sibling StructElem
targets beneath a StructTreeRoot. The rebind cases hold the root, its public
inventory, and the surrounding structure tree fixed while changing only the
selected sibling. They require a generic active-content change and PFP001,
without publishing an element identity, destination, position, or digest.
The negatives change only an element's Alt metadata or the /D value overridden
by /SD. They require only the stored-byte change: a compatibility adapter must
follow the effective PDF 2.0 destination, not recurse through arbitrary target
metadata or treat an inactive fallback as selected. The catalog named cases
exercise both a legacy /Dests dictionary and a /Names /Dests name tree, whose
mapped dictionary contains both /D and /SD.

The PDF 2.0 remote-GoTo fixtures use an action's effective /SD value at a
document-action root and a semantic /Next member. Its first array entry is a
synthetic opaque byte-string structure identifier for a remote document; the
benchmark never opens that document. The rebind pairs hold their action root,
file specification, public inventory, and /D fallback fixed while changing
only that identifier. Their truth requires the generic root payload or
action-sequence signal and PFP001. The paired fallback negatives change only
the /D value overridden by /SD and require only stored_pdf_bytes_changed. A
separate no-/SD pair changes /D and requires the generic active-content payload
signal and PFP001. A byte-reencoding pair uses distinct identifier bytes that
the pinned parser decodes to the same text, so an adapter must retain the
original bytes. Together these fixtures require an adapter to preserve effective
/SD precedence without disclosing a remote file, identifier, destination,
position, or private digest.

The Launch, remote- and embedded-GoTo, SubmitForm, and ImportData
target-rewrite fixtures also retain their action type and public inventory.
They alter only inert file or endpoint targets, including direct and FileSpec
representations. Their truth remains generic so an adapter must report a
private payload-change signal, rather than exposing a file name or endpoint.

The Associated Files fixture holds the embedded stream and file specification
constant, then adds a document-level association. It tests association topology
without exposing the file name, payload, or relationship value in public truth.
