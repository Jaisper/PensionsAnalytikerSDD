"""Feature 037 — partnerne hver for sig: fordeling (equalizer), afkast og grundlag. Inflationen er fælles.
Syntetisk rapport for begge (test_partner.py)."""
import pytest

from tests.browser.conftest import vent_paa_planen
from tests.browser.test_partner import faner, til_resultat_som_par
from tests.browser.test_tidslinje import marker_resultat, vent_paa_ny_beregning

pytestmark = pytest.mark.browser

SKYDERE = "#forbrug-baand input[type=range]"


@pytest.fixture
def par(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    vent_paa_planen(side, timeout=120000)
    return side


def dine(side):
    return side.evaluate("tilstand.aktuelleSvar.antagelser")


def partnerens(side):
    return side.evaluate("tilstand.aktuelleSvar.person.partner.antagelser")


def vis_partner(side):
    marker_resultat(side)
    faner(side).nth(1).click()
    side.wait_for_function("() => tilstand.hvem === 'partner'")


def saet_baand(side, i, vaerdi):
    s = side.locator(SKYDERE).nth(i)
    marker_resultat(side)
    s.fill(vaerdi)
    s.dispatch_event("input")
    vent_paa_ny_beregning(side)


def saet_afkast(side, vaerdi):
    marker_resultat(side)
    side.locator("#r-afkast").fill(vaerdi)
    side.locator("#r-afkast").dispatch_event("input")
    vent_paa_ny_beregning(side)


def test_partneren_starter_med_en_kopi(par):
    p, d = partnerens(par), dine(par)
    assert p["afkast_efter_pal"] == d["afkast_efter_pal"]
    assert p["beregningsgrundlag"] == d["beregningsgrundlag"]
    assert p["forbrugsprofil"] == []
    assert "inflation" not in p                                  # inflationen er husstandens


def test_fordelingen_hver_for_sig(par):
    assert par.locator("#forbrug").is_visible()
    saet_baand(par, 1, "70")
    assert dine(par)["forbrugsprofil"][1] == 0.7
    assert partnerens(par)["forbrugsprofil"] == []
    vis_partner(par)
    assert all(par.locator(SKYDERE).nth(i).input_value() == "100" for i in range(par.locator(SKYDERE).count()))
    saet_baand(par, 0, "120")
    assert partnerens(par)["forbrugsprofil"][0] == 1.2
    assert dine(par)["forbrugsprofil"][1] == 0.7 and dine(par)["forbrugsprofil"][0] == 1.0
    # Partnerens bånd følger partnerens egne aldre, ikke dine.
    assert "partner" not in (par.locator(SKYDERE).first.get_attribute("aria-label") or "")
    assert par.fejl == []


def test_afkastet_hver_for_sig_inflationen_faelles(par):
    dit = dine(par)["afkast_efter_pal"]
    vis_partner(par)
    saet_afkast(par, "6")
    assert partnerens(par)["afkast_efter_pal"] == 0.06
    assert dine(par)["afkast_efter_pal"] == dit
    marker_resultat(par)
    par.locator("#r-inflation").fill("3")
    par.locator("#r-inflation").dispatch_event("input")
    vent_paa_ny_beregning(par)
    assert dine(par)["inflation"] == 0.03 and "inflation" not in partnerens(par)
    marker_resultat(par)
    faner(par).nth(0).click()
    par.wait_for_function("() => tilstand.hvem === 'dig'")
    assert par.input_value("#r-afkast") == str(round(dit * 100)) or float(par.input_value("#r-afkast")) == dit * 100


def test_grundlaget_hver_for_sig(par):
    vis_partner(par)
    marker_resultat(par)
    par.get_by_role("button", name="Regn som pensionsselskaberne").click()
    vent_paa_ny_beregning(par)
    assert partnerens(par)["beregningsgrundlag"] == "branchestandard"
    assert dine(par)["beregningsgrundlag"] == "egne"
    assert "forskellige forventninger" in par.inner_text("#hovedtal-grundlag")
    assert "regnet som pensionsselskaberne" in par.inner_text("#hovedtal-grundlag")
    faner(par).nth(0).click()
    par.wait_for_function("() => tilstand.hvem === 'dig'")
    par.wait_for_function("() => /dine egne estimater/.test(document.querySelector('#hovedtal-grundlag').textContent)")
    assert par.locator("#r-egne").is_visible()


def test_valgene_overlever_opdater_og_gem(par):
    vis_partner(par)
    saet_afkast(par, "6")
    saet_baand(par, 0, "120")
    # Opdater fra datapanelet bygger svaret fra guiden: partnerens valg og fordelingen bevares.
    par.click("#data-panel-knap")
    par.click("#opdater")
    par.wait_for_function("() => document.querySelector('#opdater-status').innerText.includes('opdateret')")
    assert partnerens(par)["afkast_efter_pal"] == 0.06 and partnerens(par)["forbrugsprofil"][0] == 1.2
    g = par.evaluate("gemData()")
    assert g["antagelser"]["partner"]["afkast_efter_pal"] == 0.06
    assert g["antagelser"]["partner"]["forbrugsprofil"][0] == 1.2
    assert par.fejl == []


def test_samlet_viser_kun_det_der_giver_mening_summeret(par):
    # Afkast, stopalder, næste krone og år-for-år er pr. person; de hører ikke til fanen Samlet.
    skjult = "#forudsaetninger, #saadan, #menu a[href='#saadan']"
    faner(par).nth(2).click()
    par.wait_for_function("() => tilstand.hvem === 'samlet'")
    for sel in skjult.split(", "):
        assert par.locator(sel).is_hidden(), sel
    assert par.locator("#samlet-panel").is_visible()
    faner(par).nth(0).click()
    par.wait_for_function("() => tilstand.hvem === 'dig'")
    for sel in skjult.split(", "):
        assert par.locator(sel).is_visible(), sel


def test_unikke_id_er(par):
    assert par.evaluate("""() => { const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
                                   return ids.filter((x, i) => ids.indexOf(x) !== i); }""") == []
