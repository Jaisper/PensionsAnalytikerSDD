"""Opsparingstrinnet i guiden efter review 2026-11-24: klar ordlyd, én overskrift pr. type, og felter, der kun
vises, når de er relevante (Princip X)."""
import pytest

from tests.browser.test_opsparing import til_opsparingstrinnet

pytestmark = pytest.mark.browser

TRIN = '.trin[data-trin="4"]'


def synlig(side, sel):
    return side.locator(sel).is_visible()


def test_ordlyden_er_klar(side):
    til_opsparingstrinnet(side)
    tekst = side.inner_text(TRIN)
    for gammel in ("du ikke har solgt", "Står i din bank", "Vi bruger først banken",
                   "Det gælder også for felterne nedenfor", "(valgfri)"):
        assert gammel not in tekst, gammel
    assert "valgfri" in side.inner_text(f"{TRIN} .hjaelp")          # sagt én gang i indledningen
    overskrifter = side.locator(f"{TRIN} .opsparing-gruppe h3").all_inner_texts()
    assert overskrifter[:3] == ["Bank", "Frit depot", "Aktiesparekonto"]


def test_felterne_vises_naar_de_er_relevante(side):
    til_opsparingstrinnet(side)
    for sel in ("#bank-i-plan", "#depot-gevinst", "#depot-i-plan", "#ask-i-plan"):
        assert not synlig(side, sel), sel
    side.fill("#bank", "100000")
    assert synlig(side, "#bank-i-plan")
    side.fill("#depot", "200000")
    assert synlig(side, "#depot-gevinst") and synlig(side, "#depot-i-plan")
    assert "minus det, du har købt for" in side.inner_text('[data-felt="opsparing[depot].urealiseret_gevinst"]')
    side.fill("#ask", "50000")
    assert synlig(side, "#ask-i-plan")
    side.fill("#depot", "")
    assert not synlig(side, "#depot-gevinst")


def test_indskud_paa_aktiesparekonto_kraever_loen(side):
    til_opsparingstrinnet(side)
    assert not synlig(side, "#ask-indskud")
    # En gemt værdi i et skjult felt sendes ikke (ellers fejl om løn ved et felt, borgeren ikke kan se).
    side.evaluate("document.querySelector('#ask-indskud').value = '20000'")
    assert side.evaluate("opsparingSvar()") == []
    side.click("#tilbage")
    side.click("#tilbage")
    side.fill("#loen-maaned", "40000")
    side.click("#naeste")
    side.click("#naeste")
    assert synlig(side, "#ask-indskud") and synlig(side, "#ask-i-plan")
    assert side.evaluate("opsparingSvar()")[0]["aarligt_indskud"] == 20000
