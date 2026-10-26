"""Feature 019 T001 — planhorisonten er adskilt fra livrentens beregningshorisont (FR-001, SC-001, SC-002)."""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Ordning, Pensionsprofil, UgyldigtInput, beregn
from tests.conftest import BEREGNINGSDATO

ANT = Antagelser(afkast_efter_pal=0.04, inflation=0.02)
PROFIL = Pensionsprofil(
    foedselsdato=date(1960, 3, 1), civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
    ordninger=(Ordning("liv", "livsvarig", 800_000, 67, oprettet=date(2010, 1, 1)),
               Ordning("rate", "ratepension", 900_000, 67, oprettet=date(2010, 1, 1), udbetaling_aar=10)),
    opsparing=(Aktiv("bank", 300_000),),
)


def plan(slut):
    return beregn(PROFIL, replace(ANT, plan_slut_alder=slut), 2026, BEREGNINGSDATO)


def livrente(res):
    return {next(k.brutto for k in a.kilder if k.kilde_id == "liv") for a in res.aar if any(k.kilde_id == "liv" for k in a.kilder)}


def fast(res):
    return min(j.jaevn * a.realfaktor for j, a in zip(res.jaevn.aar, res.aar))


def test_uden_planhorisont_er_alt_uaendret():
    uden = beregn(PROFIL, ANT, 2026, BEREGNINGSDATO)
    med = plan(90)
    assert [a.netto_i_alt for a in med.aar] == [a.netto_i_alt for a in uden.aar]
    assert [j.jaevn for j in med.jaevn.aar] == [j.jaevn for j in uden.jaevn.aar]


def test_planens_slutning_styrer_tabellen():
    assert plan(85).aar[-1].alder == 85 and plan(95).aar[-1].alder == 95


def test_livrenten_er_den_samme_uanset_planen():
    assert livrente(plan(85)) == livrente(plan(90)) == livrente(plan(95))
    assert len(livrente(plan(95))) == 1


def test_det_faste_beloeb_falder_med_planens_laengde():
    assert fast(plan(85)) > fast(plan(90)) > fast(plan(95))


def test_en_ratepension_forlaenger_en_kort_plan():
    # Ratepensionen udbetales 67–76; en plan til 70 år forlænges til sidste rate.
    assert plan(70).aar[-1].alder == 76


def test_planen_skal_slutte_efter_i_dag():
    with pytest.raises(UgyldigtInput) as e:
        plan(66)
    assert e.value.felt == "antagelser.plan_slut_alder"
