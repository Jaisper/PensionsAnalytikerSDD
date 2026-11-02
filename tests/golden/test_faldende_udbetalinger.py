"""Feature 033 — faldende udbetalinger: en profil med en procent pr. bånd på fem år fra stopalderen.

Udjævningen vægter hvert år, så niveauet i år t er c · vægt(t) i dagens kroner. Reglerne fra 010
gælder uændret: ingen lån, ingen negativ buffer, og bufferen ender i 0. Golden cases regnet i hånden
med rente 0 og inflation 0.
"""
from dataclasses import replace
from datetime import date

import pytest
from hypothesis import given, settings, strategies as st

from pensionskerne import Antagelser, Loen, Ordning, UgyldigtInput, beregn
from pensionskerne.jaevn import baand, beregn_jaevn, vaegte
from pensionskerne.model import Forbrugsprofil
from pensionskerne.validering import valider
from tests.conftest import BEREGNINGSDATO, enlig_profil
from tests.golden.test_jaevn_uden_laan import raekker


def niveauer(netto, vaegt, engangs=None):
    j = beregn_jaevn(raekker(netto), engangs or {}, 0.0, 0.0, 2030, vaegt=vaegt)
    return [round(a.jaevn, 6) for a in j.aar], [round(a.buffer_rest, 6) for a in j.aar]


# ── Båndene (FR-003) ──────────────────────────────────────────────────────────

def test_baand_fra_60_giver_seks():
    assert baand(60, 95) == ((60, 64), (65, 69), (70, 74), (75, 79), (80, 84), (85, 95))


def test_baand_fra_67_slutter_ved_84_og_85_plus():
    assert baand(67, 90) == ((67, 71), (72, 76), (77, 81), (82, 84), (85, 90))


def test_baand_fra_65_til_90_giver_fem():
    assert baand(65, 90) == ((65, 69), (70, 74), (75, 79), (80, 84), (85, 90))


def test_baand_slutter_med_planen():
    assert baand(65, 78) == ((65, 69), (70, 74), (75, 78))


def test_vaegte_pr_alder():
    profil = (1.0, 1.0, 0.9, 0.8, 0.7)
    v = vaegte(profil, start_alder=65, aldre=range(63, 92))
    assert v[63] == v[64] == 1.0                       # før stopalderen
    assert v[65] == v[69] == v[70] == v[74] == 1.0
    assert v[75] == 0.9 and v[80] == 0.8 and v[85] == 0.7 and v[91] == 0.7


def test_kortere_profil_end_baand_bruger_sidste_procent():
    # Stopalderen flyttes fra 65 til 60: seks bånd, men profilen har fem procenter (US1 scenarie 6).
    v = vaegte((1.0, 0.9, 0.8, 0.7, 0.6), start_alder=60, aldre=range(60, 95))
    assert [v[a] for a in (60, 65, 70, 75, 80, 85)] == [1.0, 0.9, 0.8, 0.7, 0.6, 0.6]


# ── Vægtet udjævning (FR-002) ──────────────────────────────────────────────────

def test_penge_der_kommer_foerst_fordeles_efter_profilen():
    # [300, 0, 0] med vægte 1, ½, ½: c = 300 / (1 + ½ + ½) = 150 → 150, 75, 75; bufferen 150, 75, 0.
    jaevn, buffer = niveauer([300, 0, 0], [1.0, 0.5, 0.5])
    assert jaevn == [150, 75, 75]
    assert buffer == [150, 75, 0]


def test_penge_der_kommer_senere_kan_stadig_ikke_bruges_foer():
    # [0, 100, 200] med vægte 1, ½, ½: fra år 0 er minimum 0 → 0. Fra år 1: min(100/½, 300/1) = 200
    # → 200 · ½ = 100. År 2: 200/½ = 400 → 200. Profilen kan ikke låne af fremtiden (010).
    jaevn, buffer = niveauer([0, 100, 200], [1.0, 0.5, 0.5])
    assert jaevn == [0, 100, 200]
    assert buffer == [0, 0, 0]


def test_trin_holder_forholdet_mellem_baandene():
    # [100, 0, 300, 0] med vægte 1, 1, ½, ½: fra år 0: min(100, 50, 400/2,5, 400/3) = 50 ved k=1.
    # Fra år 2: min(300/½, 300/1) = 300 ved k=3 → 150, 150. Forholdet ½ holdes inden for segmentet.
    jaevn, buffer = niveauer([100, 0, 300, 0], [1.0, 1.0, 0.5, 0.5])
    assert jaevn == [50, 50, 150, 150]
    assert buffer == [50, 0, 150, 0]


