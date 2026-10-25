"""Feature 012 T006 — partneren i brugerfladen (US1–US4, FR-006–FR-008).

Begge personer indlæses fra den syntetiske rapport (samme ordninger, hver sine id'er)."""
import json

import pytest

from pensionsoverblik import app
from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

pytestmark = pytest.mark.browser


def til_resultat_som_par(side, tmp_path, civilstand="gift"):
    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    side.set_input_files("#pdf-fil", str(pdf))
    side.click("#pdf-knap")
    side.wait_for_selector("#pdf-status p")
    side.fill("#kommune", "Aarhus")
    side.check(f"input[name=civilstand][value={civilstand}]")
    side.fill("#partner-foedselsdato", "1965-02-01")
    side.check("input[name=partnerdata][value=fuld]")
    assert side.locator('.fremdrift li[data-trin="3"]').is_visible()
    side.click("#naeste")                       # → trin 2: dine ordninger
    for felt in side.query_selector_all("#ordninger input[id$='-udbetaling_start_alder']"):
        if not felt.input_value():
            felt.fill("70")
    side.click("#naeste")                       # → trin 3: din partners ordninger
    assert side.locator('.trin[data-trin="3"]').is_visible()
    side.set_input_files("#p-pdf-fil", str(pdf))
    side.click("#p-pdf-knap")
    side.wait_for_selector("#p-pdf-status p")
    for felt in side.query_selector_all("#p-ordninger input[id$='-udbetaling_start_alder']"):
        if not felt.input_value():
            felt.fill("70")
    side.click("#naeste")                       # → trin 4: forventninger
    side.click("#naeste")                       # → resultat
    side.wait_for_selector("#resultat:not([hidden])")


def faner(side):
    return side.locator('[role="tab"]')


def test_guiden_har_et_partnertrin_kun_ved_fuld_profil(side):
    side.check("input[name=civilstand][value=gift]")
    assert side.locator('.fremdrift li[data-trin="3"]').is_hidden()
    side.check("input[name=partnerdata][value=fuld]")
    assert side.locator('.fremdrift li[data-trin="3"]').is_visible()
    side.check("input[name=partnerdata][value=overslag]")
    assert side.locator("#partner-indkomst").is_visible()


def test_partnerens_rapport_fylder_kun_partneren(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    svar = side.evaluate("tilstand.aktuelleSvar")
    dig = [o["id"] for o in svar["ordninger"]]
    partner = [o["id"] for o in svar["person"]["partner"]["profil"]["ordninger"]]
    assert dig and partner and all(i.startswith("o") for i in dig) and all(i.startswith("p") for i in partner)
    assert svar["person"]["civilstand"] == "gift"


def test_faner_og_samlet_er_summen(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    assert [f.inner_text() for f in faner(side).all()] == ["Dig", "Partner", "Samlet"]
    dig = side.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    faner(side).nth(0).focus()
    side.keyboard.press("ArrowRight")           # tastatur: Dig → Partner
    assert faner(side).nth(1).get_attribute("aria-selected") == "true"
    partner = side.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    assert "partner" in side.inner_text("#resultat-titel").lower()
    faner(side).nth(2).click()
    samlet = side.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    assert samlet == dig + partner
    assert side.locator("#samlet-panel").is_visible() and side.locator("#graf-panel").is_hidden()


def test_traek_under_partner_aendrer_partneren(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    faner(side).nth(1).click()
    raekker = side.locator(".tl-raekke").evaluate_all("rr => rr.map(r => r.dataset.id)")
    assert raekker[0].startswith("p")
    foer = side.evaluate("JSON.stringify(tilstand.aktuelleSvar.ordninger)")
    b = side.locator(f'.tl-raekke[data-id="{raekker[1]}"] .tl-bjaelke')
    side.evaluate("window.__f = tilstand.v")
    b.focus()
    b.press("ArrowRight")
    side.wait_for_function("() => tilstand.v !== window.__f")
    assert side.evaluate("JSON.stringify(tilstand.aktuelleSvar.ordninger)") == foer  # dine ordninger uændrede
    pp = side.evaluate("tilstand.aktuelleSvar.person.partner.profil.ordninger")
    assert any(o["id"] == raekker[1] for o in pp)
    assert faner(side).nth(1).get_attribute("aria-selected") == "true"  # bliver på fanen


def test_find_bedste_plan_for_partneren(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    faner(side).nth(1).click()
    side.click("#optimer-knap")
    side.wait_for_selector("#forslag .forslag__resultat", timeout=120000)
    if side.locator("#forslag h3").count():
        assert all(i.startswith("p") for i in side.evaluate("Object.keys(tilstand.forslag.d.plan.ordninger)"))


def test_samme_som_cpython(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    g = json.dumps(side.evaluate("tilstand.aktuelleSvar"))
    b = side.evaluate("([g, d]) => kald('beregn', g, d)", [g, "2026-10-25"])
    c = app.beregn(g, "2026-10-25")
    assert b["data"]["husstand"]["samlet"]["maaned"] == c["data"]["husstand"]["samlet"]["maaned"]
    assert b["data"]["husstand"]["partner"]["hovedtal"] == c["data"]["husstand"]["partner"]["hovedtal"]


def test_axe_og_360(side, tmp_path):
    til_resultat_som_par(side, tmp_path)
    faner(side).nth(2).click()
    side.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = side.evaluate("async () => (await axe.run(document, {runOnly: "
                         "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    side.set_viewport_size({"width": 360, "height": 800})
    side.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    assert side.fejl == []
