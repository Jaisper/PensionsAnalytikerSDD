"""Feature 020d — metodesiden (US4), eksport (US6) og udskrift."""
import json

import pytest

from tests.browser.conftest import indlaes_axe

from pensionskerne import register
from pensionsoverblik import app

pytestmark = pytest.mark.browser


def test_metodesiden_uden_data(side):
    side.click("#metode-link")
    side.wait_for_selector("#metode:not([hidden]) .metode-emne")
    m = app.metode()
    assert side.locator("#metode .metode-emne").count() == len(m["forklaringer"]["emner"])
    assert side.locator("#metode-satser tbody tr").count() == len(register.poster(m["satsaar"]))
    assert side.locator("#metode-forenklinger li").count() == len(register.forenklinger())
    foer = side.inner_text("#metode-emner")
    side.check('[data-niveauvaelger="metode"] input[value="niveau3"]')
    assert side.inner_text("#metode-emner") != foer and "{" not in side.inner_text("#metode-emner")
    assert side.evaluate("tilstand.metode") == m


def test_eksport_json_og_csv(resultat):
    with resultat.expect_download() as dl:
        resultat.click("#eksport-json")
    data = json.loads(open(dl.value.path(), encoding="utf-8").read())
    assert data["input"] == resultat.evaluate("tilstand.aktuelleSvar")
    assert dl.value.suggested_filename.endswith(".json")
    with resultat.expect_download() as dl:
        resultat.click("#eksport-csv")
    tekst = open(dl.value.path(), encoding="utf-8-sig").read()
    assert tekst.splitlines()[0].startswith("Alder;Kalenderår")
    assert len(tekst.splitlines()) == len(data["aar"]) + 1


def test_udskrift_aabner_alle_fold_uder_og_lukker_dem_igen(resultat):
    lukkede = resultat.evaluate("document.querySelectorAll('#resultat details:not([open])').length")
    assert lukkede > 0
    resultat.evaluate("window.dispatchEvent(new Event('beforeprint'))")
    assert resultat.evaluate("document.querySelectorAll('#resultat details:not([open])').length") == 0
    resultat.evaluate("window.dispatchEvent(new Event('afterprint'))")
    assert resultat.evaluate("document.querySelectorAll('#resultat details:not([open])').length") == lukkede


def test_axe_og_360(side):
    side.click("#metode-link")
    side.wait_for_selector("#metode:not([hidden]) .metode-emne")
    indlaes_axe(side)
    fejl = side.evaluate("async () => (await axe.run(document, {runOnly: "
                         "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    side.set_viewport_size({"width": 360, "height": 800})
    side.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)


def test_satser_og_kilder_er_venstrestillet(side):
    # Produktejer 2026-11-24: alle celler i tabellen "Satser og kilder" venstrestilles.
    side.click("#metode-link")
    side.wait_for_selector("#metode-satser tbody tr")
    justering = side.evaluate("""() => [...document.querySelectorAll('#metode-satser th, #metode-satser td')]
        .map((c) => getComputedStyle(c).textAlign)""")
    assert justering and set(justering) <= {"left", "start"}, set(justering)
