"""Feature 035 T001 — Rådet for Afkastforventningers forudsætninger i registret (FR-003).

Kilde: afkastforventninger.dk, "afkastforventninger-1-halvar-2027.xlsx" (offentliggjort 2.11.2026).
"""
import pytest

from pensionskerne.register import post
from pensionskerne.register.opslag import Regelopslag

KLASSER = 10


def v(id_):
    return post(2026, id_).vaerdi


def test_saettet_har_navn_og_udgivelsesdato():
    saet = v("raadet.saet")
    assert saet["navn"] == "1. halvår 2027" and saet["udgivet"] == "2026-11-02"


@pytest.mark.parametrize("id_", ["raadet.afkast.aar_1_5", "raadet.afkast.aar_6_10", "raadet.afkast.aar_1_10",
                                 "raadet.standardafvigelse", "raadet.investeringsomkostninger.aar_1_10"])
def test_ti_aktivklasser(id_):
    assert len(v(id_)) == len(v("raadet.aktivklasser")) == KLASSER


def test_udvalgte_tal():
    klasser = v("raadet.aktivklasser")
    obl, aktier = klasser.index("Stats- og realkreditobligationer"), klasser.index("Globale aktier (developed markets)")
    assert v("raadet.afkast.aar_1_5")[aktier] == 0.066 and v("raadet.afkast.aar_6_10")[aktier] == 0.077
    assert v("raadet.standardafvigelse")[obl] == 0.043
    assert v("raadet.korrelation")[obl][aktier] == 0.1
    assert v("raadet.investeringsomkostninger.aar_1_10")[aktier] == 0.0045


def test_korrelation_er_symmetrisk_med_ettal_paa_diagonalen():
    for navn, n in (("raadet.korrelation", KLASSER), ("raadet.lang.korrelation", 3)):
        k = v(navn)
        assert len(k) == n and all(len(r) == n for r in k)
        assert all(k[i][i] == 1 for i in range(n))
        assert all(k[i][j] == k[j][i] for i in range(n) for j in range(n))


def test_lang_sigt_tre_aktivklasser():
    assert v("raadet.lang.aktivklasser") == ["Obligationer", "Illikvide aktiver", "Aktier"]
    assert v("raadet.lang.afkast") == [0.035, 0.065, 0.065]
    assert v("raadet.lang.standardafvigelse") == [0.08, 0.12, 0.18]
    assert v("raadet.lang.investeringsomkostninger") == [0.0022, 0.0022, 0.0045]


def test_hver_klasse_hoerer_til_en_langsigtet_klasse():
    tilknytning = v("raadet.lang.tilknytning")
    assert set(tilknytning) == set(v("raadet.aktivklasser"))
    assert set(tilknytning.values()) <= set(v("raadet.lang.aktivklasser"))


def test_inflation_pr_periode():
    assert v("raadet.inflation") == {"aar_1_5": 0.018, "aar_6_10": 0.018, "aar_11": 0.02}


def test_fraktiler_fra_henstillingen():
    assert v("branchestandard.fraktiler") == [0.05, 0.95]


def test_raadets_tal_er_ikke_satsregulerede():
    o = Regelopslag(2026, 2040, 0.02)
    assert o.v("raadet.afkast.aar_1_5") == v("raadet.afkast.aar_1_5")
