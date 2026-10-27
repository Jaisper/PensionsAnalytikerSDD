"""Feature 020 — forklaringer i tre niveauer i brugerfladen (US1, US2, FR-008, FR-010, SC-006, SC-007)."""
import pytest

from pensionsoverblik import app

pytestmark = pytest.mark.browser


def vent_paa_katalog(side):
    side.wait_for_function("() => !!tilstand.forklaringer")


def test_hovedtallet_forklares_paa_tre_niveauer_og_niveauet_huskes(resultat):
    vent_paa_katalog(resultat)
    resultat.click("#hovedtal-forklaring-boks summary")
    tekst1 = resultat.inner_text("#hovedtal-forklaring-tekst")
    assert "om måneden" in tekst1 and "Det største bidrag" in tekst1
    resultat.check('[data-niveauvaelger="hovedtal"] input[value="niveau3"]')
    assert "Forbrugsudjævning" in resultat.inner_text("#hovedtal-forklaring-tekst")
    assert resultat.evaluate("localStorage.getItem('forklaringsniveau')") == "niveau3"
    # Samme niveau i "Dit år".
    resultat.evaluate("visAar(tilstand.v.aar[0].alder)")
    assert resultat.is_checked('[data-niveauvaelger="aar"] input[value="niveau3"]')


def test_dit_aar_fra_tabellen_afstemmer(resultat):
    vent_paa_katalog(resultat)
    resultat.locator("#aar-tabel").evaluate("t => t.closest('details').open = true")
    resultat.evaluate("saetNiveau('niveau2')")
    knap = resultat.locator("#aar-tabel tbody th button").nth(3)
    knap.click()
    assert resultat.locator("#aar-forklaring").is_visible()
    v = resultat.evaluate("tilstand.v")
    a = v["aar"][3]
    assert f"Dit år {a['kalenderaar']}" in resultat.inner_text("#aar-forklaring-titel")
    sidste = resultat.locator("#aar-forklaring-tekst tbody tr").last.inner_text()
    assert sidste.startswith("I alt")
    assert resultat.evaluate("kr(tilstand.v.aar[3].netto)") in sidste


def test_klik_i_grafen_aabner_aaret(resultat):
    vent_paa_katalog(resultat)
    alder = resultat.evaluate("tilstand.v.aar[0].alder")
    i = resultat.evaluate("tilstand.graf.data.labels.indexOf(String(tilstand.v.aar[0].alder))")
    resultat.evaluate(f"tilstand.graf.options.onClick(null, [{{index: {i}}}], tilstand.graf)")
    assert f"du er {alder}" in resultat.inner_text("#aar-forklaring-titel")


def test_forklaringen_aabner_hurtigt(resultat):
    vent_paa_katalog(resultat)
    ms = resultat.evaluate("() => { const t = performance.now(); saetNiveau('niveau3'); visAar(tilstand.v.aar[5].alder); return performance.now() - t; }")
    assert ms < 300  # SC-007, uden kald til motoren


def test_katalog_samme_som_cpython(resultat):
    vent_paa_katalog(resultat)
    assert resultat.evaluate("tilstand.forklaringer") == app.forklaringer()


def test_axe_og_360(resultat):
    vent_paa_katalog(resultat)
    resultat.click("#hovedtal-forklaring-boks summary")
    resultat.evaluate("saetNiveau('niveau3'); visAar(tilstand.v.aar[2].alder)")
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
