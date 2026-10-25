"""Feature 009 T002 — skat af positiv nettokapitalindkomst (PSL §§ 6, 7, stk. 1, 10 og 19, stk. 2).

Golden cases regnet i hånden med 2026-satserne:
  bundskat 12,01 %, kommuneskat 25 % (testens valg), kirkeskat 0
  personfradrag 54.100 kr. (af personlig indkomst + kapitalindkomst)
  mellemskat 7,5 % over 641.200 kr.; kapitalindkomst tæller kun over bundfradraget 55.000 kr.
  skatteloft for kapitalindkomst 42 % (bund + kommune + trin; kirkeskat indgår ikke)
"""
import pytest

from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.skat import beregn_skat

O = Regelopslag(2026, 2026, 0.0)
KOMMUNE = 0.25
FLAD = 0.1201 + KOMMUNE  # 0,3701


def skat(pi, ki=0.0, kirke=0.0):
    return beregn_skat(pi, KOMMUNE, kirke, O, kapitalindkomst=ki)


def test_uden_kapitalindkomst_uaendret():
    assert skat(300_000).total == pytest.approx((300_000 - 54_100) * FLAD)


def test_kapitalindkomst_under_bundfradraget_kun_flad_skat():
    # (330.000 − 54.100) × 37,01 % = 275.900 × 0,3701 = 102.110,59; merskatten af 30.000 kr. = 11.103 kr.
    s = skat(300_000, 30_000)
    assert s.total == pytest.approx(102_110.59, abs=0.01)
    assert s.skat_kapitalindkomst == pytest.approx(11_103.0, abs=0.01)


def test_kapitalindkomst_over_bundfradraget_men_under_mellemskattegraensen():
    # Grundlag for mellemskat: 300.000 + (100.000 − 55.000) = 345.000 < 641.200 → kun flad skat.
    s = skat(300_000, 100_000)
    assert s.total == pytest.approx((400_000 - 54_100) * FLAD, abs=0.01)
    assert s.skat_kapitalindkomst == pytest.approx(100_000 * FLAD, abs=0.01)


def test_skatteloft_for_kapitalindkomst():
    """PI 700.000, KI 100.000. Mellemskattegrundlag 745.000:
    - PI-delen af båndet: 641.200–700.000 = 58.800 × 7,5 % = 4.410 (loft 44,57 % ikke ramt: 44,51 %)
    - KI-delen: 700.000–745.000 = 45.000 × 7,5 % = 3.375, nedslag 45.000 × (44,51 % − 42 %) = 1.129,50
    Flad: (800.000 − 54.100) × 37,01 % = 276.057,59 → i alt 282.713,09.
    Uden KI: 645.900 × 37,01 % + 4.410 = 243.457,59 → merskat 39.255,50."""
    s = skat(700_000, 100_000)
    assert s.total == pytest.approx(282_713.09, abs=0.01)
    assert s.skat_kapitalindkomst == pytest.approx(39_255.50, abs=0.01)


def test_kirkeskat_af_kapitalindkomst_uden_for_loftet():
    s = skat(300_000, 30_000, kirke=0.007)
    assert s.skat_kapitalindkomst == pytest.approx(30_000 * (FLAD + 0.007), abs=0.01)


def test_personfradrag_udnyttes_af_kapitalindkomst():
    # Ingen personlig indkomst: 60.000 kr. kapitalindkomst → (60.000 − 54.100) × 37,01 %.
    s = skat(0, 60_000)
    assert s.total == pytest.approx(5_900 * FLAD, abs=0.01)


def test_negativ_kapitalindkomst_ignoreres():
    assert skat(300_000, -20_000).total == pytest.approx(skat(300_000).total)
