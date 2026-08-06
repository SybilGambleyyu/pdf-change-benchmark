"""Stable error types for PDFCAB."""


class PdfCabError(Exception):
    """Base class for expected PDFCAB failures."""


class FixtureError(PdfCabError):
    """A fixture tree is incomplete, malformed, or inconsistent."""


class AdapterError(PdfCabError):
    """A supplied tool could not be invoked or returned invalid output."""


class OutputError(PdfCabError):
    """A requested benchmark output cannot be safely written."""
