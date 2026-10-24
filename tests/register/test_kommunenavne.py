"""Officielle kommunenavne til brugerfladen (feature 002, T002)."""
from pensionskerne import register


def test_alle_98_kommuner_har_et_navn():
    navne = register.kommunenavne(2026)
    assert len(navne) == 98
    assert navne["kobenhavn"] == "København"
    assert navne["lyngbytaarbaek"] == "Lyngby-Taarbæk"
    assert set(navne) == set(register.kommuneregister(2026).satser)
