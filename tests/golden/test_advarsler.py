"""T040 — advarsler og flag (FR-072)."""
from datetime import date

from pensionskerne import Antagelser, Ordning, beregn
from tests.conftest import BEREGNINGSDATO, enlig_profil


def test_mellemskat_et_interval_pr_sammenhaengende_periode():
    rate = Ordning("stor", "ratepension", 8_000_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    res = beregn(enlig_profil(ordninger=(rate,)), Antagelser(afkast_efter_pal=0, inflation=0),
                 2026, BEREGNINGSDATO)
    mellem = [a for a in res.advarsler if a.kode == "MELLEMSKAT_INTERVAL"]
    assert len(mellem) == 1 and mellem[0].aldre == (65, 74)


def test_ukendt_oprettelse_giver_advarsel_ikke_fejl():
    rate = Ordning("r", "ratepension", 100_000, 64, oprettet=None)
    res = beregn(enlig_profil(ordninger=(rate,)), Antagelser(), 2026, BEREGNINGSDATO)
    assert "UDBETALING_FOER_LOVLIG_ALDER" in [a.kode for a in res.advarsler]


def test_ikke_verificeret_post_flagges_i_aaret():
    res = beregn(enlig_profil(), Antagelser(), 2026, BEREGNINGSDATO)
    # Kommuneskatten er 'sekundaer' (afventer krydstjek) og flagges i hvert år, den bruges.
    assert "sekundaer:kommune.aarhus" in res.aar_ved(65).flag
    # Skønnet ATP flagges kun i de år, hvor ATP udbetales.
    assert "skoennet_atp" in res.aar_ved(70).flag
    assert "skoennet_atp" not in res.aar_ved(65).flag
