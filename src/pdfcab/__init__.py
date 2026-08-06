"""PDF Change Assurance Benchmark."""

__version__ = "0.2.0"

from pdfcab.score import score_pdffence
from pdfcab.validate import verify_fixture_tree

__all__ = ["__version__", "score_pdffence", "verify_fixture_tree"]
