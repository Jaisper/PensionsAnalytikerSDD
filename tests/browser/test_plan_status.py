"""Feature 036 — den bedste plan: egne forventninger i guiden, én statuslinje for planen og én
fremstilling af "Find bedste plan". Syntetisk rapport (se test_optimering.py)."""
import json

import pytest

from tests.browser.test_optimering import daarlig_plan, find_bedste_plan

pytestmark = pytest.mark.browser


def status(side):
    return side.inner_text("#plan-status")


def knap(side):
    return side.locator("#optimer-knap")


# ── US1: forventningerne i guiden ────────────────────────────────────────────

def test_forventningerne_kan_springes_over(ny_side):
    s = ny_side
    s.goto(s.base_url)
    s.evaluate("motorKlar")
    hjaelp = s.text_content("#grundlag-hjaelp")
    assert "behøver ikke" in hjaelp and "Rådet for Afkastforventninger" in hjaelp
    valg = s.locator("#egne-valg")
    assert not valg.is_checked()
    assert s.evaluate("document.querySelector('#egne-forventninger').hidden")
    assert s.evaluate("tilstand.grundlag") == "branchestandard"
    s.evaluate("() => { const b = document.querySelector('#egne-valg'); b.checked = true;"
               " b.dispatchEvent(new Event('change')); }")
    assert not s.evaluate("document.querySelector('#egne-forventninger').hidden")
    assert s.evaluate("tilstand.grundlag") == "egne"


def test_egne_forventninger_bruges_fra_start(bedste_plan):
    # Fixturen `side` sætter "Jeg vil bruge mine egne forventninger" før guiden.
    s = bedste_plan
    assert "dine egne estimater" in s.inner_text("#hovedtal-grundlag")
    assert s.evaluate("tilstand.aktuelleSvar.antagelser.beregningsgrundlag") == "egne"
    p = s.evaluate("tilstand.planer")
    assert p["bedste"]["antagelser"]["beregningsgrundlag"] == "egne"


def test_afkrydsningen_gemmes(bedste_plan):
    assert bedste_plan.evaluate("guideFelter()['egne-valg']") is True


# ── US2: statuslinjen ────────────────────────────────────────────────────────

def test_status_bedste_plan(bedste_plan):
    s = bedste_plan
    assert "den bedste plan" in status(s)
    assert knap(s).inner_text() == "Find bedste plan"
    assert "knap--sekundaer" in knap(s).get_attribute("class")
    assert s.get_attribute("#plan-status", "role") == "status"
    assert "Dine forventninger og din fordeling ændres ikke" in s.inner_text("#optimer-hjaelp")


def test_status_egen_plan(resultat):
    assert "din egen plan" in status(resultat) and "mere" in status(resultat)


def test_status_aendret_uden_ny_soegning(bedste_plan):
    s = bedste_plan
    nr = s.evaluate("autoNr")
    daarlig_plan(s)
    assert s.evaluate("autoNr") == nr                       # regnes med det samme, men søges ikke
    assert "ændret" in status(s) and "ikke længere" in status(s)
    assert knap(s).inner_text() == "Find bedste plan igen"
    assert "knap--primaer" in knap(s).get_attribute("class")
    assert "ikke længere den bedste" in s.inner_text("#hovedtal-plan")
    assert s.fejl == []


def test_skift_af_grundlag_soeger_ikke(bedste_plan):
    s = bedste_plan
    nr = s.evaluate("autoNr")
    s.evaluate("window.__f = tilstand.v")
    s.get_by_role("button", name="Regn som pensionsselskaberne").click()
    s.wait_for_function("() => tilstand.v !== window.__f")
    assert s.evaluate("autoNr") == nr
    assert "forventninger" in status(s) and "Find bedste plan igen" in status(s)
    assert knap(s).inner_text() == "Find bedste plan igen"
    assert s.locator("#egne-valg").is_checked() is False       # afkrydsningen følger skiftet


def test_find_bedste_plan_igen_bruges_med_det_samme(bedste_plan):
    s = bedste_plan
    daarlig_plan(s)
    egen = s.evaluate("tilstand.aktuelleSvar")
    find_bedste_plan(s)
    p = s.evaluate("tilstand.planer")
    assert p is not None
    if p.get("ingenForbedring"):
        assert "allerede den bedste" in status(s)
    else:
        assert p["egen"] == egen                              # den viste plan blev "din egen plan"
        assert s.evaluate("tilstand.aktuelleSvar") == p["bedste"]
        assert "den bedste plan" in status(s)
        assert "Brug min egen plan" in s.inner_text("#hovedtal-plan")
    assert knap(s).inner_text() == "Find bedste plan"
    assert s.fejl == []


def test_afbryd_beholder_planen(bedste_plan):
    s = bedste_plan
    daarlig_plan(s)
    foer = json.dumps(s.evaluate("tilstand.aktuelleSvar"))
    s.click("#optimer-knap")
    s.wait_for_selector("#optimer-afbryd")
    assert "Finder bedste plan" in status(s)
    s.click("#optimer-afbryd")
    s.wait_for_function("() => document.body.dataset.plan === 'klar' && !tilstand.soeger")
    assert json.dumps(s.evaluate("tilstand.aktuelleSvar")) == foer
    assert s.inner_text("#hovedtal").endswith("kr.")
    assert "ændret" in status(s)
    assert s.locator("#optimer-afbryd").count() == 0


# ── US3: én fremstilling ─────────────────────────────────────────────────────

def test_ingen_forslagsboks_eller_stiplede_bjaelker(bedste_plan):
    s = bedste_plan
    daarlig_plan(s)
    find_bedste_plan(s)
    assert s.locator("#forslag").count() == 0
    assert s.locator(".tl-spoegelse").count() == 0
    assert s.get_by_role("button", name="Anvend").count() == 0


def test_axe_og_360_med_aendret_plan(bedste_plan):
    s = bedste_plan
    daarlig_plan(s)
    s.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = s.evaluate("async () => (await axe.run(document, {runOnly: "
                      "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    s.set_viewport_size({"width": 360, "height": 800})
    s.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    assert s.fejl == []
