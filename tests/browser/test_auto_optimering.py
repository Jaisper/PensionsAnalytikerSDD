"""Feature 007b — den bedste plan regnes og vises med det samme (hovedtallet), og borgeren kan
skifte til sin egen plan. Uden stopalder starter ingen ordning før folkepensionsalderen."""
import pytest

pytestmark = pytest.mark.browser


def test_bedste_plan_er_hovedtallet(bedste_plan):
    p = bedste_plan.evaluate("tilstand.planer")
    assert p is not None, "den syntetiske rapport kan forbedres"
    tekst = bedste_plan.inner_text("#hovedtal-plan")
    assert "den bedste plan" in tekst and "Med din egen plan" in tekst
    bedste = bedste_plan.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    assert bedste >= p["egenMaaned"]
    fp = bedste_plan.evaluate("tilstand.v.graenser.folkepensionsalder")
    for o in bedste_plan.evaluate("tilstand.aktuelleSvar.ordninger"):
        egen = next(x for x in p["egen"]["ordninger"] if x["id"] == o["id"])
        if o["udbetaling_start_alder"] != egen["udbetaling_start_alder"]:
            assert o["udbetaling_start_alder"] >= fp
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
    bedste_plan.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = bedste_plan.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
