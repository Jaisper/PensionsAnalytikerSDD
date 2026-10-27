"""Feature 020b — skifteren mellem dagens og årets kroner, "Sådan læser du …", kortenes forklaring
og ordlisten (US3, FR-008, FR-009, FR-010)."""
import pytest

pytestmark = pytest.mark.browser


def klar(side):
    side.wait_for_function("() => !!tilstand.forklaringer")


def test_skifteren_viser_aarets_kroner_og_huskes(resultat):
    klar(resultat)
    i = resultat.evaluate("tilstand.v.graf.aldre.indexOf(tilstand.v.aar.at(-1).alder)")
    real = resultat.evaluate(f"tilstand.v.graf.serier[0].vaerdier[{i}]")
    faktor = resultat.evaluate(f"tilstand.v.graf.realfaktor[{i}]")
    resultat.check("input[name=kroner][value=aarets]")
    vist = resultat.evaluate(f"tilstand.graf.data.datasets.find((d) => d.label === tilstand.v.graf.serier[0].titel).data[{i}]")
    assert vist == round(real / faktor)
    assert "i årets kroner" in resultat.inner_text("#kroner-tekst")
    assert "årets kroner" in resultat.inner_text("#kort")
    assert resultat.evaluate("localStorage.getItem('beloebsvisning')") == "aarets"
    assert "dagens kroner" in resultat.inner_text("#resultat .hero")  # hovedtallet er altid i dagens kroner


def test_grafens_laesevejledning_naevner_kun_det_viste(resultat):
    klar(resultat)
    resultat.click('[data-laes="graf"] summary')
    tekst = resultat.inner_text('[data-laes="graf"] .laes__tekst')
    titler = resultat.evaluate("tilstand.v.graf.serier.map((s) => s.titel)")
    assert all(t in tekst for t in titler)
    assert "Løn" not in titler and "Løn," not in tekst


def test_kortets_forklaring_foelger_niveauet(resultat):
    klar(resultat)
    knap = resultat.locator("#kort .info-knap").first
    knap.click()
    boks = resultat.locator("#kort [data-kort-forklaring]").first
    foer = boks.inner_text()
    resultat.evaluate("saetNiveau('niveau3')")
    assert boks.inner_text() != foer and "§" in boks.inner_text()


def test_ordlisten(resultat):
    klar(resultat)
    assert resultat.locator("#ordliste dt").count() >= 12


def test_axe_og_360(resultat):
    klar(resultat)
    resultat.evaluate("document.querySelectorAll('details').forEach((d) => (d.open = true))")
    resultat.check("input[name=kroner][value=aarets]")
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
