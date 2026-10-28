"""Feature 017c T001 — løn som på lønsedlen: bruttoløn og pensionsprocenter (SC-001, SC-002, FR-004).

Inflation 0. Borgeren er født 1. marts 1966: 60 år i 2026 og folkepensionsalder 68.
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Loen, Ordning, UgyldigtInput
from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.loen import ligningsmaessige_fradrag, pension_af_loen
from pensionskerne.regler.skat import beregn_skat
from tests.golden.test_loen import person, regn

O = Regelopslag(2026, 2026, 0.0)
AM = O.v("skat.am_bidrag")
BRUTTO = 40_000 * 12
RATE = Ordning("rate", "ratepension", 1_000_000, 68, oprettet=date(2010, 1, 1), udbetaling_aar=10, fra_loen=True)
LIV = Ordning("liv", "livsvarig", 500_000, 68, aarlig_indbetaling=10_000, fra_loen=True)
PRIVAT = Ordning("privat", "ratepension", 100_000, 68, oprettet=date(2010, 1, 1), udbetaling_aar=10,
                 aarlig_indbetaling=5_000)


def flaget(res, navn):
    return any(navn in a.flag for a in res.aar)


def test_pension_af_loen():
    loen, indbetaling = pension_af_loen(BRUTTO, 0.04, 0.08, O)
    assert loen == pytest.approx(BRUTTO * 1.08)
    assert indbetaling == pytest.approx(BRUTTO * 0.12 * (1 - AM))


def test_personlig_indkomst_og_netto_som_paa_loensedlen():
    """SC-001: AM-bidrag af løn og hele pensionsbidraget; egen andel trækkes fra før skat."""
    res = regn(person(Loen(BRUTTO, stop_alder=64, pension_eget=0.04, pension_firma=0.08), ordninger=(RATE,)))
    a = res.aar_ved(60)
    eget, firma = BRUTTO * 0.04, BRUTTO * 0.08
    pi = (BRUTTO - eget) * (1 - AM)
    lmf = ligningsmaessige_fradrag(BRUTTO + firma, 60, 68, O)
    skat = beregn_skat(pi, O.kommuneskat("aarhus"), 0.0, O, ligningsmaessige_fradrag=lmf).total
    assert a.netto_i_alt == pytest.approx(pi - skat)
    assert flaget(res, "forenkling:pensionsprocent_af_bruttoloen")


def test_svarer_til_aarsloen_inkl_firmabidrag_og_indbetaling_efter_am():
    """Lønsedlen er en anden måde at skrive det samme på som 017's årsløn og indbetaling."""
    seddel = regn(person(Loen(BRUTTO, stop_alder=64, pension_eget=0.04, pension_firma=0.08), ordninger=(RATE,)))
    aars = regn(person(Loen(BRUTTO * 1.08, stop_alder=64),
                       ordninger=(replace(RATE, aarlig_indbetaling=BRUTTO * 0.12 * (1 - AM), fra_loen=False),)))
    assert [a.netto_i_alt for a in seddel.aar] == pytest.approx([a.netto_i_alt for a in aars.aar])


def test_fordeles_efter_rapporten_og_private_ordninger_er_uaendrede():
    """SC-002: forholdet 0 : 10.000 giver alt til den livsvarige; den private beholder sit beløb."""
    total = BRUTTO * 0.12 * (1 - AM)
    seddel = regn(person(Loen(BRUTTO, stop_alder=64, pension_eget=0.04, pension_firma=0.08),
                         ordninger=(RATE, LIV, PRIVAT)))
    aars = regn(person(Loen(BRUTTO * 1.08, stop_alder=64),
                       ordninger=(replace(RATE, fra_loen=False), replace(LIV, aarlig_indbetaling=total, fra_loen=False),
                                  PRIVAT)))
    assert [a.netto_i_alt for a in seddel.aar] == pytest.approx([a.netto_i_alt for a in aars.aar])


def test_ligelig_fordeling_naar_alle_er_nul():
    total = BRUTTO * 0.12 * (1 - AM)
    liv = replace(LIV, aarlig_indbetaling=0)
    seddel = regn(person(Loen(BRUTTO, stop_alder=64, pension_eget=0.04, pension_firma=0.08), ordninger=(RATE, liv)))
    aars = regn(person(Loen(BRUTTO * 1.08, stop_alder=64),
                       ordninger=(replace(RATE, aarlig_indbetaling=total / 2, fra_loen=False),
                                  replace(liv, aarlig_indbetaling=total / 2, fra_loen=False))))
    assert [a.netto_i_alt for a in seddel.aar] == pytest.approx([a.netto_i_alt for a in aars.aar])


def test_uden_procenter_er_alt_som_foer():
    med = regn(person(Loen(500_000, stop_alder=64), ordninger=(RATE,)))
    uden = regn(person(Loen(500_000, stop_alder=64), ordninger=(replace(RATE, fra_loen=False),)))
    assert [a.netto_i_alt for a in med.aar] == [a.netto_i_alt for a in uden.aar]
    assert not flaget(med, "forenkling:pensionsprocent_af_bruttoloen")


def test_procenter_uden_ordning_fra_loennen_giver_fejl():
    with pytest.raises(UgyldigtInput) as e:
        regn(person(Loen(BRUTTO, pension_firma=0.08), ordninger=(PRIVAT,)))
    assert e.value.felt == "loen.pension_firma"


@pytest.mark.parametrize("felt", ["pension_eget", "pension_firma"])
def test_procenten_skal_vaere_mellem_0_og_100(felt):
    with pytest.raises(UgyldigtInput) as e:
        regn(person(Loen(BRUTTO, **{felt: 1.2}), ordninger=(RATE,)))
    assert e.value.felt == f"loen.{felt}"
