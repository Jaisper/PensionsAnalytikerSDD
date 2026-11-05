"""Feature 035c — bufferens afkast med branchestandarden.

Uden eget afkast følger bufferen (engangsbeløb og opsparing uden for pension) Rådet for
Afkastforventningers langsigtede afkast for obligationer efter investeringsomkostninger og PAL-skat:
(0,035 − 0,0022) × (1 − 0,153). Har borgeren selv angivet afkastet, følger bufferen det, både med
branchestandarden og med egne antagelser.
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Ordning, Pensionsprofil, beregn
from tests.conftest import BEREGNINGSDATO

RAADET_OBLIGATIONER = (0.035 - 0.0022) * (1 - 0.153)
BRANCHE = Antagelser(beregningsgrundlag="branchestandard")


def person(*ordninger, opsparing=()):
    return Pensionsprofil(foedselsdato=date(1964, 3, 1), civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=ordninger, opsparing=opsparing)


RATE = Ordning("rate", "ratepension", 800_000, 67, oprettet=date(2010, 1, 1), udbetaling_aar=10)
ALDERS = Ordning("alders", "aldersopsparing", 300_000, 67)  # engangsbeløb i bufferen


def regn(profil, antagelser=BRANCHE):
    return beregn(profil, antagelser, 2026, BEREGNINGSDATO)


def koder(res):
    return {a.kode for a in res.advarsler}


def test_uden_eget_afkast_folger_bufferen_raadet():
    res = regn(person(RATE, ALDERS))
    assert res.antagelser.buffer_afkast_efter_pal == pytest.approx(RAADET_OBLIGATIONER)
    assert res.antagelser.afkast_efter_pal == Antagelser().afkast_efter_pal  # dit estimat er uændret
    assert "BUFFER_AFKAST_BRANCHE" in koder(res)
    a = next(a for a in res.advarsler if a.kode == "BUFFER_AFKAST_BRANCHE")
    assert "2,8 %" in a.besked and "raadet.lang.afkast" in a.registerposter


def test_hoejt_og_lavt_forloeb_har_samme_bufferafkast():
    res = regn(person(RATE, ALDERS))
    for f in res.prognose.values():
        assert f.antagelser.buffer_afkast_efter_pal == pytest.approx(RAADET_OBLIGATIONER)


def test_eget_afkast_folges_ogsaa_med_branchestandarden():
    res = regn(person(RATE, ALDERS), replace(BRANCHE, afkast_efter_pal=0.05, afkast_angivet=True))
    assert res.antagelser.buffer_afkast_efter_pal is None
    assert res.antagelser.afkast_efter_pal == 0.05
    assert "BUFFER_AFKAST_BRANCHE" not in koder(res)
    assert "forenkling:branchestandard_opsparing_fast_afkast" in res.aar[0].flag


def test_bufferens_afkast_giver_kapitalindkomst():
    """Bufferens afkast er kapitalindkomst. (Det faste beløb stiger ikke nødvendigvis med det: skat og
    modregning i pensionstillæg og ældrecheck kan tage det meste.)"""
    nul = regn(person(RATE, ALDERS), replace(BRANCHE, afkast_efter_pal=0.0, afkast_angivet=True))
    raadet = regn(person(RATE, ALDERS))
    assert sum(a.kapitalindkomst for a in nul.aar) == 0
    assert sum(a.kapitalindkomst for a in raadet.aar) > 0


def test_ingen_besked_uden_noget_i_bufferen():
    assert "BUFFER_AFKAST_BRANCHE" not in koder(regn(person(RATE)))


def test_opsparing_uden_for_pension_giver_besked():
    assert "BUFFER_AFKAST_BRANCHE" in koder(regn(person(RATE, opsparing=(Aktiv("bank", 200_000),))))


def test_egne_antagelser_er_uaendrede():
    """SC-001: med egne antagelser bruger bufferen afkastet som før; feltet er None."""
    p = person(RATE, ALDERS)
    a = Antagelser(afkast_efter_pal=0.03)
    res = regn(p, a)
    assert res.antagelser.buffer_afkast_efter_pal is None
    assert [x.netto_i_alt for x in res.aar] == \
        pytest.approx([x.netto_i_alt for x in regn(p, replace(a, buffer_afkast_efter_pal=0.03)).aar])