def test_vaegten_gemmes_pr_aar():
    j = beregn_jaevn(raekker([300, 0, 0]), {}, 0.0, 0.0, 2030, vaegt=[1.0, 0.5, 0.5])
    assert [a.vaegt for a in j.aar] == [1.0, 0.5, 0.5]


def test_uden_vaegt_er_alt_som_foer():
    netto = [120_000, 0, 300_000, 50_000, 0]
    uden = beregn_jaevn(raekker(netto), {67: 80_000}, 0.03, 0.02, 2030)
    flad = beregn_jaevn(raekker(netto), {67: 80_000}, 0.03, 0.02, 2030, vaegt=[1.0] * 5)
    assert uden == flad


profiler = st.lists(st.sampled_from([x / 20 for x in range(10, 21)]), min_size=1, max_size=30).map(
    lambda xs: [1.0] + sorted(xs, reverse=True)[1:])


@given(st.lists(st.floats(min_value=0, max_value=500_000), min_size=1, max_size=30), profiler,
       st.floats(min_value=0, max_value=0.08), st.floats(min_value=0, max_value=0.05))
@settings(max_examples=150, deadline=None)
def test_egenskab_aldrig_laan_og_ender_i_nul(netto, profil, rente, inflation):
    vaegt = (profil + [profil[-1]] * len(netto))[:len(netto)]
    j = beregn_jaevn(raekker(netto), {}, rente, inflation, 2030, vaegt=vaegt)
    g = 1 + inflation
    normeret = [a.jaevn / g ** i / vaegt[i] for i, a in enumerate(j.aar)]
    tol = 1e-6 * (1 + max(netto))
    assert all(a.buffer_rest >= -tol for a in j.aar)
    assert all(normeret[i + 1] >= normeret[i] - tol for i in range(len(normeret) - 1))
    assert j.aar[-1].buffer_rest == pytest.approx(0, abs=1e-6 * (1 + sum(netto)))


@given(st.lists(st.floats(min_value=0, max_value=500_000), min_size=1, max_size=30), profiler)
@settings(max_examples=100, deadline=None)
def test_egenskab_foerste_aar_mindst_som_det_flade(netto, profil):
    # US1 scenarie 3: en profil, der ikke stiger, giver mindst lige så meget i det første år.
    vaegt = (profil + [profil[-1]] * len(netto))[:len(netto)]
    flad = beregn_jaevn(raekker(netto), {}, 0.0, 0.0, 2030)
    faldende = beregn_jaevn(raekker(netto), {}, 0.0, 0.0, 2030, vaegt=vaegt)
    assert faldende.aar[0].jaevn >= flad.aar[0].jaevn - 1e-6 * (1 + max(netto))


# ── Hele beregningen ───────────────────────────────────────────────────────────

FOEDT = date(1966, 3, 1)  # 60 år i 2026, folkepension 69
RATE = Ordning("rate", "ratepension", 1_200_000, 65, oprettet=date(2000, 1, 1), udbetaling_aar=10)
LIV = Ordning("liv", "livsvarig", 1_000_000, 67, oprettet=date(2000, 1, 1))
KAP = Ordning("kap", "kapitalpension", 900_000, 65, oprettet=date(2000, 1, 1))
FALDENDE = Forbrugsprofil((1.0, 1.0, 0.9, 0.8, 0.7))


def profil():
    return enlig_profil(foedselsdato=FOEDT, ordninger=(RATE, LIV, KAP), loen=Loen(480_000))


def real(res):
    return {j.alder: j.jaevn * a.realfaktor for j, a in zip(res.jaevn.aar, res.aar)}


def test_flad_profil_er_som_foer():
    # SC-002: en flad profil ændrer intet (kun de gemte antagelser er forskellige).
    flad = beregn(profil(), Antagelser(forbrugsprofil=Forbrugsprofil((1.0,) * 5)), 2026, BEREGNINGSDATO)
    uden = beregn(profil(), Antagelser(), 2026, BEREGNINGSDATO)
    assert replace(flad, antagelser=uden.antagelser) == uden


