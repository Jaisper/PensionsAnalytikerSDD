"""Feature 035 T004 — μ og σ for en portefølje ud fra Rådets forudsætninger (henstillingen pkt. 7.2 og
appendix 1). Facit er håndregnet fra registrets tal (Rådet, 1. halvår 2027):

- μ = ln(1 + Σ wᵢ·(afkastᵢ − investeringsomkostningᵢ)) og σ = √(wᵀSw), hvor S_ij = ρ_ij·σᵢ·σⱼ.
- År 1–5 og 6–10 har hver sit afkast; investeringsomkostningerne for år 1–10 gælder i alle ti år.
- Fra år 11 gælder Rådets tre aktivklasser.
"""
import math

import pytest

from pensionskerne.prognose import forudsaetninger, mu_sigma
from pensionskerne.register.opslag import Regelopslag

OBL, AKT = "Stats- og realkreditobligationer", "Globale aktier (developed markets)"


def ms(aar, vaegte):
    return mu_sigma(vaegte, forudsaetninger(Regelopslag(2026, 2026, 0.0), aar))


@pytest.mark.parametrize("aar", [1, 5])
def test_aar_1_5_kun_obligationer(aar):
    mu, sigma = ms(aar, {OBL: 1.0})
    assert mu == pytest.approx(math.log(1 + 0.034 - 0.0022))
    assert sigma == pytest.approx(0.043)


@pytest.mark.parametrize("aar", [6, 10])
def test_aar_6_10_halvt_og_halvt(aar):
    mu, sigma = ms(aar, {OBL: 0.5, AKT: 0.5})
    assert mu == pytest.approx(math.log(1 + 0.5 * (0.036 - 0.0022) + 0.5 * (0.077 - 0.0045)))
    assert sigma == pytest.approx(math.sqrt(0.25 * 0.043**2 + 0.25 * 0.165**2 + 2 * 0.25 * 0.1 * 0.043 * 0.165))


@pytest.mark.parametrize("aar", [11, 40])
def test_fra_aar_11_tre_aktivklasser(aar):
    # 60 % globale aktier → "Aktier", 40 % obligationer → "Obligationer"; korrelationen er 0.
    mu, sigma = ms(aar, {OBL: 0.4, AKT: 0.6})
    assert mu == pytest.approx(math.log(1 + 0.6 * (0.065 - 0.0045) + 0.4 * (0.035 - 0.0022)))
    assert sigma == pytest.approx(math.sqrt(0.36 * 0.18**2 + 0.16 * 0.08**2))


def test_illikvide_samles_i_en_klasse_fra_aar_11():
    mu, sigma = ms(11, {"Ejendomme": 0.5, "Infrastruktur": 0.5})
    assert mu == pytest.approx(math.log(1 + 0.065 - 0.0022))
    assert sigma == pytest.approx(0.12)


def test_ukendt_aktivklasse_afvises():
    with pytest.raises(KeyError):
        ms(1, {"Kryptovaluta": 1.0})


def test_opslagene_spores():
    o = Regelopslag(2026, 2026, 0.0)
    mu_sigma({OBL: 1.0}, forudsaetninger(o, 12))
    assert {"raadet.lang.afkast", "raadet.lang.tilknytning"} <= set(o.brugt)


def test_inflation_pr_aar():
    o = Regelopslag(2026, 2026, 0.0)
    assert forudsaetninger(o, 3).inflation == 0.018
    assert forudsaetninger(o, 10).inflation == 0.018
    assert forudsaetninger(o, 11).inflation == 0.02
