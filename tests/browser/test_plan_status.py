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


# ── Tidslinjen: bjælkerne må aldrig gå ud over sporet (fundet i produktion 2026-11-23) ──

BJAELKER_UDENFOR = """() => [...document.querySelectorAll('.tl-raekke')].flatMap((r) => {
  const spor = r.querySelector('.tl-spor').getBoundingClientRect();
  return [...r.querySelectorAll('.tl-bjaelke, .tl-greb')].map((b) => b.getBoundingClientRect())
    .filter((b) => b.width && (b.right > spor.right + 1 || b.left < spor.left - 1))
    .map((b) => `${r.dataset.id}: ${Math.round(b.left)}–${Math.round(b.right)} uden for ${Math.round(spor.left)}–${Math.round(spor.right)}`);
})"""


@pytest.mark.parametrize("bredde", [1280, 1640])
def test_bjaelkerne_holder_sig_i_sporet(bedste_plan, bredde):
    s = bedste_plan
    s.set_viewport_size({"width": bredde, "height": 900})
    s.wait_for_timeout(300)
    assert s.evaluate(BJAELKER_UDENFOR) == []
    daarlig_plan(s)
    find_bedste_plan(s)
    s.wait_for_timeout(300)
    assert s.evaluate(BJAELKER_UDENFOR) == []


@pytest.mark.parametrize("bredde", [1280, 1640])
def test_bjaelkerne_holder_sig_i_sporet_for_et_par(side, tmp_path, bredde):
    from tests.browser.conftest import vent_paa_planen
    from tests.browser.test_partner import til_resultat_som_par
    side.set_viewport_size({"width": bredde, "height": 900})
    til_resultat_som_par(side, tmp_path)
    vent_paa_planen(side, timeout=120000)
    side.wait_for_timeout(300)
    assert side.evaluate(BJAELKER_UDENFOR) == []
    side.locator("#person-faner [data-hvem=partner]").click()
    side.wait_for_timeout(500)
    assert side.evaluate(BJAELKER_UDENFOR) == []


def test_bjaelkerne_foelger_med_naar_vinduet_aendrer_bredde(bedste_plan):
    s = bedste_plan
    s.set_viewport_size({"width": 1900, "height": 900})
    s.wait_for_timeout(500)
    s.set_viewport_size({"width": 1100, "height": 900})
    s.wait_for_timeout(500)
    assert s.evaluate(BJAELKER_UDENFOR) == []


def test_bjaelkerne_holder_sig_i_sporet_selv_med_forkert_grafskala(bedste_plan):
    # Uanset årsagen (grafen bredere end sporet, forældet skala): bjælkerne bliver i sporet.
    s = bedste_plan
    s.evaluate("""() => { const x = tilstand.graf.scales.x, f = x.getPixelForValue.bind(x);
                          x.getPixelForValue = (i) => f(i) * 1.4; placerBjaelker(); }""")
    s.wait_for_timeout(400)  # bjælkerne animeres (transition .15s)
    assert s.evaluate(BJAELKER_UDENFOR) == []
