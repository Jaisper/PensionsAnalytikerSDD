"""Feature 007 T001 — find bedste plan (FR-001–FR-006, SC-001).

Optimeringen søger over kernens egne beregninger. Testene sikrer, at forslaget aldrig er
dårligere end udgangspunktet, at hver afprøvet kandidat holder sig inden for lovens og
registrets grænser, og at svaret er deterministisk.
"""
from dataclasses import replace
from datetime import date

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from pensionskerne import Antagelser, Ordning, beregn
from pensionskerne import optimering as opt
from pensionskerne.optimering import Plan, anvend, fast_niveau, optimer, slutniveau, vindue
from pensionsoverblik.visning import byg_visning, graenser
from tests.conftest import BEREGNINGSDATO, enlig_profil

A = Antagelser(afkast_efter_pal=0.03, inflation=0.02)

FIRE = (
    Ordning("rate", "ratepension", 900_000, 67, oprettet=date(2010, 1, 1), udbetaling_aar=10),
    Ordning("liv", "livsvarig", 1_200_000, 67, oprettet=date(2010, 1, 1)),
    Ordning("ald", "aldersopsparing", 150_000, 67, oprettet=date(2010, 1, 1)),
    Ordning("kap", "kapitalpension", 400_000, 66, oprettet=date(2000, 1, 1)),
)


def profil(*ordninger, **kw):
    return enlig_profil(ordninger=ordninger or FIRE, **kw)


def resultat(p, a=A):
    return beregn(p, a, 2026, BEREGNINGSDATO)


# ── Mål ─────────────────────────────────────────────────────────────────────────────────────────

def test_maalet_er_visningens_hovedtal():
    """Feature 008: hovedtallet er det faste beløb hele perioden — samme tal som målet."""
    for p in (profil(), profil(FIRE[0]), profil(FIRE[1], FIRE[3])):
        res = resultat(p)
        assert round(fast_niveau(res, vindue(res)), -2) == byg_visning(res)["hovedtal"]["maaned"]


def test_slutniveau_er_visningens_senere_niveau():
    res = resultat(profil(FIRE[0], FIRE[2]))
    h = byg_visning(res)["hovedtal"]
    assert round(slutniveau(res), -2) == (h["senere"] or h)["maaned"]


# ── Forslaget ───────────────────────────────────────────────────────────────────────────────────

def test_forslag_er_mindst_lige_saa_godt_og_kan_anvendes():
    p = profil()
    r = optimer(p, A, 2026, BEREGNINGSDATO, maks_evalueringer=400)
    v = vindue(resultat(p))
    assert r.udgangspunkt_maaned == pytest.approx(fast_niveau(resultat(p), v))
    if r.bedste is not None:
        assert r.bedste_maaned > r.udgangspunkt_maaned
        p2, a2 = anvend(p, A, r.bedste)
        assert fast_niveau(resultat(p2, a2), v) == pytest.approx(r.bedste_maaned)


def test_skubber_ikke_engangsbeloeb_sent_for_at_hoeje_hovedtallet():
    """T003: at flytte et engangsbeløb sent hæver hovedtallet, men sænker de første år."""
    p = profil()
    r = optimer(p, A, 2026, BEREGNINGSDATO)
    if r.bedste is not None:
        p2, a2 = anvend(p, A, r.bedste)
        res = resultat(p2, a2)
        assert fast_niveau(res, vindue(resultat(p))) >= fast_niveau(resultat(p), vindue(resultat(p)))
        assert r.bedste.starter.get("ald", 0) <= r.udgangspunkt.starter["ald"] + 2


def test_finder_en_forbedring_for_en_daarlig_plan():
    """Alt skubbet sent: tidlige år uden udbetaling. Under 009's realistiske buffer er det tydeligt
    dårligt (≈ 2.000 kr./md.). (Den tidligere profil — én sen ratepension — er efter 009 kun ca.
    70 kr./md. fra det bedste, fordi opsparing i bufferen nu koster skat og pensionstillæg.)"""
    p = profil(replace(FIRE[0], udbetaling_start_alder=77, udbetaling_aar=10), replace(FIRE[1], udbetaling_start_alder=75),
               FIRE[2], replace(FIRE[3], udbetaling_start_alder=78))
    r = optimer(p, A, 2026, BEREGNINGSDATO, maks_evalueringer=1500)
    assert r.bedste is not None and r.bedste_maaned > r.udgangspunkt_maaned + 1000


def test_deterministisk():
    p = profil()
    assert optimer(p, A, 2026, BEREGNINGSDATO, maks_evalueringer=300) == \
        optimer(p, A, 2026, BEREGNINGSDATO, maks_evalueringer=300)


def test_udtoemmende_ved_lille_soegerum_og_budget_overholdes():
    lille = optimer(profil(FIRE[1]), A, 2026, BEREGNINGSDATO, maks_evalueringer=5000)
    assert lille.udtoemmende and lille.evalueret == lille.mulige
    stor = optimer(profil(), A, 2026, BEREGNINGSDATO, maks_evalueringer=200)
    assert not stor.udtoemmende and stor.mulige > stor.evalueret
    assert stor.evalueret <= 200 + max(len(d) for d in opt.soegerum(profil(), A, 2026)[1]) * 3


