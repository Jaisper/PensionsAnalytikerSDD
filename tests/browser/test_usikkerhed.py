"""Feature 018 T002 — usikkerhed om afkast og inflation i brugerfladen (US1, US2, SC-003, SC-004)."""
import json
import time

import pytest

from pensionsoverblik import app
from tests.browser.test_partner import faner, til_resultat_som_par

pytestmark = pytest.mark.browser

IDAG = "2026-10-25"


def vent_paa_spaend(side, timeout=30000):
    side.wait_for_function("() => tilstand.usikkerhed !== null && tilstand.usikkerhed !== undefined", timeout=timeout)


def test_spaend_og_tabel(resultat):
    t = time.perf_counter()
    vent_paa_spaend(resultat)
    assert time.perf_counter() - t < 3  # SC-004 (efter at resultatet er vist)
    tekst = resultat.inner_text("#hovedtal-spaend")
    assert "mellem" in tekst
    resultat.click("#hovedtal-spaend a")
    assert resultat.locator("#usikkerhed").get_attribute("open") is not None
    raekker = resultat.locator("#usikkerhed-tabel tbody tr")
    assert raekker.count() == 7
    assert "Dit valg" in raekker.nth(0).inner_text()
    assert resultat.fejl == []


def test_samme_som_cpython(resultat):
    vent_paa_spaend(resultat)
    svar = json.dumps(resultat.evaluate("tilstand.aktuelleSvar"))
    for s in resultat.evaluate("tilstand.usikkerhed"):
        assert s["beloeb"] == app.scenarie(svar, IDAG, s["afkast"], s["inflation"])["data"]


def test_ny_beregning_afbryder_de_gamle_scenarier(resultat):
    nr = resultat.evaluate("usikkerhedNr")
    resultat.evaluate("regnUsikkerhed()")
    resultat.evaluate("regnUsikkerhed()")
    vent_paa_spaend(resultat)
    assert resultat.evaluate("usikkerhedNr") == nr + 2
    assert len(resultat.evaluate("tilstand.usikkerhed")) == 6


def test_spaendet_foelger_fanen(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    vent_paa_spaend(side, timeout=60000)
    dig = side.inner_text("#hovedtal-spaend")
    faner(side).nth(2).click()
    samlet = side.inner_text("#hovedtal-spaend")
    assert dig != samlet and "mellem" in samlet
    rk = side.evaluate("tilstand.usikkerhed")[0]["beloeb"]
    assert rk["samlet"] == rk["dig"] + rk["partner"]


def test_axe_og_360(resultat):
    vent_paa_spaend(resultat)
    resultat.click("#hovedtal-spaend a")
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
