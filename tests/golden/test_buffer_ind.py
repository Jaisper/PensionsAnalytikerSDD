"""Feature 029 — det, der kommer ind i bufferen hvert år (`JaevnAar.ind_buffer`): engangsbeløb og
opsparing, men ikke saldoen, der føres videre fra arbejdsårene. Ren bogføring, ingen ny regel.

Bufferen ved årets udgang er (sidste års saldo + ind + til side − fra bufferen) × (1 + rente)."""
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Loen, Ordning, beregn
from pensionskerne.jaevn import beregn_jaevn
from tests.conftest import BEREGNINGSDATO, enlig_profil
from tests.golden.test_jaevn_uden_laan import raekker


def test_ind_er_engangsbeloebet_i_aaret():
    j = beregn_jaevn(raekker([0, 100, 0, 0]), {66: 300.0}, 0.0, 0.0, 2030)
    assert [a.ind_buffer for a in j.aar] == [0, 300, 0, 0]


@pytest.mark.parametrize("rente", [0.0, 0.05])
def test_saldoen_gaar_op_med_ind_og_ud(rente):
    j = beregn_jaevn(raekker([0, 100, 400, 0, 50]), {66: 300.0, 68: 200.0}, rente, 0.02, 2030)
    forrige = 0.0
    for a in j.aar:
        assert a.buffer_rest == pytest.approx((forrige + a.ind_buffer + a.til_buffer - a.fra_buffer) * (1 + rente))
        forrige = a.buffer_rest


def _profiler():
    rate = Ordning("rate", "ratepension", 1_500_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    kap = Ordning("kap", "kapitalpension", 900_000, 64, oprettet=date(2000, 1, 1), udbetalingsform="portioner",
                  udbetaling_aar=3)
    ald = Ordning("ald", "aldersopsparing", 600_000, 79, oprettet=date(2015, 1, 1))
    loen = Loen(600_000, stop_alder=64)
    return [
        ("portioner", enlig_profil(foedselsdato=date(1971, 3, 1), ordninger=(rate, kap, ald), loen=loen)),
        ("bank og indskud", enlig_profil(foedselsdato=date(1971, 3, 1), ordninger=(rate, kap), loen=loen,
                                         opsparing=(Aktiv("b", 200_000, aarligt_indskud=24_000),))),
    ]


@pytest.mark.parametrize("profil", [p for _, p in _profiler()], ids=[n for n, _ in _profiler()])
def test_med_arbejdsaar_er_den_overfoerte_saldo_ikke_ind(profil):
    # Uden afkast er saldoen summen af ind, til side og fra bufferen år for år, også over stopalderen.
    res = beregn(profil, Antagelser(afkast_efter_pal=0.0, inflation=0.0), 2026, BEREGNINGSDATO)
    forrige = 0.0
    for a in res.jaevn.aar:
        assert a.buffer_rest == pytest.approx(forrige + a.ind_buffer + a.til_buffer - a.fra_buffer, abs=0.01), a.alder
        forrige = a.buffer_rest
    assert sum(a.ind_buffer for a in res.jaevn.aar) > 0
