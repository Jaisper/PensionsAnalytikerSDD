"""Feature 031 — forsikringerne fra PensionsInfo-rapporten i overblikket: afsnittet "Hvis du bliver syg
eller dør" med en gruppe pr. type. Syntetisk rapport med opdigtede data."""
import pytest

from tests.browser.conftest import koer_guide, vent_paa_planen

pytestmark = pytest.mark.browser

AFSNIT = "#forsikringer"


@pytest.fixture
def med_forsikringer(side, tmp_path):
    from tests.app.pensionsinfo_syntetisk import RAPPORT_MED_FORSIKRINGER_PDF

    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_MED_FORSIKRINGER_PDF)
    koer_guide(side, pdf)
    vent_paa_planen(side)
    return side


def test_afsnittet_viser_dækningerne_pr_type(med_forsikringer):
    s = med_forsikringer
    assert s.is_visible(AFSNIT)
    titler = s.locator(f"{AFSNIT} h3").all_inner_texts()
    assert titler == ["Hvis du dør", "Hvis du mister arbejdsevnen", "Hvis du får en kritisk sygdom", "Sundhedsforsikring"]
    tekst = s.inner_text(AFSNIT)
    assert "1.540.000 kr. på én gang" in tekst                   # summen ved død
    assert "60.000 kr. om året" in tekst                         # ægtefællepensionen
    assert "Begunstiget oplyst" in tekst and "skattefri" in tekst
    assert "300.000 kr. om året" in tekst and "til du er 67 år" in tekst
    assert "150.000 kr. på én gang" in tekst
    assert "Børn: 50.000 kr. på én gang" in tekst                # kritisk sygdom for børn
    assert "Testselskab" in tekst


def test_ingen_forsikringer_intet_afsnit(resultat):
    assert resultat.is_hidden(AFSNIT)


def test_axe(med_forsikringer):
    s = med_forsikringer
    s.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = s.evaluate("async () => (await axe.run('#forsikringer', {runOnly: "
                      "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
