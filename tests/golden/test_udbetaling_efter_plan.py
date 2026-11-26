"""Feature 040b — en ratepension, der udbetales efter planens slutning (fejl fundet af produktejeren: "beder om at
pengene skal stoppe ved 80 år, men den regner alligevel til 84"). Tabellen går stadig til sidste rate, men den
øvrige opsparing (og en eventuel rest) er brugt op ved den valgte alder. Årene efter planen er årets egen
indkomst; bufferen røres ikke. Håndregnede cases med rente 0 og inflation 0."""
from dataclasses import replace

import pytest

from pensionskerne import beregn
from pensionskerne.jaevn import beregn_jaevn
from tests.conftest import BEREGNINGSDATO
from tests.golden.test_jaevn_uden_laan import raekker
from tests.golden.test_levetid import ANT, PROFIL


def niveauer(netto, plan_raekker, rest=0.0):
    j = beregn_jaevn(raekker(netto), {}, 0.0, 0.0, 2030, rest_slut=rest, plan_raekker=plan_raekker)
    return [round(a.jaevn, 6) for a in j.aar], [round(a.buffer_rest, 6) for a in j.aar]


def test_udjaevningen_slutter_ved_planens_slutning():
    # Planen er de to første rækker: min(300, 300/2) = 150. Bagefter er det årets egen indkomst.
    assert niveauer([300, 0, 50, 50], 2) == ([150, 150, 50, 50], [150, 0, 0, 0])


def test_resten_staar_ved_planens_slutning_og_roeres_ikke_bagefter():
    # min(300, (300 − 100)/2) = 100 → 100, 100; resten 100 står urørt i årene efter.
    assert niveauer([300, 0, 50, 50], 2, rest=100.0) == ([100, 100, 50, 50], [200, 100, 100, 100])


def test_uden_aar_efter_planen_er_alt_uaendret():
    assert niveauer([300, 0, 0], 3) == niveauer([300, 0, 0], None) == ([100, 100, 100], [200, 100, 0])


def plan(slut, rest=0.0):
    return beregn(PROFIL, replace(ANT, plan_slut_alder=slut, rest_ved_plan_slut=rest), 2026, BEREGNINGSDATO)


def test_ratepensionen_efter_planen():
    # Ratepensionen udbetales 67–76; planen slutter som 70-årig.
    res = plan(70)
    assert res.aar[-1].alder == 76 and res.jaevn_til_alder == 70
    efter = [(j, a) for j, a in zip(res.jaevn.aar, res.aar) if a.alder > 70]
    assert len(efter) == 6
    assert all(j.jaevn == pytest.approx(a.disponibel) for j, a in efter)
    assert all(j.buffer_rest == pytest.approx(0.0, abs=1) for j, _ in efter)
    assert all(j.fra_buffer == pytest.approx(0.0, abs=1) for j, _ in efter)
    a = next(a for a in res.advarsler if a.kode == "UDBETALING_EFTER_PLAN")
    assert a.aldre == (71, 76) and "76" in a.besked and "70" in a.besked


def test_resten_ved_den_valgte_alder():
    res = plan(70, rest=100_000)
    f = next(f for f in res.formue if f.alder == 70)
    assert f.i_plan * f.realfaktor == pytest.approx(100_000, abs=1)
    assert "70-årig" in next(a for a in res.advarsler if a.kode == "REST_VED_PLAN_SLUT").besked


def test_den_korte_plan_bruger_opsparingen_hurtigere():
    # Opsparingen fordeles over 67–70 i stedet for 67–76, så de første år får mere.
    kort, lang = plan(70), plan(76)
    foerste = lambda r: r.jaevn.aar[0].jaevn  # noqa: E731
    assert foerste(kort) > foerste(lang)
    assert not any(a.kode == "UDBETALING_EFTER_PLAN" for a in lang.advarsler)
    assert lang.jaevn_til_alder == 76