def test_faldende_profil_i_hele_beregningen():
    flad = beregn(profil(), Antagelser(), 2026, BEREGNINGSDATO)
    res = beregn(profil(), Antagelser(forbrugsprofil=FALDENDE), 2026, BEREGNINGSDATO)
    assert res.jaevn_fra_alder == 65
    v = {j.alder: j.vaegt for j in res.jaevn.aar}
    assert v[64] == v[65] == v[74] == 1.0 and v[75] == 0.9 and v[80] == 0.8 and v[85] == 0.7
    r = real(res)
    normeret = [r[a] / v[a] for a in sorted(r) if a >= 65]
    assert all(y >= x - 12 for x, y in zip(normeret, normeret[1:]))   # ikke-faldende i forhold til profilen
    assert res.jaevn.aar[-1].buffer_rest == pytest.approx(0, abs=12)
    assert all(j.buffer_rest >= -12 for j in res.jaevn.aar)
    assert r[65] > real(flad)[65]                                      # mere i de første år
    assert r[85] < real(flad)[85]                                      # mindre senere


def test_profilen_aendrer_ikke_udbetalingerne_kun_bufferen():
    # FR-007: ordningerne, lønnen og grundbeløbet er de samme. Pensionstillæg og ældrecheck kan stige,
    # fordi bufferen bliver mindre, når mere bruges i de første år (mindre formue og kapitalindkomst).
    uden_kap = enlig_profil(foedselsdato=FOEDT, ordninger=(RATE, LIV), loen=Loen(480_000))
    flad = beregn(uden_kap, Antagelser(), 2026, BEREGNINGSDATO)
    res = beregn(uden_kap, Antagelser(forbrugsprofil=FALDENDE), 2026, BEREGNINGSDATO)

    def kilder(a, typer):
        return {k.kilde_id: k.brutto for k in a.kilder if k.type in typer}

    faste = {"ratepension", "livsvarig", "loen", "atp", "grundbeloeb"}
    ydelser = {"pensionstillaeg", "aeldrecheck"}
    for a, b in zip(flad.aar, res.aar):
        assert kilder(a, faste) == pytest.approx(kilder(b, faste))
        assert sum(kilder(b, ydelser).values()) >= sum(kilder(a, ydelser).values()) - 1


def test_husstandens_startaar_gaelder():
    # US1 + partner: båndene regnes fra et fælles kalenderår (den første, der stopper).
    start = Forbrugsprofil((1.0, 0.5), start_kalenderaar=FOEDT.year + 70, start_alder=70)
    res = beregn(profil(), Antagelser(forbrugsprofil=start), 2026, BEREGNINGSDATO)
    v = {j.alder: j.vaegt for j in res.jaevn.aar}
    assert v[74] == 1.0 and v[75] == 0.5


# ── Validering (FR-005) ────────────────────────────────────────────────────────

@pytest.mark.parametrize("procenter", [
    (0.9, 0.8),          # første bånd skal være 100 %
    (1.0, 0.45),         # under 50 %
    (1.0, 0.8, 0.9),     # må ikke stige
    (1.0, 1.05),         # over 100 %
])
def test_ugyldig_profil(procenter):
    with pytest.raises(UgyldigtInput) as e:
        valider(profil(), Antagelser(forbrugsprofil=Forbrugsprofil(procenter)), 2026, BEREGNINGSDATO)
    assert e.value.felt == "antagelser.forbrugsprofil"


def test_gyldig_profil():
    valider(profil(), Antagelser(forbrugsprofil=FALDENDE), 2026, BEREGNINGSDATO)
    valider(replace(profil(), loen=Loen(480_000, stop_alder=60)), Antagelser(forbrugsprofil=FALDENDE), 2026,
            BEREGNINGSDATO)


def test_husstanden_deler_profilen_fra_den_foerste_der_stopper():
    # A (født 1958) stopper ved 67 i 2025, B (født 1962) ved 64 i 2026. Båndene regnes fra 2025 i A's
    # aldre: 2025–2029 er 100 %, 2030–2034 er 80 %, for begge.
    from pensionskerne.husstand import beregn_husstand
    from tests.golden.test_husstand import A, A_ANT, B
    ant = replace(A_ANT, forbrugsprofil=Forbrugsprofil((1.0, 0.8)))
    h = beregn_husstand(A, ant, B, ant, 2026, BEREGNINGSDATO)
    for res in (h.a, h.b):
        v = {a.kalenderaar: j.vaegt for j, a in zip(res.jaevn.aar, res.aar)}
        assert v[2029] == 1.0 and v[2030] == 0.8 and v[2040] == 0.8


# ── Den bedste plan (US2, FR-004) ──────────────────────────────────────────────

def test_optimeringens_maal_er_beloebet_i_foerste_baand():
    from pensionskerne.optimering import fast_niveau, vindue
    res = beregn(profil(), Antagelser(forbrugsprofil=FALDENDE), 2026, BEREGNINGSDATO)
    assert fast_niveau(res, vindue(res)) == pytest.approx(real(res)[65] / 12)
