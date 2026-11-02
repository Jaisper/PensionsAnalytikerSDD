"""Feature 031/034 — forsikringerne fra PensionsInfo-rapporten som kort i "Hvis du bliver syg eller dør":
et kort pr. situation med beløbet efter skat. Syntetisk rapport med opdigtede data."""
import re

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
    side.wait_for_selector(f"{AFSNIT} .fkort")
    return side


def kort(side, id_):
    return side.locator(f".fkort:has(h3#fkort-{id_})")


def test_et_kort_pr_situation(med_forsikringer):
    s = med_forsikringer
    assert s.is_visible(AFSNIT)
    titler = s.locator(f"{AFSNIT} .fkort h3").all_inner_texts()
    assert titler == ["Hvis du dør", "Hvis du mister arbejdsevnen", "Hvis du får en kritisk sygdom", "Sundhedsforsikring"]


def test_doed_efter_afgift(med_forsikringer):
    k = kort(med_forsikringer, "doed")
    assert k.locator(".fkort__tal").inner_text() == "1.524.000 kr."    # ATP 40.000 med 40 % afgift + 1.500.000 skattefri
    assert "1.540.000 kr. før skat" in k.inner_text()
    assert "Desuden 60.000 kr. om året før skat (36.000 kr. efter afgift)." in k.inner_text()
    assert "Nogle dækninger ophører fra 67 år" in k.inner_text()
    assert k.locator(".fkort__selskab").all_inner_texts() == ["Testselskab", "ATP"]
    assert "Begunstiget oplyst" in k.locator(".fkort__detaljer").text_content()


def test_arbejdsevne_pr_maaned_efter_skat(med_forsikringer):
    k = kort(med_forsikringer, "erhvervsevne")
    tal = int(re.sub(r"\D", "", k.locator(".fkort__tal").inner_text()))
    assert 0 < tal < 25_000                                            # 300.000 om året før skat
    assert tal % 100 == 0                                              # et skøn: hele hundrede
    assert "om måneden efter skat · 25.000 kr. før skat" in k.inner_text()
    assert "Dækker til 67 år" in k.inner_text()


def test_kritisk_sygdom_og_boern(med_forsikringer):
    k = kort(med_forsikringer, "kritisk_sygdom")
    assert k.locator(".fkort__tal").inner_text() == "150.000 kr."
    assert "på én gang, skattefri" in k.inner_text()                  # ingen gentagelse af beløbet
    assert "Børn: 50.000 kr." in k.inner_text()


def test_sundhed(med_forsikringer):
    assert "Du er dækket hos Testselskab" in kort(med_forsikringer, "sundhed").inner_text()


def test_ingen_forsikringer_intet_afsnit(resultat):
    assert resultat.is_hidden(AFSNIT)


def test_axe(med_forsikringer):
    s = med_forsikringer
    s.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = s.evaluate("async () => (await axe.run('#forsikringer', {runOnly: "
                      "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    assert s.fejl == []
