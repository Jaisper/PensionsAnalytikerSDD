"""T001 — grænser til tidslinjens skydere kommer fra kernen og registret (FR-006, Princip II)."""
from datetime import date

from pensionskerne import Loen, Ordning
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
        "c": {"tidligste": 60, "oplyst": True, "seneste": 80, "kan_omlaegges": True},  # 009: kapitalpension
    }
    assert g["ratepension_aar"] == {"min": 10, "maks": 30}
    assert g["opsaettelse_maks"] == 10
    assert g["folkepensionsalder"] == 68



def test_stopalder_fra_tidligste_udbetaling_til_folkepensionsalderen():
    # Feature 025: punktet for stopalderen i tidslinjen.
    profil = enlig_profil(ordninger=(
        Ordning("a", "ratepension", 1, 65, oprettet=date(2010, 1, 1)),     # 63
        Ordning("b", "livsvarig", 1, 67, oprettet=date(2020, 1, 1)),      # 65
    ))
    assert graenser(profil, 2026)["stopalder"] == {"min": 63, "maks": 68, "aktuel": 65}  # 030: + aktuel


def test_stopalder_uden_ordninger_og_over_folkepensionsalderen():
    # Uden ordninger: lovens alder for en ordning uden oprettelsesdato (fp 68 − 3).
    # En stopalder uden for grænserne fra guiden bliver selv grænsen.
    profil = enlig_profil(ordninger=(), loen=Loen(480_000, stop_alder=70))
    assert graenser(profil, 2026)["stopalder"] == {"min": 65, "maks": 70, "aktuel": 70}
    profil = enlig_profil(ordninger=(), loen=Loen(480_000, stop_alder=62))
    assert graenser(profil, 2026)["stopalder"] == {"min": 62, "maks": 68, "aktuel": 62}


def test_stopalderen_der_gaelder_nu_er_udledt_uden_valg():
    # Feature 030: uden valgt stopalder står punktet ved den første udbetaling (højst folkepensionsalderen).
    ordninger = (Ordning("a", "ratepension", 1, 65, oprettet=date(2010, 1, 1)),
                 Ordning("b", "livsvarig", 1, 67, oprettet=date(2020, 1, 1)))
    assert graenser(enlig_profil(ordninger=ordninger, loen=Loen(480_000)), 2026)["stopalder"]["aktuel"] == 65
    assert graenser(enlig_profil(ordninger=ordninger, loen=Loen(480_000, stop_alder=66)), 2026)["stopalder"]["aktuel"] == 66
    assert graenser(enlig_profil(ordninger=(), loen=Loen(480_000)), 2026)["stopalder"]["aktuel"] == 68
