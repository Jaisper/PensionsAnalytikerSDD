"""Startsiden: rapporten aflæses, så snart den er valgt, og ATP-feltet viser 0 som pladsholder."""
import pytest

from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

pytestmark = pytest.mark.browser


def test_rapporten_aflaeses_uden_knaptryk(side, tmp_path):
    assert side.locator("#pdf-knap, #p-pdf-knap").count() == 0
    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    side.set_input_files("#pdf-fil", str(pdf))
    side.wait_for_selector("#pdf-status p")
    assert side.input_value("#foedselsdato")
    assert side.is_enabled("#pdf-fil")
    assert side.fejl == []


def test_atp_felterne_har_0_som_pladsholder(side):
    assert side.get_attribute("#atp", "placeholder") == "0"
    assert side.get_attribute("#p-atp", "placeholder") == "0"
