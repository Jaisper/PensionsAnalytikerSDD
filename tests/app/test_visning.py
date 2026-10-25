"""T007/T008/T014 — visningsmodellen er ren omformatering af kernens resultat (SC-004)."""
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, Partner, PartnerIndkomst, beregn
from pensionskerne.model import Advarsel
from pensionsoverblik.katalog import ADVARSLER, KORT, KORT_FOR_KILDETYPE
from pensionsoverblik.visning import byg_visning
from tests.conftest import BEREGNINGSDATO, enlig_profil


def _profiler():
    rate = Ordning("rate", "ratepension", 1_200_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    liv = Ordning("liv", "livsvarig", 1_500_000, 67, oprettet=date(2019, 1, 1), aarlig_indbetaling=30_000)
    ald = Ordning("ald", "aldersopsparing", 300_000, 66, oprettet=date(2015, 1, 1))
    partner = Partner(date(1966, 3, 1), {aar: PartnerIndkomst(oevrig_indkomst=150_000) for aar in range(2026, 2060)})
    return [
        ("kun rate", enlig_profil(), Antagelser()),
        ("rate+liv+ald", enlig_profil(ordninger=(rate, liv, ald)), Antagelser(inflation=0.025)),
        ("kun folkepension", enlig_profil(ordninger=(), atp_aarlig=15_000), Antagelser()),
        ("gift", enlig_profil(ordninger=(rate, liv), civilstand="gift_samlevende", partner=partner), Antagelser()),
        ("opsat", enlig_profil(foedselsdato=date(1960, 1, 15), ordninger=(liv,)),
         Antagelser(folkepension_opsaettelse_aar=2)),
    ]


@pytest.fixture(params=_profiler(), ids=lambda p: p[0])
def res_og_visning(request):
    _, profil, antagelser = request.param
    res = beregn(profil, antagelser, 2026, BEREGNINGSDATO)
    return res, byg_visning(res)


def test_hovedtal_er_fast_beloeb_hele_perioden(res_og_visning):
    """Feature 008 (FR-003): hovedtallet er det laveste jævne beløb — det, man kan leve af hele
    perioden. Før 008 var det niveauet efter sidste engangsbeløb (fund E1 i 007)."""
    res, v = res_og_visning
    if not res.jaevn:
        return
    real = [j.jaevn * a.realfaktor / 12 for j, a in zip(res.jaevn.aar, res.aar)]
    ref = max([0] + [i for i in range(1, len(real)) if real[i] > real[i - 1] + 1])
    h = v["hovedtal"]
    assert h["type"] == "jaevn"
    assert h["maaned"] == round(min(real), -2)
    assert h["fra_alder"] == res.aar[0].alder
    assert h["senere"] == (None if ref == 0 else {"maaned": round(real[ref], -2), "fra_alder": res.aar[ref].alder})
    assert "foer" not in h


def test_hovedtal_med_senere_engangsbeloeb():
    rate = Ordning("rate", "ratepension", 800_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    ald = Ordning("ald", "aldersopsparing", 300_000, 66, oprettet=date(2015, 1, 1))
    v = byg_visning(beregn(enlig_profil(ordninger=(rate, ald)), Antagelser(), 2026, BEREGNINGSDATO))
    assert v["hovedtal"]["fra_alder"] == 65
    assert v["hovedtal"]["senere"]["fra_alder"] == 66
    assert v["hovedtal"]["senere"]["maaned"] > v["hovedtal"]["maaned"]


def test_hovedtal_er_optimeringens_faste_beloeb(res_og_visning):
    """SC-001: samme tal som "Find bedste plan" bruger (lukker E1 fra 007)."""
    from pensionskerne.optimering import fast_niveau, vindue

    res, v = res_og_visning
    if res.jaevn:
        assert v["hovedtal"]["maaned"] == round(fast_niveau(res, vindue(res)), -2)


def test_engangsbeloeb_og_buffer_i_grafen():
    """Feature 008 (FR-002, SC-002): hvert engangsbeløb med ordning og buffer/direkte, og
    bufferen år for år i dagens kroner."""
    rate = Ordning("rate", "ratepension", 800_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    ald = Ordning("ald", "aldersopsparing", 300_000, 66, oprettet=date(2015, 1, 1))
    kap = Ordning("kap", "kapitalpension", 400_000, 66, oprettet=date(2000, 1, 1), i_buffer=False)
    res = beregn(enlig_profil(ordninger=(rate, ald, kap)), Antagelser(), 2026, BEREGNINGSDATO)
    v = byg_visning(res)
    engangs = v["graf"]["engangs"]
    assert {(e["ordning_id"], e["type"], e["alder"], e["i_buffer"]) for e in engangs} == {
        ("ald", "aldersopsparing", 66, True), ("kap", "kapitalpension", 66, False)}
    pr_aar = {a.alder: a.engangsbeloeb_netto * a.realfaktor for a in res.aar}
    assert sum(e["netto_real"] for e in engangs) == pytest.approx(pr_aar[66])
    buffer = [b for b in v["graf"]["buffer"] if b is not None]
    assert len(buffer) == len(res.aar)
    for b, j, a in zip(buffer, res.jaevn.aar, res.aar):
        forventet = j.buffer_rest * a.realfaktor
        assert b == pytest.approx(0 if abs(forventet) < 1 else forventet)
    assert buffer[-1] == 0
    kort = next(k for k in v["kort"] if k["noegle"] == "engangsbeloeb")
    assert {(e["ordning_id"], e["i_buffer"]) for e in kort["engangs"]} == {("ald", True), ("kap", False)}


def test_buffer_er_aldrig_negativ(res_og_visning):
    """Feature 010: udjævningen låner aldrig — bufferen er altid 0 eller mere."""
    _, v = res_og_visning
    if v["graf"]["buffer"]:
        assert min(b for b in v["graf"]["buffer"] if b is not None) >= 0


def test_graf_matcher_kernen(res_og_visning):
    """Grafen starter ved en fast alder (aksen hopper ikke, når ordninger flyttes); årene før den
    første udbetaling er tomme. Resten er kernens år, uændret."""
    res, v = res_og_visning
    foran = len(v["graf"]["aldre"]) - len(res.aar)
    assert v["graf"]["aldre"][foran:] == [a.alder for a in res.aar]
    for serie in v["graf"]["serier"]:
        assert serie["vaerdier"][:foran] == [0.0] * foran
        for i, a in enumerate(res.aar):
            forventet = sum(k.netto for k in a.kilder if KORT_FOR_KILDETYPE[k.type] == serie["noegle"])
            assert serie["vaerdier"][foran + i] == pytest.approx(forventet * a.realfaktor / 12)


def test_aksen_starter_ved_60_eller_nuvaerende_alder():
    for foedt, forventet in ((date(1968, 3, 15), 60), (date(1963, 5, 1), 63)):  # 58 og 63 år i 2026
        rate = Ordning("rate", "ratepension", 800_000, 66, oprettet=date(2010, 1, 1), udbetaling_aar=10)
        v = byg_visning(beregn(enlig_profil(foedselsdato=foedt, ordninger=(rate,)), Antagelser(), 2026, BEREGNINGSDATO))
        assert v["graf"]["aldre"][0] == forventet
        foran = v["graf"]["aldre"].index(66) if 66 in v["graf"]["aldre"] else 0
        assert v["graf"]["jaevn"][:foran] == [None] * foran and v["graf"]["buffer"][:foran] == [None] * foran


def test_graf_summer_til_netto_real(res_og_visning):
    res, v = res_og_visning
    foran = len(v["graf"]["aldre"]) - len(res.aar)
    for i, a in enumerate(res.aar):
        assert sum(s["vaerdier"][foran + i] for s in v["graf"]["serier"]) == pytest.approx(a.netto_real / 12)


def test_kort_matcher_kernen(res_og_visning):
    res, v = res_og_visning
    for kort in v["kort"]:
        if kort["noegle"] == "engangsbeloeb":
            continue  # testes i test_engangsbeloeb_faar_eget_kort
        assert kort["titel"] == KORT[kort["noegle"]]["titel"]
        serie = next(s for s in v["graf"]["serier"] if s["noegle"] == kort["noegle"])
        aldre_med_vaerdi = [al for al, x in zip(v["graf"]["aldre"], serie["vaerdier"]) if x > 0]
        assert kort["fra_alder"] == aldre_med_vaerdi[0] and kort["til_alder"] == aldre_med_vaerdi[-1]
        for d in kort["detaljer"]:
            a = res.aar_ved(d["alder"])
            kilder = [k for k in a.kilder if KORT_FOR_KILDETYPE[k.type] == kort["noegle"]]
            assert d["netto"] == pytest.approx(sum(k.netto for k in kilder))
            assert d["skat"] == pytest.approx(sum(k.skat for k in kilder))


def test_aar_og_satser(res_og_visning):
    res, v = res_og_visning
    assert [r["netto"] for r in v["aar"]] == pytest.approx([a.netto_i_alt for a in res.aar])
    assert all(s["kilde"] and s["status"] in ("verificeret", "sekundaer", "uverificeret") for s in v["satser"])
    assert {s["id"] for s in v["satser"]} <= set(res.sporing_samlet)


def test_kun_kort_med_indhold(res_og_visning):
    _, v = res_og_visning
    assert all(k["fra_alder"] is not None for k in v["kort"])


def test_hver_kendt_advarsel_placeres_som_i_kataloget():
    res = beregn(enlig_profil(), Antagelser(), 2026, BEREGNINGSDATO)
    for kode, info in ADVARSLER.items():
        falsk = Advarsel(kode, "tekst", aldre=(70, 72))
        v = byg_visning(res.__class__(**{**res.__dict__, "advarsler": (falsk,)}))
        if info["placering"] == "hovedtal":
            assert v["hovedtal_advarsler"][0]["kode"] == kode
        elif info["placering"] == "graf":
            assert v["graf"]["markeringer"][0]["fra"] == 70
            assert v["generelle_advarsler"][0]["kode"] == kode
        elif info["placering"] == "generel":
            assert v["generelle_advarsler"][0]["kode"] == kode
        else:  # kort
            kort = [k for k in v["kort"] if k["noegle"] == info["placering"]]
            target = kort[0]["advarsler"] if kort else v["generelle_advarsler"]
            assert target[0]["kode"] == kode
        assert info["ikon"] in ("!", "≈")


def test_ukendt_advarsel_bliver_generel():
    res = beregn(enlig_profil(), Antagelser(), 2026, BEREGNINGSDATO)
    v = byg_visning(res.__class__(**{**res.__dict__, "advarsler": (Advarsel("NY_KODE", "Noget nyt"),)}))
    assert v["generelle_advarsler"][0]["besked"] == "Noget nyt"


def test_jaevn_linje_i_dagens_kroner(res_og_visning):
    res, v = res_og_visning
    if not res.jaevn:
        assert v["graf"]["jaevn"] is None
        return
    for i, (j, a) in enumerate(zip(res.jaevn.aar, res.aar)):
        assert v["graf"]["jaevn"][len(v["graf"]["aldre"]) - len(res.aar) + i] == pytest.approx(j.jaevn * a.realfaktor / 12)


def test_engangsbeloeb_faar_eget_kort():
    ald = Ordning("ald", "aldersopsparing", 300_000, 66, oprettet=date(2015, 1, 1))
    res = beregn(enlig_profil(ordninger=(ald,)), Antagelser(afkast_efter_pal=0, inflation=0), 2026, BEREGNINGSDATO)
    v = byg_visning(res)
    kort = next(k for k in v["kort"] if k["noegle"] == "engangsbeloeb")
    assert kort["engangs"] == [{"ordning_id": "ald", "type": "aldersopsparing", "alder": 66, "i_buffer": True,
                                "netto": pytest.approx(300_000), "netto_real": pytest.approx(300_000)}]
    assert kort["netto_maaned"] is None
    assert "engangsbeloeb" not in [s["noegle"] for s in v["graf"]["serier"]]
