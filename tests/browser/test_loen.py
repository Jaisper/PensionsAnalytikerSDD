"""Feature 017 T014 — løn, stopalder og "Hvornår kan jeg stoppe?" i brugerfladen."""
import json

import pytest

from pensionsoverblik import app
from tests.browser.conftest import vent_paa_planen

pytestmark = pytest.mark.browser

IDAG = "2026-10-25"


def til_resultat(side, loen="40000", stop="64", bank=None):
    side.fill("#foedselsdato", "1966-03-01")
    side.fill("#kommune", "Aarhus")
    if loen:
        side.fill("#loen-maaned", loen)  # pr. måned (017c)
    if stop:
        side.fill("#stop-alder", stop)
    side.click("#naeste")                       # trin 2: ordninger
    side.click("#naeste")                       # trin 4: opsparing
    if bank:
        side.fill("#bank", bank)
    side.click("#naeste")                       # trin 5: forventninger
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")


def test_loen_giver_loenkort_og_fast_beloeb_fra_stopalderen(side):
    til_resultat(side, bank="300000")
    v = side.evaluate("tilstand.v")
    assert v["hovedtal"]["fra_alder"] == 64
    assert any(k["noegle"] == "loen" for k in v["kort"])
    assert "Løn" in side.inner_text("#kort")
    assert side.evaluate("tilstand.aktuelleSvar.person.loen") == {
        "aarlig": 480000, "stop_alder": 64, "deltid_aarlig": 0, "deltid_til_alder": None,
        "pension_eget": 0, "pension_firma": 0}
    assert side.fejl == []


def test_hvornaar_kan_jeg_stoppe_og_brug_alderen(side):
    til_resultat(side, bank="300000")
    side.fill("#oenske", "1000")
    side.click("#stop-knap")
    side.wait_for_selector("#stop-svar .forslag__resultat")
    assert "Du kan stoppe som" in side.inner_text("#stop-svar")
    assert "afprøvet alle" in side.inner_text("#stop-svar")
    side.evaluate("window.__f = tilstand.v")
    side.click("#stop-svar button")
    side.wait_for_function("() => tilstand.v !== window.__f")
    alder = side.evaluate("tilstand.aktuelleSvar.person.loen.stop_alder")
    assert side.input_value("#stop-alder") == str(alder)
    assert side.evaluate("tilstand.v.hovedtal.fra_alder") == alder


def test_uden_loen_beder_vi_om_loennen(side):
    til_resultat(side, loen=None, stop=None)
    side.fill("#oenske", "15000")
    side.click("#stop-knap")
    assert "Skriv din løn" in side.inner_text("#stop-svar")


def test_samme_som_cpython(side):
    til_resultat(side, bank="300000")
    g = json.dumps(side.evaluate("tilstand.aktuelleSvar"))
    b = side.evaluate("([g, d]) => kald('stopalder', g, d, 15000)", [g, IDAG])
    assert b == app.stopalder(g, IDAG, 15000)


def test_axe_og_360(side):
    til_resultat(side, bank="300000")
    side.fill("#oenske", "1000")
    side.click("#stop-knap")
    side.wait_for_selector("#stop-svar .forslag__resultat")
    side.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = side.evaluate("async () => (await axe.run(document, {runOnly: "
                         "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    side.set_viewport_size({"width": 360, "height": 800})
    side.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)


def test_nettoloennen_vises_ved_hovedtallet(side):
    """017b: nettolønnen pr. måned står ved hovedtallet til sammenligning."""
    til_resultat(side, bank="300000")
    vent_paa_planen(side)  # 028: teksten er skjult, mens talrullen kører
    nl = side.evaluate("tilstand.v.loen")
    tekst = side.inner_text("#hovedtal-loen")
    assert f"{nl['maaned']:,.0f}".replace(",", ".") in tekst and "til 64 år" in tekst
    assert f"{nl['andel_pct']} %" in tekst
    assert side.fejl == []


def test_ingen_nettoloen_uden_loen(side):
    til_resultat(side, loen=None, stop=None)
    assert side.is_hidden("#hovedtal-loen")
