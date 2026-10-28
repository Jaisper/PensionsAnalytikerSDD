"""Feature 007b T001 — den bedste plan begynder tidligst ved pensionsalderen (stopalderen, ellers
folkepensionsalderen). Borgeren er født 1. maj 1963: 63 år i 2026 og folkepensionsalder 68."""
from dataclasses import replace
from datetime import date

from pensionskerne import Antagelser, Loen, Ordning
from pensionskerne.optimering import optimer, pensionsalder, soegerum
from tests.conftest import BEREGNINGSDATO, enlig_profil

A = Antagelser(afkast_efter_pal=0.03, inflation=0.02)
RATE = Ordning("rate", "ratepension", 900_000, 64, oprettet=date(2010, 1, 1), udbetaling_aar=10)
LIV = Ordning("liv", "livsvarig", 1_200_000, 64, oprettet=date(2010, 1, 1))


def starter(dimensioner, oid):
    return [d[2] for dim in dimensioner for d in dim if d[0] == "start" and d[1] == oid]


def test_pensionsalderen_er_stopalderen_ellers_folkepensionsalderen():
    assert pensionsalder(enlig_profil(), 68) == 68
    assert pensionsalder(enlig_profil(loen=Loen(480_000)), 68) == 68
    assert pensionsalder(enlig_profil(loen=Loen(480_000, stop_alder=65)), 68) == 65


def test_uden_stopalder_starter_ingen_ordning_foer_folkepensionen():
    _, dim = soegerum(enlig_profil(ordninger=(RATE, LIV)), A, 2026, BEREGNINGSDATO)
    assert min(starter(dim, "rate")) == 68 and min(starter(dim, "liv")) == 68


def test_med_stopalder_starter_ingen_ordning_foer_stop():
    p = enlig_profil(ordninger=(RATE,), loen=Loen(480_000, stop_alder=65))
    _, dim = soegerum(p, A, 2026, BEREGNINGSDATO)
    assert min(starter(dim, "rate")) == 65


def test_en_ordning_der_allerede_udbetaler_flyttes_ikke():
    loebende = replace(RATE, udbetaling_start_alder=60)
    _, dim = soegerum(enlig_profil(ordninger=(loebende, LIV)), A, 2026, BEREGNINGSDATO)
    assert starter(dim, "rate") == [60]


def test_den_bedste_plan_maales_fra_pensionsalderen():
    r = optimer(enlig_profil(ordninger=(RATE, LIV)), A, 2026, BEREGNINGSDATO, maks_evalueringer=300)
    assert r.bedste is not None
    assert min(r.bedste.starter.values()) >= 68
    assert r.bedste_maaned > r.udgangspunkt_maaned
