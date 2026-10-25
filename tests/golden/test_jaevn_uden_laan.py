"""Feature 010 T001 — den jævne udbetaling låner aldrig (FR-001, SC-001–SC-003).

Det faste beløb er det højeste ikke-faldende forløb (i dagens kroner), hvor bufferen aldrig er
negativ og ender i 0. Golden cases regnet i hånden med rente 0 og inflation 0, så niveauet er
gennemsnittet af det, der er kommet ind, til og med det bindende år.
"""
from datetime import date

import pytest
from hypothesis import given, settings, strategies as st

from pensionskerne.jaevn import beregn_jaevn
from pensionskerne.model import Aarsresultat


def raekker(netto: list[float], start_alder: int = 65) -> tuple[Aarsresultat, ...]:
    return tuple(
        Aarsresultat(alder=start_alder + i, kalenderaar=2030 + i, kilder=(), personlig_indkomst=0.0, skat_i_alt=0.0,
                     indtaegtsgrundlag=0.0, tillaegsprocent=0, netto_i_alt=x, netto_real=x, realfaktor=1.0,
                     engangsbeloeb_netto=0.0, sporing=(), flag=())
        for i, x in enumerate(netto)
    )


def niveauer(netto, engangs=None, rente=0.0, inflation=0.0):
    j = beregn_jaevn(raekker(netto), engangs or {}, rente, inflation, 2030)
    return [round(a.jaevn, 6) for a in j.aar], [round(a.buffer_rest, 6) for a in j.aar]


def test_penge_der_kommer_senere_kan_ikke_bruges_foer():
    # Segment fra år 0: min(0/1, 100/2, 300/3) = 0 ved k=0 → 0. Fra år 1: min(100, 300/2) = 100. År 2: 200.
    jaevn, buffer = niveauer([0, 100, 200])
    assert jaevn == [0, 100, 200]
    assert buffer == [0, 0, 0]


def test_penge_der_kommer_foerst_fordeles():
    # min(300/1, 300/2, 300/3) = 100 ved k=2 → 100 hvert år; bufferen 200, 100, 0.
    jaevn, buffer = niveauer([300, 0, 0])
    assert jaevn == [100, 100, 100]
    assert buffer == [200, 100, 0]


def test_blandet_forloeb_stiger_i_trin():
    # [100, 0, 300, 0]: fra år 0: min(100, 50, 133,3, 100) = 50 ved k=1 → 50, 50 (buffer 50, 0).
    # Fra år 2: min(300, 150) = 150 → 150, 150.
    jaevn, buffer = niveauer([100, 0, 300, 0])
    assert jaevn == [50, 50, 150, 150]
    assert buffer == [50, 0, 150, 0]


def test_engangsbeloeb_i_et_senere_aar():
    # Indbetalinger [100, 100+400, 100]: fra år 0: min(100, 300, 233,3) = 100 → 100.
    # Fra år 1: min(500, 300) = 300 → 300, 300.
    jaevn, buffer = niveauer([100, 100, 100], engangs={66: 400})
    assert jaevn == [100, 300, 300]
    assert buffer == [0, 200, 0]


def test_rente_og_inflation():
    # [300, 0, 0] med rente 10 % og inflation 10 %: g/(1+r) = 1 → c = 300/3 = 100; niveau 100, 110, 121.
    j = beregn_jaevn(raekker([300, 0, 0]), {}, 0.10, 0.10, 2030)
    assert [round(a.jaevn, 6) for a in j.aar] == [100, 110, 121]
    assert j.aar[-1].buffer_rest == pytest.approx(0, abs=1e-6)
    assert j.niveau_foerste_aar == pytest.approx(100)


@given(st.lists(st.floats(min_value=0, max_value=500_000), min_size=1, max_size=30),
       st.floats(min_value=0, max_value=0.08), st.floats(min_value=0, max_value=0.05))
@settings(max_examples=150, deadline=None)
def test_egenskab_aldrig_laan_ikke_faldende_og_ender_i_nul(netto, rente, inflation):
    j = beregn_jaevn(raekker(netto), {}, rente, inflation, 2030)
    g = 1 + inflation
    real = [a.jaevn / g ** i for i, a in enumerate(j.aar)]
    assert all(a.buffer_rest >= -1e-6 * (1 + max(netto)) for a in j.aar)
    assert all(real[i + 1] >= real[i] - 1e-6 * (1 + max(netto)) for i in range(len(real) - 1))
    assert j.aar[-1].buffer_rest == pytest.approx(0, abs=1e-6 * (1 + sum(netto)))
