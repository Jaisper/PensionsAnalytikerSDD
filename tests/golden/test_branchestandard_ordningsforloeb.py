"""Feature 035 T005 — afkast og gebyr pr. ordning (trin 3 i branchestandarden).

`Ordning.afkast_forloeb` er afkast efter PAL-skat og investeringsomkostninger pr. kalenderår. Det
overstyrer `Antagelser` for den ordning; mangler et år, bruges det fælles afkast.
`Ordning.gebyr_pr_aar` er en fast administrationsomkostning i dagens kroner, der trækkes i depotet
hvert år i opsparingen og reguleres med satsreguleringen (henstillingen pkt. 7.2: omkostninger
uændrede i nutidskroner). Håndregnede facit.
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, Pensionsprofil, beregn
from tests.conftest import BEREGNINGSDATO

A = Antagelser(afkast_efter_pal=0.03, inflation=0.0)


def person(*ordninger, foedt=date(1958, 3, 1)):
    return Pensionsprofil(foedselsdato=foedt, civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=ordninger)


def rate(id_="rate", start=68, saldo=1_000_000, **kw):
    return Ordning(id_, "ratepension", saldo, start, oprettet=date(2010, 1, 1), udbetaling_aar=10, **kw)


def regn(profil, antagelser=A):
    return beregn(profil, antagelser, 2026, BEREGNINGSDATO)


def brutto(res, alder, id_=None, type_="ratepension"):
    return sum(k.brutto for k in res.aar_ved(alder).kilder if k.type == type_ and (id_ is None or k.kilde_id == id_))


def test_ordningens_forloeb_i_opsparingen():
    """Født 1966, raten begynder som 63: saldoen er 1.000.000 × 0,9 × 1,03²."""
    res = regn(person(rate(start=63, afkast_forloeb={2026: -0.10}), foedt=date(1966, 3, 1)))
    assert brutto(res, 63) == pytest.approx(1_000_000 * 0.9 * 1.03 ** 2 / 10)


def test_ordningens_forloeb_i_rateplanen():
    res = regn(person(rate(afkast_forloeb={2026: -0.10})))
    assert [brutto(res, a) for a in (68, 69, 70)] == pytest.approx([100_000, 90_000, 92_700])


def test_kun_ordningen_med_forloeb_paavirkes():
    res = regn(person(rate("a", start=63, afkast_forloeb={2026: -0.10}), rate("b", start=63), foedt=date(1966, 3, 1)))
    assert brutto(res, 63, "a") == pytest.approx(1_000_000 * 0.9 * 1.03 ** 2 / 10)
    assert brutto(res, 63, "b") == pytest.approx(1_000_000 * 1.03 ** 3 / 10)


def test_samme_afkast_som_forloeb_er_uaendret():
    p = person(rate(start=63), Ordning("liv", "livsvarig", 500_000, 67), foedt=date(1966, 3, 1))
    alle = {aar: 0.03 for aar in range(2026, 2080)}
    med = person(*(replace(o, afkast_forloeb=alle) for o in p.ordninger), foedt=date(1966, 3, 1))
    assert [a.netto_i_alt for a in regn(med).aar] == pytest.approx([a.netto_i_alt for a in regn(p).aar])


def test_livsvarig_ydelse_foelger_ordningens_forloeb():
    """Livrentens ydelse regnes med ordningens gennemsnitlige afkast over horisonten. Et konstant
    forløb på 5 % giver det samme som et fælles afkast på 5 %."""
    liv = Ordning("liv", "livsvarig", 500_000, 68)
    fem = {aar: 0.05 for aar in range(2026, 2080)}
    med = regn(person(replace(liv, afkast_forloeb=fem)))
    fælles = regn(person(liv), Antagelser(afkast_efter_pal=0.05, inflation=0.0))
    assert brutto(med, 70, type_="livsvarig") == pytest.approx(brutto(fælles, 70, type_="livsvarig"))
    assert brutto(med, 70, type_="livsvarig") > brutto(regn(person(liv)), 70, type_="livsvarig")


def test_gebyr_traekkes_i_opsparingen():
    """Afkast 0, ingen inflation: tre år (2026–2028) à 1.000 kr. før raten begynder som 63."""
    res = regn(person(rate(start=63, saldo=100_000, gebyr_pr_aar=1_000), foedt=date(1966, 3, 1)),
               Antagelser(afkast_efter_pal=0.0, inflation=0.0))
    assert brutto(res, 63) == pytest.approx(97_000 / 10)


def test_gebyret_er_uaendret_i_nutidskroner():
    """Med 2 % satsregulering: 1.000 + 1.020 + 1.040,40 kr."""
    res = regn(person(rate(start=63, saldo=100_000, gebyr_pr_aar=1_000), foedt=date(1966, 3, 1)),
               Antagelser(afkast_efter_pal=0.0, inflation=0.02))
    assert brutto(res, 63) == pytest.approx((100_000 - 1_000 - 1_020 - 1_040.4) / 10)


def test_gebyret_kan_ikke_goere_depotet_negativt():
    res = regn(person(rate(start=63, saldo=1_000, gebyr_pr_aar=1_000), foedt=date(1966, 3, 1)),
               Antagelser(afkast_efter_pal=0.0, inflation=0.0))
    assert brutto(res, 63) == 0
