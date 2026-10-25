"""Feature 013 T014 — opsparing uden for pension i guiden og resultatet (US1, US4, FR-009, SC-005)."""
import json

import pytest

from pensionsoverblik import app

pytestmark = pytest.mark.browser

IDAG = "2026-10-25"


def til_opsparingstrinnet(side, civilstand="enlig"):
    side.fill("#foedselsdato", "1960-05-01")
    side.fill("#kommune", "Aarhus")
    side.check(f"input[name=civilstand][value={civilstand}]")
    if civilstand != "enlig":
        side.fill("#partner-foedselsdato", "1962-02-01")
    side.click("#naeste")                       # trin 2: ordninger (springes over)
    side.click("#naeste")                       # trin 4: opsparing
    assert side.locator('.trin[data-trin="4"]').is_visible()


def til_resultat(side):
    side.click("#naeste")                       # trin 5: forventninger
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")


def hovedtal(side) -> float:
    return side.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")


def test_opsparing_haever_hovedtallet(side):
    til_opsparingstrinnet(side)
    side.fill("#bank", "400000")
    til_resultat(side)
    svar = side.evaluate("tilstand.aktuelleSvar")
    svar["person"]["opsparing"] = []
    uden = app.beregn(json.dumps(svar), IDAG)["data"]
    assert hovedtal(side) > uden["hovedtal"]["maaned"]
    assert uden["formue"] is None               # ingen ordninger og ingen opsparing: intet at vise


def test_guiden_sender_opsparingen_og_resultatet_viser_formuen(side):
    til_opsparingstrinnet(side)
    side.fill("#bank", "250000")
    side.uncheck("#bank-i-plan")
    til_resultat(side)
    assert side.evaluate("tilstand.aktuelleSvar.person.opsparing") == [
        {"id": "bank", "type": "bank", "saldo": 250000, "i_plan": False}]
    assert side.locator("#formue-fold").is_visible()
    assert "tilbage som" in side.inner_text("#formue-titel")
    side.click("#formue-fold summary")
    assert side.locator("#formue-tabel tbody tr").count() > 20
    assert side.fejl == []


def test_partnerens_opsparing_spoerges_efter_partnerdata(side):
    til_opsparingstrinnet(side, "gift")         # overslag: kun et tal til ældrechecken
    assert side.locator("#partner-formue").is_visible() and side.locator("#p-bank").is_hidden()
    side.fill("#partner-formue", "60000")
    til_resultat(side)
    assert side.evaluate("tilstand.aktuelleSvar.person.likvid_formue") == 60000


def test_samme_som_cpython(side):
    til_opsparingstrinnet(side)
    side.fill("#bank", "300000")
    til_resultat(side)
    g = json.dumps(side.evaluate("tilstand.aktuelleSvar"))
    b = side.evaluate("([g, d]) => kald('beregn', g, d)", [g, IDAG])
    c = app.beregn(g, IDAG)
    assert b["data"]["hovedtal"] == c["data"]["hovedtal"]
    assert b["data"]["formue"]["rest"] == pytest.approx(c["data"]["formue"]["rest"])


def test_axe_og_360_paa_opsparingstrinnet(side):
    til_opsparingstrinnet(side, "gift")
    side.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = side.evaluate("async () => (await axe.run(document, {runOnly: "
                         "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    side.set_viewport_size({"width": 360, "height": 800})
    side.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
