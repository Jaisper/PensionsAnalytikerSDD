"""Feature 021 T001 — indskud af beskattet løn i arbejdsårene.

Aldersopsparing betales af beskattet løn (PBL § 16) og trækkes fra årets rådighedsbeløb, som
løbende indskud på opsparing. Løbende indskud gælder også bank og frit depot (uden loft).
Borgeren er født 1. marts 1966: 60 år i 2026, folkepensionsalder 68, stop som 64.
"""
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Loen, Ordning, Pensionsprofil, beregn
from tests.conftest import BEREGNINGSDATO

ANT = Antagelser(afkast_efter_pal=0.03, inflation=0.0)
RATE = Ordning("rate", "ratepension", 1_000_000, 68, oprettet=date(2010, 1, 1), udbetaling_aar=10)
LOEN = Loen(500_000, stop_alder=64)


def person(*ordninger, opsparing=()):
    return Pensionsprofil(foedselsdato=date(1966, 3, 1), civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=(RATE,) + ordninger, opsparing=opsparing, loen=LOEN)


def regn(profil):
    return beregn(profil, ANT, 2026, BEREGNINGSDATO)


def test_aldersopsparing_med_loen_trækkes_fra_raadighedsbeloebet():
    alders = Ordning("alders", "aldersopsparing", 0, 68, oprettet=date(2026, 1, 1), aarlig_indbetaling=5_000)
    uden = regn(person())
    med = regn(person(alders))
    for alder in (60, 63):
        a, u = med.aar_ved(alder), uden.aar_ved(alder)
        assert a.indskud_opsparing == pytest.approx(5_000)
        assert a.netto_i_alt == pytest.approx(u.netto_i_alt)          # intet fradrag
        assert a.disponibel == pytest.approx(u.disponibel - 5_000)
    assert med.aar_ved(64).indskud_opsparing == 0                      # stopper ved stopalderen
    # Pengene kommer tilbage skattefrit fra 68 (64–67 er et indkomsthul uden opsparing).
    assert min(j.jaevn for j in med.jaevn.aar if j.alder >= 68) > min(j.jaevn for j in uden.jaevn.aar if j.alder >= 68)


def test_loebende_indskud_i_banken():
    uden = regn(person())
    med = regn(person(opsparing=(Aktiv("b", 0, aarligt_indskud=20_000),)))
    for alder in range(60, 64):
        assert med.aar_ved(alder).indskud_opsparing == pytest.approx(20_000)
    assert med.aar_ved(64).indskud_opsparing == 0
    assert med.formue_primo()[64] > 4 * 20_000                        # med afkast
    # Pengene bruges i indkomsthullet 64–67; fra 68 er niveauet det samme (før 023a testede vi
    # "større fra 68", som kun holdt på afrundingsstøj).
    assert min(j.jaevn for j in med.jaevn.aar if 64 <= j.alder < 68) > 20_000
    assert max(j.jaevn for j in uden.jaevn.aar if 64 <= j.alder < 68) == 0
    assert not any(a.kode == "ASK_OVER_LOFT" for a in med.advarsler)


def test_loebende_indskud_i_depotet_er_kostpris():
    res = regn(person(opsparing=(Aktiv("d", 0, type="depot", aarligt_indskud=20_000),)))
    # Kun afkastet er gevinst: den samlede aktieindkomst er under summen af indskuddene.
    assert 0 < sum(a.aktieindkomst for a in res.aar) < 4 * 20_000
