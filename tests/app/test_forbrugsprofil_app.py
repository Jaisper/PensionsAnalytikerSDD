"""Feature 033 — forbrugsprofilen gennem oversættelse og visning (US1, US3)."""
import json

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
    # Hovedtallet er beløbet i første bånd. Folkepensionen kommer senere, så beløbet kan stadig stige i
    # trin (010), men i forhold til det flade forløb er der mere først og mindre til sidst.
    flad = app.beregn(json.dumps(med_loen(GUIDE)), IDAG)["data"]
    assert v["hovedtal"]["maaned"] == f["baand"][0]["maaned"] >= flad["hovedtal"]["maaned"]
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
