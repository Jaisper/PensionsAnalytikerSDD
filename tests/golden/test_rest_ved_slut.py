"""Feature 040 T001 — penge tilbage ved planens slutning (015 US2): udjævningen ender med bufferen på X i
stedet for 0. Håndregnede cases med rente 0 og inflation 0, så niveauet er (det, der er kommet ind − X) /
antal år til og med det bindende år."""
from dataclasses import replace

import pytest

from pensionskerne import Antagelser, UgyldigtInput, beregn
from pensionskerne.jaevn import beregn_jaevn
from tests.conftest import BEREGNINGSDATO
from tests.golden.test_jaevn_uden_laan import raekker
from tests.golden.test_levetid import ANT, PROFIL, fast


def niveauer(netto, rest, engangs=None):
    j = beregn_jaevn(raekker(netto), engangs or {}, 0.0, 0.0, 2030, rest_slut=rest)
    return [round(a.jaevn, 6) for a in j.aar], [round(a.buffer_rest, 6) for a in j.aar]


def test_uden_rest_er_alt_uaendret():
    assert niveauer([300, 0, 0], 0.0) == ([100, 100, 100], [200, 100, 0])


def test_resten_trækkes_fra_foer_fordelingen():
    # min(300/1, 300/2, (300 − 60)/3) = 80 → 80 hvert år; bufferen 220, 140, 60.
    assert niveauer([300, 0, 0], 60.0) == ([80, 80, 80], [220, 140, 60])


def test_resten_binder_kun_det_sidste_segment():
    # [100, 0, 300, 0] med 100: fra år 0: min(100, 50, 133,3, (400 − 100)/4 = 75) = 50 ved k=1.
    # Fra år 2: min(300, (300 − 100)/2) = 100 → 100, 100; bufferen 200, 100.
    assert niveauer([100, 0, 300, 0], 100.0) == ([50, 50, 100, 100], [50, 0, 200, 100])


def test_for_stor_rest_giver_ingen_udbetaling_fra_bufferen():
    # Der er kun 100 i alt; 200 kan ikke nås. Intet bruges, og alt står tilbage.
    assert niveauer([100, 0], 200.0) == ([0, 0], [100, 100])


def plan(rest, slut=None):
    return beregn(PROFIL, replace(ANT, rest_ved_plan_slut=rest, plan_slut_alder=slut), 2026, BEREGNINGSDATO)


def rest_real(res):
    f = res.formue[-1]
    return f.i_plan * f.realfaktor


def test_bufferen_ender_paa_beloebet_i_dagens_kroner():
    uden, med = plan(0.0), plan(250_000)
    assert rest_real(uden) == pytest.approx(0.0, abs=1)
    assert rest_real(med) == pytest.approx(250_000, abs=1)
    assert fast(med) < fast(uden)
    # Ingen lån og aldrig faldende (010).
    assert all(j.buffer_rest >= -1e-6 for j in med.jaevn.aar)
    real = [j.jaevn * a.realfaktor for j, a in zip(med.jaevn.aar, med.aar) if a.alder >= med.jaevn_fra_alder]
    assert all(b >= a - 1 for a, b in zip(real, real[1:]))


def test_med_planens_slutning():
    med = plan(100_000, slut=95)
    assert med.aar[-1].alder == 95 and rest_real(med) == pytest.approx(100_000, abs=1)


def test_resten_er_en_markeret_antagelse():
    res = plan(250_000)
    assert "antagelse.rest_ved_plan_slut" in res.sporing_samlet
    assert any(a.kode == "REST_VED_PLAN_SLUT" for a in res.advarsler)
    assert not any(a.kode == "REST_VED_PLAN_SLUT" for a in plan(0.0).advarsler)


def test_for_stort_beloeb_giver_advarsel():
    res = plan(50_000_000)
    assert any(a.kode == "REST_IKKE_MULIG" for a in res.advarsler)
    assert fast(res) >= 0


def test_negativt_beloeb_er_ugyldigt():
    with pytest.raises(UgyldigtInput) as e:
        plan(-1)
    assert e.value.felt == "antagelser.rest_ved_plan_slut"


@pytest.mark.parametrize("slut", [69, 111])
def test_planens_slutning_skal_vaere_rimelig(slut):
    with pytest.raises(UgyldigtInput) as e:
        plan(0.0, slut=slut)
    assert e.value.felt == "antagelser.plan_slut_alder"


def test_standard_er_nul():
    assert Antagelser().rest_ved_plan_slut == 0.0
