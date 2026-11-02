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


def test_partneren_deler_profilen():
    _, a, _, b = til_husstand(med_profil(PAR))
    assert a.forbrugsprofil == b.forbrugsprofil


def test_feltfejl_peger_paa_profilen():
    r = app.beregn(json.dumps(med_profil(GUIDE, [1.0, 1.2])), IDAG)
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
