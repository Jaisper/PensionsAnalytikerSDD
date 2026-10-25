"""Feature 007 — "Find bedste plan" og engangsbeløb som buffer i brugerfladen (US1, US2, SC-002,
SC-004). Syntetisk rapport: o1 kapitalpension 65, o2 ratepension 67/10 år, o3 livsvarig 67,
o4 livsvarig 70 og folkepension 69."""
import json
from datetime import date

import pytest

from pensionskerne import beregn
from pensionskerne.optimering import fast_niveau, vindue
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


def find_forslag(side):
    side.click("#optimer-knap")
    side.wait_for_selector("#forslag:not([hidden]) .forslag__resultat", timeout=60000)


def svar_json(side):
    return json.dumps(side.evaluate("tilstand.aktuelleSvar"))


def test_find_bedste_plan_og_anvend(resultat):
    daarlig_plan(resultat)
    foer_svar = svar_json(resultat)
    find_forslag(resultat)
    tekst = resultat.inner_text("#forslag")
    assert "kr. mere om måneden" in tekst and "i stedet for" in tekst
    assert resultat.locator("#forslag li").count() >= 1
    assert resultat.locator(".tl-spoegelse").count() >= 1
    forventet = app.optimer(foer_svar, date.today().isoformat())["data"]
    resultat.get_by_role("button", name="Anvend").click()
    resultat.wait_for_selector("#forslag", state="hidden")
    efter_svar = json.loads(svar_json(resultat))
    for oid, felter in forventet["plan"]["ordninger"].items():
        o = next(x for x in efter_svar["ordninger"] if x["id"] == oid)
        assert all(o[k] == v for k, v in felter.items())
    # SC-004: det faste beløb hele perioden er forslagets beløb.
    p0, a0 = til_kerne(json.loads(foer_svar))
    v = vindue(beregn(p0, a0, 2026, date.today()))
    p, a = til_kerne(efter_svar)
    assert round(fast_niveau(beregn(p, a, 2026, date.today()), v), -2) == forventet["efter"]
    resultat.click("#data-panel-knap")
    o2 = forventet["plan"]["ordninger"]["o2"]["udbetaling_start_alder"]
    assert resultat.input_value("#data-panel-form #o2-udbetaling_start_alder") == str(o2)


def test_behold_min_plan_aendrer_intet(resultat):
    daarlig_plan(resultat)
    foer = svar_json(resultat)
    find_forslag(resultat)
    resultat.get_by_role("button", name="Behold min plan").click()
    assert resultat.locator("#forslag").is_hidden()
    assert resultat.locator(".tl-spoegelse").count() == 0
    assert svar_json(resultat) == foer


def test_forslag_forsvinder_ved_aendring(resultat):
    daarlig_plan(resultat)
    find_forslag(resultat)
    b = resultat.locator('.tl-raekke[data-id="o3"] .tl-bjaelke')
    b.focus()
    b.press("ArrowRight")
    assert resultat.locator("#forslag").is_hidden()
    assert resultat.locator(".tl-spoegelse").count() == 0


def test_fremdrift_vises(resultat):
    daarlig_plan(resultat)
    resultat.evaluate("""() => { window.__fremdrift = [];
        new MutationObserver(() => window.__fremdrift.push(document.querySelector('#forslag progress')?.value))
          .observe(document.querySelector('#forslag'), {subtree: true, childList: true, attributes: true}); }""")
    find_forslag(resultat)
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


def test_axe_og_360_med_forslag(resultat):
    daarlig_plan(resultat)
    find_forslag(resultat)
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    assert resultat.fejl == []


def test_afbryd_soegningen_beholder_planen(resultat):
    """Over 10 sekunder kræver en vej ud (brugerkontrol): "Afbryd" stopper søgningen, og planen og
    tallene er uændrede. Bagefter kan der regnes igen."""
    daarlig_plan(resultat)
    foer = svar_json(resultat)
    hovedtal = resultat.inner_text("#hovedtal")
    resultat.click("#optimer-knap")
    resultat.click("#optimer-afbryd")
    assert resultat.locator("#forslag").is_hidden()
    assert svar_json(resultat) == foer and resultat.inner_text("#hovedtal") == hovedtal
    resultat.evaluate("motorKlar")
    resultat.wait_for_function("() => motorKlar && document.querySelector('#motor').hidden")
    b = resultat.locator('.tl-raekke[data-id="o3"] .tl-bjaelke')
    resultat.evaluate("window.__f = tilstand.v")
    b.focus()
    b.press("ArrowRight")
    resultat.wait_for_function("() => tilstand.v !== window.__f")
    assert resultat.fejl == []
