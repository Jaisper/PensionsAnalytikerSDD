"""Feature 007b — den bedste plan regnes og vises med det samme (hovedtallet), og borgeren kan
skifte til sin egen plan. Uden valgt stopalder starter ingen ændret ordning før stopalderen, som
udledes af den egne plans første udbetaling (030 FR-003; før 030: folkepensionsalderen)."""
import pytest

from tests.browser.conftest import indlaes_axe

pytestmark = pytest.mark.browser


def test_bedste_plan_er_hovedtallet(bedste_plan):
    p = bedste_plan.evaluate("tilstand.planer")
    assert p is not None, "den syntetiske rapport kan forbedres"
    tekst = bedste_plan.inner_text("#hovedtal-plan")
    assert "den bedste plan" in tekst and "Med din egen plan" in tekst
    bedste = bedste_plan.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    assert bedste >= p["egenMaaned"]
    stop = bedste_plan.evaluate("tilstand.v.graenser.stopalder.aktuel")
    assert stop <= bedste_plan.evaluate("tilstand.v.graenser.folkepensionsalder")
    for o in bedste_plan.evaluate("tilstand.aktuelleSvar.ordninger"):
        egen = next(x for x in p["egen"]["ordninger"] if x["id"] == o["id"])
        if o["udbetaling_start_alder"] != egen["udbetaling_start_alder"]:
            assert o["udbetaling_start_alder"] >= stop
    assert bedste_plan.fejl == []


def test_skift_til_egen_plan_og_tilbage(bedste_plan):
    p = bedste_plan.evaluate("tilstand.planer")
    bedste_plan.get_by_role("button", name="Brug min egen plan").click()
    bedste_plan.wait_for_function("() => tilstand.v.hovedtal.maaned === tilstand.planer.egenMaaned"
                               " && document.querySelector('#hovedtal-plan button')?.textContent === 'Brug den bedste plan'")
    assert bedste_plan.evaluate("tilstand.aktuelleSvar") == p["egen"]
    assert "Det er din egen plan" in bedste_plan.inner_text("#hovedtal-plan")
    bedste_plan.get_by_role("button", name="Brug den bedste plan").click()
    bedste_plan.wait_for_function("() => document.querySelector('#hovedtal-plan button')?.textContent === 'Brug min egen plan'")
    assert bedste_plan.evaluate("tilstand.aktuelleSvar") == p["bedste"]


def test_aendringerne_kan_ses(bedste_plan):
    bedste_plan.click("#hovedtal-plan summary")
    assert bedste_plan.locator("#hovedtal-plan li").count() >= 1


def test_axe_med_planlinjen(bedste_plan):
    bedste_plan.click("#hovedtal-plan summary")
    indlaes_axe(bedste_plan)
    fejl = bedste_plan.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
