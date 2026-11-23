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


def test_kort_baand_foer_85_laegges_sammen():
    # Stop ved 64: 84–84 ville være ét år; det lægges sammen med 79–83.
    assert baand(64, 90) == ((64, 68), (69, 73), (74, 78), (79, 84), (85, 90))
    assert baand(83, 90) == ((83, 84), (85, 90))  # intet bånd foran at lægge det sammen med


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


def test_baand_paa_nul_faar_intet_og_pengene_venter():
    # 033b: [300, 0, 0] med vægte 0, 1, 1: år 0 får intet, c = 300 / 2 = 150 → 0, 150, 150.
    jaevn, buffer = niveauer([300, 0, 0], [0.0, 1.0, 1.0])
    assert jaevn == [0, 150, 150]
    assert buffer == [300, 150, 0]


def test_stigende_baand_faar_mere():
    # 033b: [350, 0, 0] med vægte 1, 1, 1,5: c = 350 / 3,5 = 100 → 100, 100, 150.
    jaevn, buffer = niveauer([350, 0, 0], [1.0, 1.0, 1.5])
    assert jaevn == [100, 100, 150]
    assert buffer == [250, 150, 0]


def test_sidste_baand_paa_nul_laaner_ikke():
    # 033b: [100, 100, 100] med vægte 1, 1, 0: pengene i det sidste år kan ikke bruges før (010), så de
    # bliver stående som formue.
    jaevn, buffer = niveauer([100, 100, 100], [1.0, 1.0, 0.0])
    assert jaevn == [100, 100, 0]
    assert buffer == [0, 0, 100]


# Faldende profiler (033) og vilkårlige profiler fra 0 til 150 % med et sidste bånd over 0 (033b).
faldende_profiler = st.lists(st.sampled_from([x / 20 for x in range(10, 21)]), min_size=1, max_size=30).map(
    lambda xs: [1.0] + sorted(xs, reverse=True)[1:])
frie_profiler = st.lists(st.sampled_from([x / 20 for x in range(0, 31)]), min_size=1, max_size=30)


@given(st.lists(st.floats(min_value=0, max_value=500_000), min_size=1, max_size=30),
       st.one_of(faldende_profiler, frie_profiler),
       st.floats(min_value=0, max_value=0.08), st.floats(min_value=0, max_value=0.05))
@settings(max_examples=200, deadline=None)
def test_egenskab_aldrig_laan_og_ender_i_nul(netto, profil, rente, inflation):
    vaegt = (profil + [profil[-1]] * len(netto))[:len(netto)]
    vaegt[-1] = vaegt[-1] or 0.05  # står det sidste år på 0 %, bliver pengene stående (test ovenfor)
    j = beregn_jaevn(raekker(netto), {}, rente, inflation, 2030, vaegt=vaegt)
    g = 1 + inflation
    normeret = [a.jaevn / g ** i / vaegt[i] for i, a in enumerate(j.aar) if vaegt[i] > 0]
    tol = 1e-6 * (1 + max(netto))
    assert all(a.buffer_rest >= -tol for a in j.aar)
    assert all(a.jaevn == 0 for i, a in enumerate(j.aar) if vaegt[i] == 0)
    assert all(normeret[i + 1] >= normeret[i] - tol for i in range(len(normeret) - 1))
    assert j.aar[-1].buffer_rest == pytest.approx(0, abs=1e-6 * (1 + sum(netto)))


@given(st.lists(st.floats(min_value=0, max_value=500_000), min_size=1, max_size=30), faldende_profiler)
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


# ── Validering (FR-001, FR-005; 033b) ──────────────────────────────────────────

@pytest.mark.parametrize("procenter", [
    (1.0, -0.05),        # under 0 %
    (1.0, 1.55),         # over 150 %
    (0.0, 0.0, 0.0),     # mindst ét bånd over 0 %
])
def test_ugyldig_profil(procenter):
    with pytest.raises(UgyldigtInput) as e:
        valider(profil(), Antagelser(forbrugsprofil=Forbrugsprofil(procenter)), 2026, BEREGNINGSDATO)
    assert e.value.felt == "antagelser.forbrugsprofil"


@pytest.mark.parametrize("procenter", [
    FALDENDE.procenter,
    (0.9, 0.8),                    # første bånd kan ændres (033b)
    (1.0, 0.8, 0.9),               # og senere bånd kan stige
    (1.5, 0.0, 1.2, 0.45, 1.0),    # 0–150 % i vilkårlig rækkefølge
])
def test_gyldig_profil(procenter):
    ant = Antagelser(forbrugsprofil=Forbrugsprofil(procenter))
    valider(profil(), ant, 2026, BEREGNINGSDATO)
    valider(replace(profil(), loen=Loen(480_000, stop_alder=60)), ant, 2026, BEREGNINGSDATO)


FRI = Forbrugsprofil((1.2, 1.0, 0.0, 1.5, 1.0))  # 033b: op, ned og et bånd uden udbetaling


