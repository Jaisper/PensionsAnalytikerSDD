"""Kontrakt K1–K7 (contracts/kerne-api.md) og register-API (T035, T036, T039, T051)."""
import datetime as dt
from datetime import date

import pytest

import pensionskerne
from pensionskerne import Antagelser, Ordning, UverificeretRegel, beregn, register
from tests.conftest import BEREGNINGSDATO, enlig_profil


def _profil():
    return enlig_profil(ordninger=(
        Ordning("rate", "ratepension", 900_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=12,
                aarlig_indbetaling=40_000),
        Ordning("liv", "livsvarig", 1_500_000, 68, oprettet=date(2019, 1, 1), aarlig_indbetaling=30_000),
        Ordning("ald", "aldersopsparing", 300_000, 66, oprettet=date(2015, 1, 1), aarlig_indbetaling=9_900),
    ), kirkeskat=0.0072, anden_kapitalindkomst=10_000)


def test_k2_determinisme():
    a = beregn(_profil(), Antagelser(), 2026, BEREGNINGSDATO)
    assert a == beregn(_profil(), Antagelser(), 2026, BEREGNINGSDATO)


def test_k1_laeser_ikke_dags_dato(monkeypatch):
    class Faelde(dt.date):
        @classmethod
        def today(cls):
            raise AssertionError("date.today() må ikke kaldes")
    monkeypatch.setattr(dt, "date", Faelde)
    beregn(_profil(), Antagelser(), 2026, BEREGNINGSDATO)


def test_k5_k7_summer_og_graenser():
    for a in beregn(_profil(), Antagelser(), 2026, BEREGNINGSDATO).aar:
        assert sum(k.skat for k in a.kilder) == pytest.approx(a.skat_i_alt, abs=0.01)
        assert sum(k.netto for k in a.kilder) == pytest.approx(a.netto_i_alt, abs=0.01)
        assert a.skat_i_alt <= a.personlig_indkomst + 0.01
        assert all(k.netto >= -0.01 for k in a.kilder)


def test_k6_sporing_ikke_tom_og_gyldig():
    gyldige = {p.id for p in register.poster(2026)}
    res = beregn(_profil(), Antagelser(), 2026, BEREGNINGSDATO)
    for a in res.aar:
        assert a.sporing
        for id in a.sporing:
            assert id in gyldige or id.startswith(("antagelse.", "kommune.")), id
    assert set().union(*(a.sporing for a in res.aar)) <= set(res.sporing_samlet)


def test_k4_streng_tilstand_afviser():
    # Kommuneskatten har status 'sekundaer', indtil T-REG har krydstjekket regnearket.
    with pytest.raises(UverificeretRegel):
        beregn(_profil(), Antagelser(), 2026, BEREGNINGSDATO, streng=True)


def test_register_api():
    assert register.satsaar() == [2026]
    assert register.post(2026, "skat.bundskat").vaerdi == 0.1201
    assert len(register.kommuner(2026)) == 100  # 98 + 2 aliaser
    assert pensionskerne.beregn is beregn


def test_quickstart_eksempel():
    from pensionskerne import Pensionsprofil
    profil = Pensionsprofil(
        foedselsdato=date(1963, 5, 1), civilstand="enlig", kommune="aarhus", kirkeskat=None,
        likvid_formue=50_000,
        ordninger=[Ordning(id="rate1", type="ratepension", oprettet=date(2010, 1, 1), saldo=1_000_000,
                           aarlig_indbetaling=0, udbetaling_start_alder=65, udbetaling_aar=10)],
    )
    res = beregn(profil, Antagelser(afkast_efter_pal=0.0, inflation=0.0), satsaar=2026,
                 beregningsdato=date(2026, 10, 24))
    aar65 = next(a for a in res.aar if a.alder == 65)
    assert aar65.kilder[0].brutto == 100_000
    assert res.folkepensionsalder == 68
