"""Feature 035 — branchestandarden i brugerfladen (US1, US2, FR-007, FR-010). Syntetisk rapport."""
import re

import pytest

from tests.browser.conftest import koer_guide, vaelg_grundlag, vent_paa_planen

pytestmark = pytest.mark.browser


def tal(tekst):
    return [int(re.sub(r"\D", "", x)) for x in re.findall(r"\d[\d.]*(?= kr)", tekst)]


@pytest.fixture
def branche(side, tmp_path):
    from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    vaelg_grundlag(side, "branchestandard")
    koer_guide(side, pdf)
    vent_paa_planen(side)
    side.wait_for_function("() => /højt afkast/.test(document.querySelector('#hovedtal-spaend').textContent)")
    return side


def test_altid_som_pensionsselskaberne(ny_side):
    """035b: intet valg i guiden; afkast og inflation er valgfrie egne estimater."""
    s = ny_side
    s.goto(s.base_url)
    s.evaluate("motorKlar")
    assert s.evaluate("tilstand.grundlag") == "branchestandard"
    assert s.locator("input[name=grundlag]").count() == 0
    assert "Dine egne estimater (valgfrit)" in s.text_content("#egne-forventninger")
    assert s.evaluate("!document.querySelector('#egne-forventninger').hidden")


def test_tre_tal_med_branchens_benaevnelser(branche):
    s = branche
    assert "regnet som pensionsselskaberne" in s.inner_text("#hovedtal-grundlag")
    assert "1. halvår 2027" in s.inner_text("#hovedtal-grundlag")
    spaend = s.inner_text("#hovedtal-spaend")
    assert "Udbetaling ved højt afkast" in spaend and "Ved lavt afkast" in spaend
    hoej, lav = tal(spaend)[:2]
    forventet = int(s.locator("#hovedtal").get_attribute("data-vaerdi"))
    assert lav < forventet < hoej


def test_afkastskyderne_er_skjult(branche):
    assert branche.locator("#r-egne").is_hidden()
    assert branche.locator("#r-branche").is_visible()


def test_skift_til_egne_antagelser(branche):
    s = branche
    s.get_by_role("button", name="Brug mine egne estimater").click()
    s.wait_for_function("() => /dine egne estimater/.test(document.querySelector('#hovedtal-grundlag').textContent)")
    s.wait_for_function("() => /Hvis afkast og inflation/.test(document.querySelector('#hovedtal-spaend').textContent)")
    assert s.locator("#r-egne").is_visible()
    s.get_by_role("button", name="Regn som pensionsselskaberne").click()
    s.wait_for_function("() => /højt afkast/.test(document.querySelector('#hovedtal-spaend').textContent)")


def test_scenarietabellen_har_kun_levetid(branche):
    s = branche
    # Tabellen ligger i en lukket fold-ud: tæl rækkerne, når scenarierne er regnet.
    s.wait_for_function("() => document.querySelectorAll('#usikkerhed-tabel tbody tr').length === 3")
    raekker = s.locator("#usikkerhed-tabel tbody tr").all_text_contents()
    assert len(raekker) == 3 and all("Som selskaberne" in r for r in raekker)


def test_axe(branche):
    s = branche
    s.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = s.evaluate("async () => (await axe.run('#resultat', {runOnly: "
                      "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    assert s.fejl == []
