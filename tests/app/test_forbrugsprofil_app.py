"""Feature 033 — forbrugsprofilen gennem oversættelse og visning (US1, US3)."""
import json

import pytest

from pensionsoverblik import app
from pensionsoverblik.oversaet import til_husstand, til_kerne
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_loen_app import med_loen
from tests.app.test_oversaet import GUIDE  # født 1963-05-01, ratepension fra 65

FALDENDE = [1.0, 1.0, 0.9, 0.8, 0.7]


def med_profil(guide, profil=FALDENDE):
    return {**guide, "antagelser": {**(guide.get("antagelser") or {}), "forbrugsprofil": profil}}


def test_profilen_oversaettes():
    _, a = til_kerne(med_profil(GUIDE))
    assert a.forbrugsprofil.procenter == tuple(FALDENDE)
    assert til_kerne(GUIDE)[1].forbrugsprofil.procenter == ()


def med_partner(guide, **antagelser):
    p = guide["person"]["partner"]
    return {**guide, "person": {**guide["person"], "partner": {**p, "antagelser": antagelser}}}


def test_partneren_arver_uden_egne_felter():
    # 037 FR-001: gemt før 037 – partneren bruger dine værdier.
    _, a, _, b = til_husstand(med_profil(PAR))
    assert b.forbrugsprofil.procenter == a.forbrugsprofil.procenter == tuple(FALDENDE)
    assert (b.afkast_efter_pal, b.beregningsgrundlag) == (a.afkast_efter_pal, a.beregningsgrundlag)


def test_partnerens_egne_antagelser():
    # 037: fordeling, afkast og grundlag hver for sig. Inflationen er husstandens.
    g = med_partner(med_profil(PAR), afkast_efter_pal=0.06, beregningsgrundlag="branchestandard",
                    forbrugsprofil=[1.0, 0.5], inflation=0.09)
    _, a, _, b = til_husstand(g)
    assert a.forbrugsprofil.procenter == tuple(FALDENDE) and b.forbrugsprofil.procenter == (1.0, 0.5)
    assert b.afkast_efter_pal == 0.06 and a.afkast_efter_pal != 0.06
    assert b.beregningsgrundlag == "branchestandard"
    assert b.inflation == a.inflation


def test_partnerens_tomme_profil_er_flad():
    _, a, _, b = til_husstand(med_partner(med_profil(PAR), forbrugsprofil=[]))
    assert a.forbrugsprofil.procenter == tuple(FALDENDE) and b.forbrugsprofil.procenter == ()


def test_feltfejl_peger_paa_partnerens_profil():
    r = app.beregn(json.dumps(med_partner(PAR, forbrugsprofil=[1.0, 1.6])), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "person.partner.antagelser.forbrugsprofil"


def test_scenarierne_flytter_begges_afkast():
    # 037 FR-004: ±1 procentpoint gælder begge, hver fra sit eget afkast.
    g = med_partner(PAR, afkast_efter_pal=0.06)
    dig = g["antagelser"].get("afkast_efter_pal", 0.04)
    s = app.scenarie(json.dumps(g), IDAG, dig - 0.01, g["antagelser"].get("inflation", 0.02))
    forventet = med_partner(PAR, afkast_efter_pal=0.05)
    forventet["antagelser"] = {**forventet["antagelser"], "afkast_efter_pal": dig - 0.01}
    v = app.beregn(json.dumps(forventet), IDAG)["data"]
    assert s["data"]["partner"] == v["husstand"]["partner"]["hovedtal"]["maaned"]


def test_feltfejl_peger_paa_profilen():
    r = app.beregn(json.dumps(med_profil(GUIDE, [1.0, 1.6])), IDAG)  # over 150 % (033b)
    assert not r["ok"] and r["fejl"]["felt"] == "antagelser.forbrugsprofil"


def test_visningen_har_baandene_med_beloeb():
    v = app.beregn(json.dumps(med_profil(med_loen(GUIDE))), IDAG)["data"]
    f = v["forbrug"]
    assert [(b["fra"], b["til"]) for b in f["baand"]][:2] == [(65, 69), (70, 74)]
    assert [b["procent"] for b in f["baand"]] == [100, 100, 90, 80, 70][:len(f["baand"])]
    assert all(b["maaned"] is None or b["maaned"] > 0 for b in f["baand"])
    # Hovedtallet er det laveste beløb i første bånd; båndet viser det typiske (det kan stige i trin, 010).
    # Folkepensionen kommer senere, men i forhold til det flade forløb er der mere først og mindre til sidst.
    flad = app.beregn(json.dumps(med_loen(GUIDE)), IDAG)["data"]
    assert flad["hovedtal"]["maaned"] <= v["hovedtal"]["maaned"] <= f["baand"][0]["maaned"]
    assert f["baand"][-1]["maaned"] < flad["forbrug"]["baand"][-1]["maaned"]
    assert any(a["kode"] == "FORBRUGSPROFIL" for a in v["hovedtal_advarsler"])


def test_baand_paa_nul_og_over_100_vises():
    # 033b: hovedtallet er beløbet ved 100 %; et bånd på 0 % viser intet beløb, og visningen fejler ikke.
    v = app.beregn(json.dumps(med_profil(med_loen(GUIDE), [1.0, 0.0, 1.5, 1.0, 1.0])), IDAG)["data"]
    f = v["forbrug"]
    assert [b["procent"] for b in f["baand"]][:3] == [100, 0, 150] and not f["flad"]
    assert f["baand"][1]["maaned"] == 0
    assert v["hovedtal"]["maaned"] > 0
    assert f["baand"][2]["maaned"] > f["baand"][0]["maaned"]  # 150 % (pengene kan komme i trin, 010)


def test_flad_profil_viser_baand_med_100_procent():
    v = app.beregn(json.dumps(med_loen(GUIDE)), IDAG)["data"]
    assert v["forbrug"]["baand"] and all(b["procent"] == 100 for b in v["forbrug"]["baand"])
    assert v["forbrug"]["flad"]


def test_antagelserne_er_i_json_form():
    # Fundet af test_pyodide: tuple i CPython, liste efter JSON i browseren.
    v = app.beregn(json.dumps(med_profil(GUIDE)), IDAG)["data"]
    assert v["antagelser"]["forbrugsprofil"]["procenter"] == FALDENDE
    assert json.loads(json.dumps(v["antagelser"])) == v["antagelser"]


def test_baandets_beloeb_er_det_typiske():
    # Set i browseren: 66 år med ratepension fra 64. Beregningen begynder ved 66, så 64–68 havde intet
    # beløb, og et bånds første år kan være et skæveår. Beløbet er det, båndet har i flest år (ved
    # lighed det seneste): 66–68 stiger i trin, så 64–68 viser 68's beløb, og 69–73 viser 90 % af det.
    g = {**GUIDE, "person": {**GUIDE["person"], "foedselsdato": "1960-05-01"},
         "ordninger": [{**GUIDE["ordninger"][0], "udbetaling_start_alder": 64}]}
    v = app.beregn(json.dumps(med_profil(g, [1.0, 0.9, 0.85, 0.8])), IDAG)["data"]
    baand = v["forbrug"]["baand"]
    pr_alder = {a["alder"]: round(a["jaevn"] * a["realfaktor"] / 12, -2) for a in v["aar"]}
    assert baand[0]["fra"] == 64 and baand[0]["maaned"] == pr_alder[68]
    assert baand[1]["maaned"] == pr_alder[70]
    assert baand[1]["maaned"] == pytest.approx(0.9 * baand[0]["maaned"], rel=0.01)
