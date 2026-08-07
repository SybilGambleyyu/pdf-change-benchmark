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

The SetOCGState fixtures use two catalog-declared optional-content groups and
a default-configuration RBGroups entry. Root and semantic-chain positives
either choose the other catalog group, change the ordered ON/OFF operation, or
change PreserveRB. The paired negatives keep the selected group and operation
fixed while changing only Name or Usage metadata, or add explicit
PreserveRB=true where it was absent. Positives require the appropriate generic
active-content signal and PFP001; negatives require only the stored-byte
change. No truth record publishes a group identity, metadata value, operation,
radio-button setting, action position, or private fingerprint.

The GoTo-to-embedded-GoTo fixture keeps the action dictionary count fixed and
retains an embedded child PDF in both files. Only the candidate action adds a
structurally shaped target for that child while changing the fixed action type.
It tests that an action inventory does not collapse ordinary navigation and
navigation into embedded documents.

The GoToE target-semantics fixtures use two synthetic FileSpecs in the catalog
Names/EmbeddedFiles name tree and a child Target dictionary that selects one
by its binary name. Document-action-root and semantic-chain positives either
rebind that selected name to the other FileSpec or rewrite a direct action
FileSpec target. Their paired negatives keep the selected target fixed while
changing only a selected or direct FileSpec description, or the unrelated
name-tree entry. The positives require the corresponding generic active-content
signal and PFP001; negatives require only the stored-byte change. The fixtures
do not publish a name, file target, stream value, description, position, or
private fingerprint.

The GoToE FileAttachment target fixtures use two page-attached FileAttachment
annotations per page and a child Target dictionary with /R /C, /P, and /A but
no /N. The eight positives hold /P and /A fixed while rebinding the selected
attachment through each standard selector combination: zero-based page/index,
zero-based page/NM, named page/index, and named page/NM. Both selected
FileSpecs retain the same filename and description while their inert embedded
stream bytes differ. The four negatives hold the selected attachment fixed and
change only its FileSpec description or annotation Contents. Positives require
the corresponding generic active-content signal and PFP001; negatives require
only the stored-byte change. No truth record publishes a selector, page,
annotation, file target, stream value, description, or private fingerprint.

The GoToE hierarchy-scope fixtures keep every action field fixed while
rewriting a source catalog EmbeddedFiles mapping that cannot define the target:
either the action has a fixed external-root FileSpec or the rewritten name is
inside a nested Target beneath an already-selected child. Both document-action
and semantic-chain pairs require only the stored-byte change. The original
same-root top-level named-child fixtures remain positive controls. No truth
record publishes a target hierarchy, name, file target, stream value, or
private fingerprint.

The GoTo3DView-to-GoToDp fixture keeps a page-attached 3D annotation and a
catalog document-part hierarchy on both sides. The baseline action references
the 3D annotation; the candidate action references the document part. It tests
that an inventory does not collapse those two standard action types while
keeping their surrounding targets reachable and unchanged.

The GoTo3DView target-binding fixtures use two page-attached 3D annotations.
The document-open and semantic action-chain positives either select the other
annotation or rewrite /V while retaining public action inventory. Target-rebind
pairs deliberately omit the annotation's optional /P page reference and make
the two target annotations otherwise indistinguishable, so an adapter must
prove target membership through the catalog page tree and the page's Annots
array. The paired negatives keep the selection fixed while changing annotation
metadata or page Rotate state. Positives require the appropriate generic
active-content signal and PFP001; negatives require only the stored-byte
change. No truth record publishes a target identity, page or annotation
position, annotation contents, selected view, or private fingerprint.

The GoToDp target-binding fixtures use a catalog DPartRoot, its DPartRootNode,
and nested DParts arrays containing two leaf document parts. The document-open
and semantic action-chain rebind pairs choose different leaves while retaining
their public action inventory. Their paired negatives keep the selected leaf
fixed while changing only its DPM metadata or its referenced page's Rotate
state. The positives require the appropriate generic active-content signal and
PFP001; the negatives require only the stored-byte change. No truth record
publishes a DPart identity, metadata value, page reference, tree position, or
private fingerprint.

The JavaScript and URI payload-rewrite fixtures keep their respective action
types and public inventory fixed while changing only inert stored payload
material. The JavaScript stream pair retains exactly the same raw stream bytes
while changing its ASCII-hex decoding configuration; each side remains a
syntactically valid JavaScript stream with different decoded material. Their
truth records require a generic active-content payload-change signal and the
existing active-content policy ID, never a source value or digest.

