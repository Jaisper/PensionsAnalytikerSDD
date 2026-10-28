"""Feature 017c T006 — løn som på lønsedlen i guiden (US1–US3, SC-003, FR-005, FR-006)."""
import json

import pytest

from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF
from tests.browser.test_gem import KODE, aabn

pytestmark = pytest.mark.browser


def med_rapport(side, tmp_path):
    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    side.set_input_files("#pdf-fil", str(pdf))
    side.wait_for_selector("#pdf-status p")
    side.fill("#kommune", "Aarhus")


def til_resultat(side):
    side.click("#naeste")                       # trin 2: ordninger
    for felt in side.query_selector_all("#ordninger input[id$='-udbetaling_start_alder']"):
        if not felt.input_value():
            felt.fill("70")
    side.click("#naeste")                       # trin 4: opsparing
    side.click("#naeste")                       # trin 5: forventninger
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")


def test_loensedlen_sendes_og_rapporten_vises_ved_procenterne(side, tmp_path):
    med_rapport(side, tmp_path)
    maaned = side.evaluate("tilstand.rapportIndbetaling['']")
    assert maaned > 0
    assert "om måneden" in side.inner_text("#pension-rapport")
    side.fill("#loen-maaned", "40.000")
    side.fill("#pension-eget", "4")
    side.fill("#pension-firma", "8,5")
    assert "% af lønnen" in side.inner_text("#pension-rapport")
    side.fill("#stop-alder", "64")
    til_resultat(side)
    loen = side.evaluate("tilstand.aktuelleSvar.person.loen")
    assert (loen["aarlig"], loen["pension_eget"], loen["pension_firma"]) == (480000, 0.04, 0.085)
    ordninger = side.evaluate("tilstand.aktuelleSvar.ordninger")
    assert all(o["fra_loen"] == (o["aarlig_indbetaling"] > 0) for o in ordninger if o["type"] != "kapitalpension")
    assert side.evaluate("tilstand.v.loen.maaned") > 0
    assert side.fejl == []


def test_procenter_uden_ordning_fra_loennen_giver_fejl_ved_feltet(side):
    side.fill("#foedselsdato", "1966-03-01")
    side.fill("#kommune", "Aarhus")
    side.fill("#loen-maaned", "40000")
    side.fill("#pension-firma", "8")
    side.click("#naeste")                       # trin 2 (ingen ordninger)
    side.click("#naeste")
    side.click("#naeste")
    side.click("#naeste")
    side.wait_for_selector('[data-felt~="loen.pension_firma"] .felt__fejl')
    assert "ordning" in side.inner_text('[data-felt~="loen.pension_firma"]')


def test_gemt_aarsloen_aabnes_som_maanedsloen(side, ny_side, tmp_path):
    """FR-005: en fil gemt før 017c har årslønnen i feltet "loen"."""
    side.fill("#foedselsdato", "1966-03-01")
    side.fill("#kommune", "Aarhus")
    side.fill("#stop-alder", "64")
    felter = side.evaluate("guideFelter()")
    felter.pop("loen-maaned")
    felter["loen"] = "480.000"
    fil = side.evaluate("([f, k]) => krypter({skema: GEM.skema, gemt: idag(), felter: f, ordninger: [], "
                        "partnerOrdninger: [], naesteId: 1, naestePid: 1, valg: {}}, k)", [felter, KODE])
    sti = tmp_path / "gammel.json"
    sti.write_text(json.dumps(fil), encoding="utf-8")
    ny_side.goto(ny_side.base_url)
    ny_side.evaluate("motorKlar")
    aabn(ny_side, sti)
    ny_side.wait_for_selector("#resultat:not([hidden])")
    assert ny_side.input_value("#loen-maaned") == "40.000"
    assert ny_side.evaluate("tilstand.aktuelleSvar.person.loen.aarlig") == 480000


def test_afkrydsning_pr_ordning_og_axe(side, tmp_path):
    med_rapport(side, tmp_path)
    side.click("#naeste")
    assert side.locator("#ordninger input[id$='-fra-loen']").count() > 0
    side.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = side.evaluate("async () => (await axe.run(document, {runOnly: "
                         "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