def test_fri_profil_i_hele_beregningen():
    res = beregn(profil(), Antagelser(forbrugsprofil=FRI), 2026, BEREGNINGSDATO)
    v = {j.alder: j.vaegt for j in res.jaevn.aar}
    assert v[65] == 1.2 and v[70] == 1.0 and v[75] == 0.0 and v[80] == 1.5 and v[85] == 1.0
    r = real(res)
    assert all(r[a] == 0 for a in range(75, 80))                       # 75–79 får intet
    normeret = [r[a] / v[a] for a in sorted(r) if a >= 65 and v[a] > 0]
    assert all(y >= x - 12 for x, y in zip(normeret, normeret[1:]))   # ikke-faldende i forhold til profilen
    assert all(j.buffer_rest >= -12 for j in res.jaevn.aar)
    assert res.jaevn.aar[-1].buffer_rest == pytest.approx(0, abs=12)
    assert r[80] == pytest.approx(1.5 / 1.2 * r[65], rel=0.02)        # forholdet mellem båndene holdes


def test_optimeringens_maal_springer_baand_paa_nul_over():
    from pensionskerne.optimering import fast_niveau, slutniveau, spring, vindue
    res = beregn(profil(), Antagelser(forbrugsprofil=FRI), 2026, BEREGNINGSDATO)
    maal = fast_niveau(res, vindue(res))
    assert maal == pytest.approx(real(res)[65] / 1.2 / 12)            # beløbet ved 100 %
    assert slutniveau(res) > 0 and spring(res, vindue(res)) >= 0


def test_forudsaetning_med_fri_profil():
    res = beregn(profil(), Antagelser(forbrugsprofil=FRI), 2026, BEREGNINGSDATO)
    besked = next(a.besked for a in res.advarsler if a.kode == "FORBRUGSPROFIL")
    assert "120 % fra 65, 100 % fra 70, 0 % fra 75, 150 % fra 80, 100 % fra 85" in besked
    stigende = beregn(profil(), Antagelser(forbrugsprofil=Forbrugsprofil((1.0, 1.0, 1.2))), 2026,
                      BEREGNINGSDATO)
    assert "120 % fra 75" in next(a.besked for a in stigende.advarsler if a.kode == "FORBRUGSPROFIL")


def test_hver_sin_profil_fra_egen_stopalder():
    # 037 (erstatter 033's fælles profil, produktejerens beslutning 2026-11-23): A (født 1958) stopper
    # ved 67 i 2025, B (født 1962) ved 64 i 2026. Hver har sin egen profil fra sin egen stopalder.
    from pensionskerne.husstand import beregn_husstand
    from tests.golden.test_husstand import A, A_ANT, B
    vaegte = lambda res: {a.kalenderaar: j.vaegt for j, a in zip(res.jaevn.aar, res.aar)}
    a_ant = replace(A_ANT, forbrugsprofil=Forbrugsprofil((1.0, 0.8)))
    h = beregn_husstand(A, a_ant, B, A_ANT, 2026, BEREGNINGSDATO)
    va, vb = vaegte(h.a), vaegte(h.b)
    assert va[2029] == 1.0 and va[2030] == 0.8 and va[2040] == 0.8    # A: 67–71 er 2025–2029
    assert all(w == 1.0 for w in vb.values())                         # B: flad
    h = beregn_husstand(A, A_ANT, B, replace(A_ANT, forbrugsprofil=Forbrugsprofil((1.0, 0.5))), 2026,
                        BEREGNINGSDATO)
    va, vb = vaegte(h.a), vaegte(h.b)
    assert all(w == 1.0 for w in va.values())
    assert vb[2030] == 1.0 and vb[2031] == 0.5                         # B: 64–68 er 2026–2030


# ── Den bedste plan (US2, FR-004) ──────────────────────────────────────────────

def test_optimeringens_maal_er_beloebet_i_foerste_baand():
    from pensionskerne.optimering import fast_niveau, vindue
    res = beregn(profil(), Antagelser(forbrugsprofil=FALDENDE), 2026, BEREGNINGSDATO)
    assert fast_niveau(res, vindue(res)) == pytest.approx(real(res)[65] / 12)


# ── Resultatet til visningen (US3, FR-008) ─────────────────────────────────────

def test_baandene_staar_paa_resultatet():
    res = beregn(profil(), Antagelser(), 2026, BEREGNINGSDATO)
    assert res.forbrug_baand[0] == (65, 69) and res.forbrug_baand[-1][0] == 85
    tidlig = beregn(replace(profil(), loen=Loen(480_000, stop_alder=60)), Antagelser(), 2026, BEREGNINGSDATO)
    assert tidlig.forbrug_baand[:2] == ((60, 64), (65, 69)) and len(tidlig.forbrug_baand) == 6


def test_husstandens_baand_fra_egen_stopalder():
    # 037: A stopper ved 67, B ved 64. Før 037 fulgte B's bånd A's (63–67 i B's aldre).
    from pensionskerne.husstand import beregn_husstand
    from tests.golden.test_husstand import A, A_ANT, B
    ant = replace(A_ANT, forbrugsprofil=Forbrugsprofil((1.0, 0.8)))
    h = beregn_husstand(A, ant, B, ant, 2026, BEREGNINGSDATO)
    assert h.a.forbrug_baand[0] == (67, 71)
    assert h.b.forbrug_baand[0] == (64, 68)


def test_forudsaetning_kun_med_faldende_profil():
    koder = lambda res: [a.kode for a in res.advarsler]
    assert "FORBRUGSPROFIL" not in koder(beregn(profil(), Antagelser(), 2026, BEREGNINGSDATO))
    res = beregn(profil(), Antagelser(forbrugsprofil=FALDENDE), 2026, BEREGNINGSDATO)
    besked = next(a.besked for a in res.advarsler if a.kode == "FORBRUGSPROFIL")
    assert "90 % fra 75, 80 % fra 80, 70 % fra 85" in besked
