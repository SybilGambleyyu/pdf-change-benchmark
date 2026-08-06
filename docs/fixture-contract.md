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

The Associated Files fixture holds the embedded stream and file specification
constant, then adds a document-level association. It tests association topology
without exposing the file name, payload, or relationship value in public truth.
