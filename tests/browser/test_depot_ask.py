"""Feature 013b T006 — frit depot og aktiesparekonto i guiden og resultatet (US1, US2)."""
import pytest

from tests.browser.test_opsparing import til_opsparingstrinnet, til_resultat

pytestmark = pytest.mark.browser


def test_depot_og_aktiesparekonto_sendes_og_beskattes(side):
    til_opsparingstrinnet(side)
    side.fill("#depot", "300000")
    side.fill("#depot-gevinst", "120000")
    side.fill("#ask", "100000")
    side.uncheck("#ask-i-plan")
    til_resultat(side)
    assert side.evaluate("tilstand.aktuelleSvar.person.opsparing") == [
        {"id": "depot", "type": "depot", "saldo": 300000, "i_plan": True, "urealiseret_gevinst": 120000},
        {"id": "ask", "type": "ask", "saldo": 100000, "i_plan": False, "aarligt_indskud": 0}]
    aar = side.evaluate("tilstand.v.aar")
    assert sum(a["aktieindkomst"] for a in aar) > 0
    assert all(a["skat_aktiesparekonto"] > 0 for a in aar)
    assert side.fejl == []


def test_tom_gevinst_giver_antagelsen(side):
    til_opsparingstrinnet(side)
    side.fill("#depot", "200000")
    til_resultat(side)
    assert side.evaluate("tilstand.aktuelleSvar.person.opsparing[0].urealiseret_gevinst") is None
    # Halvdelen er gevinst i dag, og afkastet lægger mere til, før der sælges.
    assert side.evaluate("tilstand.v.aar.reduce((s, a) => s + a.aktieindkomst, 0)") > 100000


def test_indskud_uden_loen_giver_fejl_ved_feltet(side):
    til_opsparingstrinnet(side)
    side.fill("#ask-indskud", "20000")
    side.click("#naeste")                       # trin 5: forventninger
    side.click("#naeste")
    side.wait_for_selector('[data-felt="opsparing[ask].aarligt_indskud"] .felt__fejl')
    assert "løn" in side.inner_text('[data-felt="opsparing[ask].aarligt_indskud"]')


def test_axe_paa_opsparingstrinnet(side):
    til_opsparingstrinnet(side)
    side.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = side.evaluate("async () => (await axe.run(document, {runOnly: "
                         "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
