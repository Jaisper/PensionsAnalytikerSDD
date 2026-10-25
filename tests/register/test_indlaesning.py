"""T005 — registret: struktur, status og satsår (FR-010, FR-011)."""
import pytest

from pensionskerne import UgyldigtInput, register
from pensionskerne.register import ENHEDER, STATUSSER


def test_satsaar_2026_findes():
    assert 2026 in register.satsaar()


def test_alle_poster_har_kilde_status_og_enhed():
    for p in register.poster(2026):
        assert p.kilde.strip(), p.id
        assert p.status in STATUSSER, p.id
        assert p.enhed in ENHEDER, p.id


def test_kun_beloeb_reguleres():
    for p in register.poster(2026):
        if p.reguleres:
            assert p.enhed == "kr_aar", p.id


def test_98_kommuner_plus_aliaser():
    reg = register.kommuneregister(2026)
    assert len(reg.satser) == 98
    assert register.kommune_noegle(2026, "Århus") == "aarhus"
    assert register.kommune_noegle(2026, "Lyngby-Taarbæk") == "lyngbytaarbaek"
    assert register.kommune_noegle(2026, "Atlantis") is None
    assert all(0.2 < v < 0.3 for v in reg.satser.values())


def test_ukendt_satsaar_afvises_uden_fallback():
    with pytest.raises(UgyldigtInput) as e:
        register.post(1999, "skat.bundskat")
    assert e.value.felt == "satsaar"
