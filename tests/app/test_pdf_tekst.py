"""T002 — tekstudtræk, sidefilter og CPR-fjernelse (FR-001, FR-002, US3)."""
from datetime import date

import pytest

from pensionsoverblik.pdfimport.tekst import (
    PdfFejl, cpr_foedselsdato, fjern_cpr, relevante_sider, udtraek_sider,
)
from tests.app.pdfhjaelp import RAPPORT, lav_pdf


def test_udtraek_sider():
    sider = udtraek_sider(lav_pdf(RAPPORT))
    assert len(sider) == 4
    assert "Nuværende pensionsopsparinger" in sider[1]


def test_ikke_en_pdf():
    with pytest.raises(PdfFejl) as e:
        udtraek_sider(b"hej med dig")
    assert e.value.kode == "ikke_pdf"


def test_pdf_uden_tekst_er_scannet():
    with pytest.raises(PdfFejl) as e:
        udtraek_sider(lav_pdf([[]]))
    assert e.value.kode == "ingen_tekst"
    assert "pensionsinfo.dk" in e.value.besked


@pytest.mark.parametrize("cpr,forventet", [
    ("0105631234", date(1963, 5, 1)),     # 7. ciffer 1 → 1900-tallet
    ("0101054123", date(2005, 1, 1)),     # 4 og år ≤ 36 → 2000-tallet
    ("0101584123", date(1958, 1, 1)),     # 4 og år > 36 → 1900-tallet
    ("0101575123", date(2057, 1, 1)),     # 5–8 og år ≤ 57 → 2000-tallet
    ("0101585123", date(1858, 1, 1)),     # 5–8 og år > 57 → 1800-tallet
    ("3102631234", None),                 # ugyldig dato
])
def test_cpr_aarhundrede(cpr, forventet):
    assert cpr_foedselsdato(cpr) == forventet


def test_fjern_cpr_med_og_uden_bindestreg():
    tekst, foedt = fjern_cpr("CPR-nr. 010563-1234 og igen 0105631234. Aftale 123456.")
    assert "010563" not in tekst and "-1234" not in tekst and "0105631234" not in tekst
    assert tekst.count("[CPR fjernet]") == 2
    assert foedt == date(1963, 5, 1)
    assert "123456" in tekst  # aftalenumre bevares


def test_relevante_sider_frasorterer_reklame():
    sider = udtraek_sider(lav_pdf(RAPPORT))
    tekst = relevante_sider(sider)
    assert "Nuværende pensionsopsparinger" in tekst and "Dine aftaler" in tekst
    assert "Reklame" not in tekst


def test_relevante_sider_falder_tilbage_til_alt():
    assert "noget" in relevante_sider(["noget helt andet"])
