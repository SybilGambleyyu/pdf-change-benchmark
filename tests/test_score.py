"""Process-bound PDFFence adapter scoring coverage."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from pdfcab.errors import AdapterError
from pdfcab.score import score_pdffence

_FAKE_PDFFENCE = Path(__file__).with_name("fake_pdffence.py")


def test_process_bound_adapter_matches_every_fixture():
    report = score_pdffence([sys.executable, _FAKE_PDFFENCE])

    assert report.passed_count == len(report.fixture_scores)
    assert all(score.passed for score in report.fixture_scores)


def test_adapter_errors_are_generic_and_do_not_echo_output(tmp_path):
    malformed = tmp_path / "malformed_adapter.py"
    marker = "PDFCAB_ADAPTER_SECRET_DO_NOT_LEAK"
    malformed.write_text(f"print({marker!r})\n", encoding="utf-8")

    with pytest.raises(AdapterError) as error:
        score_pdffence([sys.executable, malformed])

    assert marker not in str(error.value)
