"""T001 — grænser til tidslinjens skydere kommer fra kernen og registret (FR-006, Princip II)."""
from datetime import date

from pensionskerne import Ordning
from pensionsoverblik.visning import graenser
from tests.conftest import enlig_profil


def test_tidligste_alder_pr_ordning():
    profil = enlig_profil(ordninger=(
        Ordning("a", "ratepension", 1, 65, oprettet=date(2010, 1, 1)),     # fp 68 − 5
        Ordning("b", "livsvarig", 1, 67, oprettet=date(2020, 1, 1)),      # fp 68 − 3
        Ordning("c", "kapitalpension", 1, 65, oprettet=None, tidligste_udbetalingsalder=60),
    ))
    g = graenser(profil, 2026)
    assert g["ordninger"] == {
        "a": {"tidligste": 63, "oplyst": False},
        "b": {"tidligste": 65, "oplyst": False},
        "c": {"tidligste": 60, "oplyst": True},
    }
    assert g["ratepension_aar"] == {"min": 10, "maks": 30}
    assert g["opsaettelse_maks"] == 10
    assert g["folkepensionsalder"] == 68

