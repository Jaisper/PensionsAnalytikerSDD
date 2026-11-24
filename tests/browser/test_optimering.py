"""Feature 007 og 036 — "Find bedste plan" og engangsbeløb som buffer i brugerfladen (US1, US2, SC-002,
SC-004). Syntetisk rapport: o1 kapitalpension 65, o2 ratepension 67/10 år, o3 livsvarig 67,
o4 livsvarig 70 og folkepension 69."""
import json
from datetime import date

import pytest

from tests.browser.conftest import indlaes_axe

from pensionskerne import beregn
from pensionskerne.optimering import fast_niveau, maalvindue
from pensionsoverblik import app
from pensionsoverblik.oversaet import til_kerne

pytestmark = pytest.mark.browser


def daarlig_plan(side):
    """Skub ratepensionen 10 år og den sene livsvarige pension 5 år senere — det kan forbedres."""
    side.evaluate("window.__f = tilstand.v")
    for rid, tryk in (("o2", 2), ("o4", 1)):
        b = side.locator(f'.tl-raekke[data-id="{rid}"] .tl-bjaelke')
        b.focus()
        for _ in range(tryk):
            b.press("PageUp")
    side.wait_for_function("() => tilstand.v !== window.__f && !document.querySelector('.tl-fejl')")


def find_bedste_plan(side):
    """Tryk "Find bedste plan" og vent, til søgningen er færdig (036: samme søgning som ved start)."""
    nr = side.evaluate("autoNr")
    side.click("#optimer-knap")
    side.wait_for_function(f"() => autoNr > {nr} && document.body.dataset.plan === 'klar' && !tilstand.soeger",
                           timeout=60000)


def svar_json(side):
    return json.dumps(side.evaluate("tilstand.aktuelleSvar"))


def test_find_bedste_plan_bruges_med_det_samme(resultat):
    daarlig_plan(resultat)
    foer_svar = svar_json(resultat)
    forventet = app.optimer(foer_svar, date.today().isoformat())["data"]
    assert forventet["forbedret"], "den dårlige plan kan forbedres"
    find_bedste_plan(resultat)
    efter_svar = resultat.evaluate("tilstand.aktuelleSvar")
    for oid, felter in forventet["plan"]["ordninger"].items():
        o = next(x for x in efter_svar["ordninger"] if x["id"] == oid)
        assert all(o[k] == v for k, v in felter.items())
    # SC-004: det faste beløb hele perioden er søgningens beløb.
    p0, a0 = til_kerne(json.loads(foer_svar))
    v = maalvindue(beregn(p0, a0, 2026, date.today()), p0)  # 007b
    p, a = til_kerne(efter_svar)
    assert round(fast_niveau(beregn(p, a, 2026, date.today()), v), -2) == forventet["efter"]
    resultat.click("#data-panel-knap")
    o2 = forventet["plan"]["ordninger"]["o2"]["udbetaling_start_alder"]
    assert resultat.input_value("#data-panel-form #o2-udbetaling_start_alder") == str(o2)


def test_brug_min_egen_plan_fortryder(resultat):
    daarlig_plan(resultat)
    foer = svar_json(resultat)
    find_bedste_plan(resultat)
    resultat.get_by_role("button", name="Brug min egen plan").click()
    resultat.wait_for_function(
        "() => document.querySelector('#hovedtal-plan button')?.textContent === 'Brug den bedste plan'")
    assert svar_json(resultat) == foer


def test_fremdrift_vises(resultat):
    daarlig_plan(resultat)
    resultat.evaluate("""() => { window.__fremdrift = [];
        new MutationObserver(() => window.__fremdrift.push(document.querySelector('#plan-status-mere progress')?.value))
          .observe(document.querySelector('#plan-status-mere'), {subtree: true, childList: true, attributes: true}); }""")
    find_bedste_plan(resultat)
    assert any(v is not None for v in resultat.evaluate("window.__fremdrift"))


def test_pyodide_samme_forslag_som_cpython(resultat):
    daarlig_plan(resultat)
    g = svar_json(resultat)
    idag = "2026-10-25"
    assert resultat.evaluate("([g, d]) => kald('optimer', g, d)", [g, idag]) == app.optimer(g, idag)


def test_engangsbeloeb_som_buffer_eller_direkte(resultat):
    raekke = resultat.locator('.tl-raekke[data-id="o1"]')
    assert "til buffer" in raekke.inner_text()
    resultat.click("#data-panel-knap")
    boks = resultat.locator("#data-panel-form #o1-i_buffer")
    assert boks.is_checked()
    boks.uncheck()
    resultat.click("#opdater")
    resultat.wait_for_function("() => document.querySelector('#opdater-status').innerText.includes('opdateret')")
    assert "udbetales direkte" in raekke.inner_text()
    assert "tl-bjaelke--direkte" in raekke.locator(".tl-bjaelke").get_attribute("class")
    assert resultat.evaluate("tilstand.aktuelleSvar.ordninger.find(o => o.id === 'o1').i_buffer") is False
    d = resultat.evaluate("([g, d]) => kald('optimer', g, d)", [svar_json(resultat), "2026-10-25"])["data"]
    assert "o1" not in d["plan"]["ordninger"]


def test_axe_og_360_efter_soegning(resultat):
    daarlig_plan(resultat)
    find_bedste_plan(resultat)
    indlaes_axe(resultat)
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    assert resultat.fejl == []