def test_fremdrift_kaldes_og_slutter_ved_fuld():
    kald = []
    optimer(profil(FIRE[1]), A, 2026, BEREGNINGSDATO, fremdrift=lambda n, i_alt: kald.append((n, i_alt)))
    assert kald and kald[-1][0] == kald[-1][1]
    assert all(a <= b for (a, _), (b, _) in zip(kald, kald[1:]))


def test_ingen_ordninger_kun_folkepension():
    r = optimer(enlig_profil(ordninger=()), A, 2026, BEREGNINGSDATO)
    assert r.udtoemmende
    assert r.bedste is None or set(r.bedste.starter) == set()


# ── Grænser og værn ─────────────────────────────────────────────────────────────────────────────

def test_alle_kandidater_inden_for_graenserne(monkeypatch):
    p = profil()
    g = graenser(p, 2026)
    set_planer = []
    original = opt._evaluer_plan

    def spion(plan, *args, **kw):
        set_planer.append(plan)
        return original(plan, *args, **kw)

    monkeypatch.setattr(opt, "_evaluer_plan", spion)
    optimer(p, A, 2026, BEREGNINGSDATO, maks_evalueringer=300)
    assert set_planer
    for plan in set_planer:
        for oid, start in plan.starter.items():
            assert start >= g["ordninger"][oid]["tidligste"] - 1e-9
            assert start <= g["folkepensionsalder"] + g["opsaettelse_maks"]
        for oid, aar in plan.varighed.items():
            assert g["ratepension_aar"]["min"] <= aar <= g["ratepension_aar"]["maks"]
        assert 0 <= plan.opsaettelse <= g["opsaettelse_maks"]


def test_engangsbeloeb_uden_buffer_flyttes_ikke():
    ald = replace(FIRE[2], i_buffer=False)
    p = profil(FIRE[0], FIRE[1], ald)
    _, dimensioner = opt.soegerum(p, A, 2026)
    assert "ald" not in {d[0][1] for d in dimensioner if d[0][0] == "start"}
    r = optimer(p, A, 2026, BEREGNINGSDATO, maks_evalueringer=300)
    if r.bedste:
        assert "ald" not in r.bedste.starter


def test_vaern_forkaster_hul():
    """En plan, der skubber alt til 78 år, efterlader år uden indkomst. Den må aldrig vælges."""
    p = profil()
    udgangspunkt = opt._udgangspunkt(p, A)
    hul = Plan(starter={k: 78 for k in udgangspunkt.starter}, varighed=udgangspunkt.varighed, opsaettelse=10)
    ref = opt._reference(resultat(p), p)
    assert opt._evaluer_plan(hul, p, A, 2026, BEREGNINGSDATO, ref) is None


def test_ugyldig_kandidat_er_ikke_gennemfoerlig():
    p = profil()
    udgangspunkt = opt._udgangspunkt(p, A)
    for_tidligt = Plan(starter={**udgangspunkt.starter, "rate": 50}, varighed=udgangspunkt.varighed, opsaettelse=0)
    ref = opt._reference(resultat(p), p)
    assert opt._evaluer_plan(for_tidligt, p, A, 2026, BEREGNINGSDATO, ref) is None


# ── Egenskab (SC-001) ───────────────────────────────────────────────────────────────────────────

@given(
    st.integers(min_value=63, max_value=72), st.integers(min_value=10, max_value=20),
    st.integers(min_value=63, max_value=72), st.integers(min_value=100_000, max_value=2_000_000),
    st.booleans(),
)
@settings(max_examples=8, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def test_egenskab_aldrig_daarligere_og_inden_for_graenser(rate_start, rate_aar, liv_start, saldo, buffer):
    p = profil(
        Ordning("rate", "ratepension", saldo, rate_start, oprettet=date(2010, 1, 1), udbetaling_aar=rate_aar),
        Ordning("liv", "livsvarig", saldo, liv_start, oprettet=date(2010, 1, 1)),
        Ordning("ald", "aldersopsparing", saldo / 4, 66, oprettet=date(2010, 1, 1), i_buffer=buffer),
    )
    r = optimer(p, A, 2026, BEREGNINGSDATO, maks_evalueringer=150)
    if r.bedste is not None:
        assert r.bedste_maaned > r.udgangspunkt_maaned
        g = graenser(p, 2026)
        for oid, start in r.bedste.starter.items():
            assert g["ordninger"][oid]["tidligste"] - 1e-9 <= start <= g["folkepensionsalder"] + g["opsaettelse_maks"]


def test_buffer_der_ender_i_nul_er_ikke_et_hul():
    """Bufferen går op i nul i sidste år. Regnestøj (±1e-9) må ikke tælle som et hul — ellers
    vælger CPython og WebAssembly forskellige planer (fundet i T006, SC-002)."""
    res = resultat(profil())
    sidste = res.jaevn.aar[-1].buffer_rest
    assert abs(sidste) < 1
    ref = opt._reference(res, profil())
    negative = [j.buffer_rest * a.realfaktor for j, a in zip(res.jaevn.aar, res.aar)]
    assert ref.buffer_hul_aar == sum(1 for b in negative if b < -1)
    for stoej in (-1e-9, 1e-9):
        rykket = replace(res, jaevn=replace(res.jaevn, aar=(*res.jaevn.aar[:-1], replace(res.jaevn.aar[-1], buffer_rest=stoej))))
        assert opt._reference(rykket, profil()).buffer_hul_aar == ref.buffer_hul_aar
