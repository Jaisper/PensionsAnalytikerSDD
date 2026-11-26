"""Feature 040 T005 — planens slutning og penge tilbage i guiden og under "Prøv andre forudsætninger", prisen
ved hovedtallet og partnerens egne værdier."""
import json

import pytest

from pensionsoverblik import app
from tests.browser.conftest import indlaes_axe, vent_paa_planen
from tests.browser.test_opsparing import IDAG, hovedtal, til_opsparingstrinnet, til_resultat
from tests.browser.test_partner import faner, til_resultat_som_par
from tests.browser.test_tidslinje import marker_resultat, vent_paa_ny_beregning

pytestmark = pytest.mark.browser


def til_forventninger(side):
    til_opsparingstrinnet(side)
    side.fill("#bank", "500000")
    side.click("#naeste")
    assert side.locator('.trin[data-trin="5"]').is_visible()


def saet_slider(side, sel, vaerdi):
    side.locator(sel).fill(str(vaerdi))
    side.locator(sel).dispatch_event("input")


def test_felterne_i_guiden_sendes_med(side):
    til_forventninger(side)
    assert side.locator("#plan-slut").input_value() == "90"
    assert "90 år" in side.inner_text("#plan-slut-v")
    saet_slider(side, "#plan-slut", 95)
    assert side.inner_text("#plan-slut-v") == "95 år"
    side.fill("#rest-slut", "250.000")
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")
    a = side.evaluate("tilstand.aktuelleSvar.antagelser")
    assert a["plan_slut_alder"] == 95 and a["rest_ved_plan_slut"] == 250000
    assert side.evaluate("tilstand.v.aar.at(-1).alder") == 95
    # Prisen ved hovedtallet.
    tekst = side.inner_text("#hovedtal-rest")
    assert "250.000 kr. tilbage som 95-årig" in tekst and "koster ca." in tekst
    assert side.fejl == []


def test_standard_sender_ingenting(side):
    til_forventninger(side)
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")
    a = side.evaluate("tilstand.aktuelleSvar.antagelser")
    assert a["plan_slut_alder"] is None and a["rest_ved_plan_slut"] == 0
    assert not side.locator("#hovedtal-rest").is_visible()


def test_proev_andre_forudsaetninger(side):
    til_forventninger(side)
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")
    vent_paa_planen(side, timeout=120000)
    foer = hovedtal(side)
    assert side.locator("#r-plan-slut").is_visible() and side.locator("#r-rest").is_visible()
    marker_resultat(side)
    saet_slider(side, "#r-plan-slut", 100)
    vent_paa_ny_beregning(side)
    assert side.evaluate("tilstand.aktuelleSvar.antagelser.plan_slut_alder") == 100
    assert side.evaluate("tilstand.v.aar.at(-1).alder") == 100
    assert hovedtal(side) <= foer
    assert side.locator("#plan-slut").input_value() == "100"        # guiden følger med
    marker_resultat(side)
    side.fill("#r-rest", "300000")
    side.locator("#r-rest").dispatch_event("change")
    vent_paa_ny_beregning(side)
    assert side.evaluate("tilstand.aktuelleSvar.antagelser.rest_ved_plan_slut") == 300000
    assert "300.000 kr. tilbage som 100-årig" in side.inner_text("#hovedtal-rest")
    # Tabellen er relativ til valget: 95 og 105 år.
    side.wait_for_function("() => tilstand.usikkerhed && tilstand.usikkerhed.some((r) => r.plan_slut_alder === 105)",
                           timeout=60000)
    tabel = side.inner_text("#usikkerhed-tabel")
    assert "105 år" in tabel and "95 år" in tabel
    side.click("#nulstil")
    vent_paa_ny_beregning(side)
    assert side.evaluate("tilstand.aktuelleSvar.antagelser.rest_ved_plan_slut") == 0
    assert side.input_value("#r-rest") == ""
    assert side.fejl == []


def test_samme_som_cpython(side):
    til_forventninger(side)
    saet_slider(side, "#plan-slut", 93)
    side.fill("#rest-slut", "200000")
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")
    svar = json.dumps(side.evaluate("tilstand.aktuelleSvar"))
    forventet = app.beregn(svar, IDAG)["data"]
    assert side.evaluate("tilstand.v.hovedtal") == forventet["hovedtal"]


def test_partneren_har_sine_egne(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    vent_paa_planen(side, timeout=120000)
    marker_resultat(side)
    faner(side).nth(1).click()
    side.wait_for_function("() => tilstand.hvem === 'partner'")
    marker_resultat(side)
    saet_slider(side, "#r-plan-slut", 95)
    vent_paa_ny_beregning(side)
    s = side.evaluate("tilstand.aktuelleSvar")
    assert s["person"]["partner"]["antagelser"]["plan_slut_alder"] == 95
    assert s["antagelser"].get("plan_slut_alder") is None
    assert side.locator("#p-plan-slut").input_value() == "95"
    assert side.fejl == []


def test_axe_paa_forventningstrinnet(side):
    til_forventninger(side)
    indlaes_axe(side)
    fejl = side.evaluate("async () => (await axe.run('.trin[data-trin=\"5\"]')).violations.map((v) => v.id)")
    assert fejl == []
