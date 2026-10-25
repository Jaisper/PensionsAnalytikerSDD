"""T018 — private ordninger: § 11 A-rater (A9), livsvarig, lofter, engangsbeløb."""
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, beregn
from pensionskerne.regler.ordninger import (
    engangs_netto, indbetalingsloft, livsvarig_ydelse, rateplan,
)
from tests.conftest import BEREGNINGSDATO, enlig_profil


def test_rate_11a_uden_afkast_er_lineaer():
    assert rateplan(1_000_000, 10, 0.0) == pytest.approx([100_000] * 10)


def test_rate_11a_stiger_med_afkast():
    rater = rateplan(500_000, 10, 0.03)
    assert rater[0] == pytest.approx(50_000)  # JV C.A.10.2.2.4.1's eksempel
    assert all(b > a for a, b in zip(rater, rater[1:]))


def test_rate_11a_opbruger_saldoen():
    rater = rateplan(500_000, 10, 0.03)
    saldo = 500_000
    for rate in rater:
        saldo = (saldo - rate) * 1.03
    assert saldo == pytest.approx(0, abs=1e-6)


def test_livsvarig_ydelse_opbruger_saldoen_over_horisonten():
    y = livsvarig_ydelse(1_000_000, 20, 0.03)
    nutidsvaerdi = sum(y / 1.03 ** i for i in range(20))
    assert nutidsvaerdi == pytest.approx(1_000_000)
    assert livsvarig_ydelse(1_000_000, 20, 0.0) == 50_000


def test_lofter(o2026):
    assert indbetalingsloft("ratepension", 50, 68, o2026) == 68_700
    assert indbetalingsloft("aldersopsparing", 60, 68, o2026) == 9_900
    assert indbetalingsloft("aldersopsparing", 61, 68, o2026) == 9_900   # 7 år til fp
    assert indbetalingsloft("aldersopsparing", 62, 68, o2026) == 64_200  # under 7 år
    assert indbetalingsloft("livsvarig", 62, 68, o2026) is None


def test_engangsbeloeb(o2026):
    assert engangs_netto("aldersopsparing", 100_000, o2026) == 100_000
    assert engangs_netto("kapitalpension", 100_000, o2026) == pytest.approx(60_000)


def test_ratepensionsloft_flytter_overskud_til_livsvarig(nul_antagelser):
    rate = Ordning("rate", "ratepension", 0, 65, oprettet=date(2010, 1, 1), aarlig_indbetaling=100_000)
    res = beregn(enlig_profil(ordninger=(rate,)), nul_antagelser, 2026, BEREGNINGSDATO)
    assert "RATEPENSION_LOFT" in [a.kode for a in res.advarsler]
    aar65 = res.aar_ved(65)
    kilder = {k.kilde_id: k for k in aar65.kilder}
    assert kilder["rate"].brutto == pytest.approx(2 * 68_700 / 10)       # 2 indbetalingsår (63, 64)
    assert "ratepension_overskud_livsvarig" in kilder


def test_engangsbeloeb_udbetales_i_startaaret(nul_antagelser):
    ald = Ordning("ald", "aldersopsparing", 200_000, 66, oprettet=date(2010, 1, 1))
    kap = Ordning("kap", "kapitalpension", 100_000, 66, oprettet=date(2010, 1, 1))
    res = beregn(enlig_profil(ordninger=(ald, kap)), nul_antagelser, 2026, BEREGNINGSDATO)
    assert res.aar_ved(66).engangsbeloeb_netto == pytest.approx(260_000)
    assert res.aar_ved(66).personlig_indkomst == 0  # hverken aldersopsparing eller kapitalpension er PI


def test_aldersopsparing_indgaar_ikke_i_indtaegtsgrundlag(nul_antagelser):
    ald = Ordning("ald", "aldersopsparing", 500_000, 69, oprettet=date(2010, 1, 1))
    res = beregn(enlig_profil(ordninger=(ald,), atp_aarlig=0), nul_antagelser, 2026, BEREGNINGSDATO)
    assert res.aar_ved(69).indtaegtsgrundlag == 0


def test_opsparing_med_afkast_og_indbetaling():
    liv = Ordning("liv", "livsvarig", 100_000, 65, oprettet=date(2010, 1, 1), aarlig_indbetaling=10_000)
    a = Antagelser(afkast_efter_pal=0.05, inflation=0.0, livsvarig_horisont_alder=85)
    res = beregn(enlig_profil(ordninger=(liv,)), a, 2026, BEREGNINGSDATO)
    saldo_65 = (100_000 * 1.05 + 10_000) * 1.05 + 10_000   # to år (63, 64), indbetaling ultimo
    kilde = res.aar_ved(65).kilder[0]
    assert kilde.brutto == pytest.approx(livsvarig_ydelse(saldo_65, 20, 0.05))