The direct action behavior-field fixtures cover `/Thread`, `/URI`, `/Sound`,
`/Movie`, `/Hide`, `/Named`, `/SubmitForm`, `/ResetForm`, `/Rendition`,
`/Trans`, and `/RichMediaExecute` at the catalog document-open root. Each pair
keeps the action type and public action inventory fixed while changing one
standardized behavior-bearing field: respectively `/D`, `/IsMap`, raw
top-level `/Sound` stream bytes, `/T`, `/T`, `/N`, `/CharSet`, `/Fields`,
`/JS`, `/Trans`, or `/CMD`. The `/Sound` pair requires comparison of its raw
stored stream representation; it does not require decoding the payload. Every
truth record requires generic `active_content_payload_changed` and PFP001, and
publishes no action value, stream bytes, target, command, or private digest.

The paired PieceInfo controls place the same action-shaped dictionaries beneath
a catalog `/PieceInfo` application's `/LastModified` and `/Private` data, not
a standard action trigger. Their selected fields change exactly as in the
direct-root positives, but all require `stored_pdf_bytes_changed` alone. They
prevent an adapter from treating application-private data as an action simply
because a dictionary happens to contain `/Type /Action` and `/S`. No truth
record publishes a private application key, date, action value, stream bytes,
or digest.

The semantic-root controls extend that boundary to trigger-looking keys. Four
catalog PieceInfo private values are placed beneath `/A`, `/AA`, `/NA`, or
`/PA` and retain an action-shaped value; each requires only the stored-byte
change. A real Link annotation's `/PA` archived Web Capture URI is also
byte-only. The matching positive URI-action cases are reachable, respectively,
through a page `/AA`, Link `/A`, AcroForm field `/AA`, outline-item `/A`, and
page `/PresSteps` `/NavNode` `/NA` or `/PA`. They require the generic
active-content payload signal and PFP001 while keeping the public action
inventory fixed. No truth record discloses a URI, private owner path, trigger,
or fingerprint.

The private-inventory controls test the corresponding public-count boundary.
One rewrites a private action-shaped dictionary from one action subtype to
another while keeping its object count fixed. The other adds a private `/AA`
container and its action. The rewrite requires stored bytes alone; the addition
requires reachability plus stored bytes. Neither has a semantic action owner,
so neither may produce an active-content inventory change or PFP001. No truth
record publishes an action subtype, owner path, action value, or fingerprint.

The signature-boundary controls use a field-root `/Type /Sig` dictionary whose
`/ByteRange` starts at byte zero and reaches the original physical file end.
An incremental update then appends a later revision without changing that
signature dictionary. Its truth requires generic revision, reachability,
metadata, stored-byte, and signature-coverage changes plus PFP009; it does not
claim signature validity or disclose an offset, signature content, certificate,
or hash. A second pair begins with that field-root range already behind the
current file end and appends another distinct incremental update, so its public
truth requires PFP010 without a signature-coverage change. A paired private
PieceInfo `/Type /Sig` and `/ByteRange` addition has no form-field or
catalog-permission owner and requires reachability plus stored bytes only.
Together they distinguish a standard signature root and current file boundary
from an arbitrary signature-shaped dictionary without deciding validity or
whether an update is allowed.

The Contents-boundary control starts with a current-file two-pair ByteRange
whose one omitted gap exactly matches the direct hexadecimal `/Contents`
token. Its candidate keeps the same physical file end but widens that gap by
one byte before the token. The truth requires the generic coverage event and
PFP011 only: PFP009 sees no current-file regression, and PFP010 sees a current
file boundary on both sides. It exposes neither an offset nor any signature,
certificate, digest, or trust result.

The direct-value control keeps that two-pair current-file ByteRange and exact
direct `/Contents` gap on both sides. Its candidate changes one top-level
signature-dictionary value from direct to indirect while keeping the target
object otherwise reachable through the catalog. Its truth requires the generic
direct-value inventory event and PFP012 only; PFP009 through PFP011 remain
quiet. It does not claim signature validity or disclose an object reference,
value, offset, certificate, digest, or trust result.

The own-revision control starts each side with a field-root signature and then
appends one later incremental update, so neither range reaches the current
physical file end. The baseline range still reaches the original signing
revision's footer; the candidate stops short of that footer while retaining a
well-formed layout and the same stale current-file status. Its truth requires
only the own-revision inventory event and PFP013. It therefore distinguishes
an older signature that remains structurally bounded to its signing revision
from an arbitrary earlier endpoint, without publishing an object reference,
revision boundary, range, signature content, certificate, digest, or trust
result.

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
