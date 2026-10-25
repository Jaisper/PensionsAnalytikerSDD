"""Feature 009 T010 — kapitalpensionens muligheder i brugerfladen (US1–US5, FR-009, FR-012).
Syntetisk rapport: o1 er en kapitalpension ved 65 år, tidligst 60 år (oplyst) → seneste 80 år."""
import json

import pytest

from pensionsoverblik import app

pytestmark = pytest.mark.browser


def aaben_panel(side):
    if side.get_attribute("#data-panel-knap", "aria-expanded") != "true":
        side.click("#data-panel-knap")


def opdater(side):
    side.evaluate("window.__f = tilstand.v")
    side.click("#opdater")
    side.wait_for_function("() => tilstand.v !== window.__f")


def svar(side, oid):
    return side.evaluate(f"tilstand.aktuelleSvar.ordninger.find(o => o.id === '{oid}')")


def test_kortet_har_udbetalingsform_og_afgift(resultat):
    aaben_panel(resultat)
    form = resultat.locator("#data-panel-form #o1-udbetalingsform")
    assert [o.get_attribute("value") for o in form.locator("option").all()] == ["engangs", "portioner", "ratepension", "livsvarig"]
    assert form.input_value() == "engangs"
    assert resultat.locator("#data-panel-form #o1-afgift_betalt").is_visible()
    assert resultat.locator("#data-panel-form #o1-udbetaling_aar").is_hidden()


def test_portioner_i_tidslinje_og_graf(resultat):
    aaben_panel(resultat)
    resultat.select_option("#data-panel-form #o1-udbetalingsform", "portioner")
    aar = resultat.locator("#data-panel-form #o1-udbetaling_aar")
    assert aar.is_visible()
    aar.fill("6")
    opdater(resultat)
    o1 = svar(resultat, "o1")
    assert (o1["udbetalingsform"], o1["udbetaling_aar"]) == ("portioner", 6)
    raekke = resultat.locator('.tl-raekke[data-id="o1"]')
    assert "65–70 år" in raekke.inner_text() and "6 portioner" in raekke.inner_text()
    assert raekke.locator(".tl-greb").count() == 1
    assert "tl-bjaelke--engang" not in raekke.locator(".tl-bjaelke").get_attribute("class")
    liste = resultat.inner_text("#graf-markeringer")
    assert "6 portioner" in liste and "→ buffer" in liste
    # Grebet ændrer antal portioner inden for fristen (sidste senest 80 år).
    g = raekke.locator(".tl-greb")
    assert g.get_attribute("aria-valuemin") == "2" and g.get_attribute("aria-valuemax") == "16"
    g.focus()
    g.press("ArrowRight")
    assert svar(resultat, "o1")["udbetaling_aar"] == 7


def test_omlaegning_til_ratepension(resultat):
    aaben_panel(resultat)
    resultat.select_option("#data-panel-form #o1-udbetalingsform", "ratepension")
    resultat.fill("#data-panel-form #o1-udbetaling_aar", "10")
    opdater(resultat)
    raekke = resultat.locator('.tl-raekke[data-id="o1"]')
    assert "omlagt til ratepension" in raekke.inner_text() and "65–74 år" in raekke.inner_text()
    assert "Omlægning af kapitalpension" in resultat.inner_text("#resultat")


def test_afgift_betalt_udelukker_omlaegning(resultat):
    aaben_panel(resultat)
    resultat.locator("#data-panel-form #o1-afgift_betalt").check()
    form = resultat.locator("#data-panel-form #o1-udbetalingsform")
    deaktiveret = [o.get_attribute("value") for o in form.locator("option[disabled]").all()]
    assert deaktiveret == ["ratepension", "livsvarig"]
    opdater(resultat)
    assert svar(resultat, "o1")["afgift_betalt"] is True


def test_forslagstekst_for_udbetalingsform(resultat):
    tekst = resultat.evaluate("aendringTekst({felt: 'form', fra: {form: 'engangs', aar: null}, til: {form: 'portioner', aar: 8}}, true)")
    assert tekst == "ét beløb → i portioner over 8 år"


def test_ingen_gammel_kapitalskat_antagelse(resultat):
    assert "Skat af afkast på opsparing uden for pension" not in resultat.inner_text("#resultat")


def test_portioner_som_cpython(resultat):
    aaben_panel(resultat)
    resultat.select_option("#data-panel-form #o1-udbetalingsform", "portioner")
    resultat.fill("#data-panel-form #o1-udbetaling_aar", "6")
    opdater(resultat)
    g = json.dumps(resultat.evaluate("tilstand.aktuelleSvar"))
    b = resultat.evaluate("([g, d]) => kald('beregn', g, d)", [g, "2026-10-25"])
    c = app.beregn(g, "2026-10-25")
    assert b["data"]["hovedtal"] == c["data"]["hovedtal"] and b["data"]["graf"]["engangs"] == c["data"]["graf"]["engangs"]


def test_axe_og_360(resultat):
    aaben_panel(resultat)
    resultat.select_option("#data-panel-form #o1-udbetalingsform", "portioner")
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    assert resultat.fejl == []
