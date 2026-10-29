"""Feature 025 — stopalderen som et punkt i tidslinjen under grafen. Den syntetiske rapport
(tidligste udbetaling 60 for o1, folkepensionsalder 69) med løn og stopalder 64."""
import pytest

from tests.browser.conftest import koer_guide, vent_paa_planen
from tests.browser.test_tidslinje import marker_resultat, traek, vent_paa_ny_beregning

pytestmark = pytest.mark.browser

PUNKT = '.tl-raekke[data-id="stopalder"] .tl-bjaelke'


@pytest.fixture
def med_loen(side, tmp_path):
    from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    side.set_input_files("#pdf-fil", str(pdf))
    side.wait_for_selector("#pdf-status p")
    side.fill("#loen-maaned", "40000")
    side.fill("#stop-alder", "64")
    koer_guide(side)
    vent_paa_planen(side)
    return side


def stopalder(side):
    return side.evaluate("tilstand.aktuelleSvar.person.loen.stop_alder")


def test_punktet_staar_ved_stopalderen_med_grænser_fra_kernen(med_loen):
    punkt = med_loen.locator(PUNKT)
    assert punkt.get_attribute("role") == "slider"
    assert punkt.get_attribute("aria-valuenow") == "64"
    assert punkt.get_attribute("aria-valuemin") == "60"
    assert punkt.get_attribute("aria-valuemax") == "69"
    assert punkt.get_attribute("aria-label") == "Du stopper med at arbejde"
    assert med_loen.locator(".tl-raekke").first.get_attribute("data-id") == "stopalder"


def test_traek_punktet_flytter_stopalderen_og_regner_igen(med_loen):
    marker_resultat(med_loen)
    traek(med_loen, med_loen.locator(PUNKT), -2)
    assert stopalder(med_loen) == 62
    assert med_loen.input_value("#stop-alder") == "62"
    vent_paa_ny_beregning(med_loen)
    assert "62 år" in med_loen.inner_text('.tl-raekke[data-id="stopalder"] .tl-hoved')
    assert med_loen.fejl == []


def test_grænser_og_tastatur(med_loen):
    traek(med_loen, med_loen.locator(PUNKT), -10)
    assert stopalder(med_loen) == 60
    med_loen.locator(PUNKT).focus()
    med_loen.keyboard.press("End")
    assert stopalder(med_loen) == 69
    med_loen.keyboard.press("ArrowLeft")
    assert stopalder(med_loen) == 68


def test_klik_viser_knapper(med_loen):
    med_loen.locator(PUNKT).click()
    raekke = med_loen.locator('.tl-raekke[data-id="stopalder"]')
    raekke.get_by_role("button", name="Stop 1 år tidligere").click()
    assert stopalder(med_loen) == 63


def test_ingen_raekke_uden_loen(resultat):
    assert resultat.locator('.tl-raekke[data-id="stopalder"]').count() == 0


def test_axe(med_loen):
    med_loen.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    med_loen.locator(PUNKT).click()
    fejl = med_loen.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
