"""T047 — jævn udbetaling (US7, FR-080, FR-081)."""
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, beregn
from tests.conftest import BEREGNINGSDATO, enlig_profil

A = Antagelser(afkast_efter_pal=0.04, inflation=0.02)


def _res(*ordninger, antagelser=A):
    rate = Ordning("rate", "ratepension", 800_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    return beregn(enlig_profil(ordninger=(rate, *ordninger)), antagelser, 2026, BEREGNINGSDATO)


def test_buffer_gaar_op_i_nul_til_sidst():
    ald = Ordning("ald", "aldersopsparing", 200_000, 65, oprettet=date(2010, 1, 1))
    j = _res(ald).jaevn
    assert j.aar[-1].buffer_rest == pytest.approx(0, abs=1)


def test_konstant_i_dagens_koebekraft():
    ald = Ordning("ald", "aldersopsparing", 200_000, 65, oprettet=date(2010, 1, 1))
    j = _res(ald).jaevn
    real = [a.jaevn / 1.02 ** i for i, a in enumerate(j.aar)]
    assert max(real) == pytest.approx(min(real))
    assert j.niveau_real == pytest.approx(j.niveau_foerste_aar / 1.02 ** (2028 - 2026))


def test_senere_engangsbeloeb_hæver_niveauet_fra_ankomst():
    kap = Ordning("kap", "kapitalpension", 300_000, 72, oprettet=date(2010, 1, 1))
    j = _res(kap).jaevn
    real = {a.alder: a.jaevn / 1.02 ** (a.alder - 65) for a in j.aar}
    assert real[72] > real[71]
    assert all(real[a + 1] >= real[a] - 1e-6 for a in range(65, 90))
    assert j.aar[-1].buffer_rest == pytest.approx(0, abs=1)


def test_fravalgt_engangsbeloeb_indgaar_ikke():
    med = _res(Ordning("ald", "aldersopsparing", 200_000, 65, oprettet=date(2010, 1, 1)))
    uden = _res(Ordning("ald", "aldersopsparing", 200_000, 65, oprettet=date(2010, 1, 1), i_buffer=False))
    assert uden.jaevn.niveau_foerste_aar < med.jaevn.niveau_foerste_aar
    assert uden.aar_ved(65).engangsbeloeb_netto == pytest.approx(200_000 * 1.04 ** 2)
    assert "BUFFER_YDELSE_FORENKLING" in [a.kode for a in med.advarsler]
    assert "BUFFER_YDELSE_FORENKLING" not in [a.kode for a in uden.advarsler]
