"""Feature 012 T001 — ægtefællers skatteregler (PSL § 10, stk. 3, og § 7, stk. 5).

Kommuneskat 25 %, kirkeskat 0: flad sats = 12,01 % + 25 % = 37,01 %. Personfradrag 54.100 kr.
"""
import pytest

from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.skat import beregn_skat

O = Regelopslag(2026, 2026, 0.0)
FLAD = 0.3701


def skat(pi, ki=0.0, overfoert=0.0, ekstra_bundfradrag=0.0):
    return beregn_skat(pi, 0.25, 0.0, O, kapitalindkomst=ki, overfoert_personfradrag=overfoert,
                       ekstra_ki_bundfradrag=ekstra_bundfradrag)


def test_overfoert_personfradrag_nedsaetter_skatten():
    # (300.000 − 54.100) × 37,01 % = 245.900 × 0,3701 = 91.007,59 − 10.000 = 81.007,59
    assert skat(300_000, overfoert=10_000).total == pytest.approx(81_007.59, abs=0.01)


def test_overfoert_personfradrag_kan_ikke_give_negativ_skat():
    assert skat(20_000, overfoert=5_000).total == 0


def test_eget_uudnyttede_personfradrag():
    # (54.100 − 20.000) × 37,01 % = 12.620,41
    assert skat(20_000).uudnyttet_personfradrag == pytest.approx(12_620.41, abs=0.01)
    assert skat(300_000).uudnyttet_personfradrag == 0


def test_uudnyttet_personfradrag_regner_kapitalindkomst_med():
    # PI 20.000 + KI 30.000 = 50.000 < 54.100 → (4.100) × 37,01 % = 1.517,41
    assert skat(20_000, ki=30_000).uudnyttet_personfradrag == pytest.approx(1_517.41, abs=0.01)


def test_ekstra_bundfradrag_for_kapitalindkomst():
    """PI 700.000, KI 100.000: med ægtefællens uudnyttede 55.000 er bundfradraget 110.000, så ingen
    kapitalindkomst i mellemskattegrundlaget. Total: 745.900 × 37,01 % + 58.800 × 7,5 % =
    276.057,59 + 4.410 = 280.467,59; merskat af KI = 100.000 × 37,01 % = 37.010."""
    s = skat(700_000, ki=100_000, ekstra_bundfradrag=55_000)
    assert s.total == pytest.approx(280_467.59, abs=0.01)
    assert s.skat_kapitalindkomst == pytest.approx(37_010.0, abs=0.01)


def test_uden_overfoersel_uaendret():
    assert skat(300_000).total == pytest.approx((300_000 - 54_100) * FLAD, abs=0.01)
