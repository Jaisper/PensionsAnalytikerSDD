"""Feature 034 — forsikringerne fra rapporten efter skat (FR-001, FR-002).

Skattekoderne fra PensionsInfo: A (afgiftspligtig, 40 % ved død, PBL § 25, stk. 1, nr. 1 og 6, og
§ 29), F (skatte- og afgiftsfri) og S (skattepligtig som personlig indkomst). Skattepligtigt til
efterladte regnes ikke, fordi deres indkomst er ukendt. Tab af arbejdsevne regnes med borgerens egen
skat, som om dækningen er årets eneste personlige indkomst (den erstatter lønnen).
"""
from datetime import date

import pytest

from pensionskerne.forsikring import efter_skat
from pensionskerne.regler.skat import beregn_skat
from pensionskerne.register.opslag import Regelopslag

DATO = date(2026, 11, 2)


def regn(type_, skat, form, beloeb, kommune="aarhus", kirke=True):
    return efter_skat(type_, skat, form, beloeb, kommune, kirke, 2026, DATO)


def test_afgiftspligtig_ved_doed_giver_60_procent():
    r = regn("doed", "A", "engang", 1_000_000)
    assert r.netto == pytest.approx(600_000)
    assert r.beskatning == "afgift"


def test_skattefri_er_uaendret():
    r = regn("kritisk_sygdom", "F", "engang", 210_000)
    assert r.netto == 210_000 and r.beskatning == "skattefri"


def test_skattepligtig_til_efterladte_regnes_ikke():
    r = regn("doed", "S", "engang", 1_683_000)
    assert r.netto is None and r.beskatning == "modtager"


def test_ukendt_skattekode_eller_beloeb():
    assert regn("doed", None, "engang", 500_000).beskatning == "ukendt"
    assert regn("doed", "A", "engang", None).netto is None


def test_tab_af_arbejdsevne_med_borgerens_egen_skat():
    o = Regelopslag(2026, 2026, 0.0)
    forventet = 300_000 - beregn_skat(300_000, o.kommuneskat("aarhus"), o.kirkeskat("aarhus"), o).total
    r = regn("erhvervsevne", "S", "aarraekke", 300_000)
    assert r.beskatning == "indkomst"
    assert r.netto == pytest.approx(forventet)
    assert 0 < r.netto < 300_000


def test_kirkeskat_kun_for_medlemmer():
    med = regn("erhvervsevne", "S", "aarraekke", 300_000, kirke=True).netto
    uden = regn("erhvervsevne", "S", "aarraekke", 300_000, kirke=False).netto
    assert uden > med
