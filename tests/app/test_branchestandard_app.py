"""Feature 035 T011 — branchestandarden gennem indgangslaget (US1, US2, FR-001, FR-007)."""
import json

from pensionsoverblik import app
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_oversaet import GUIDE


def med(guide, grundlag):
    return {**guide, "antagelser": {**guide["antagelser"], "beregningsgrundlag": grundlag}}


def regn(guide):
    r = app.beregn(json.dumps(guide), IDAG)
    assert r["ok"], r
    return r["data"]


def test_gemt_input_uden_feltet_er_egne_antagelser():
    """US1-3: et input fra før featuren åbnes med egne antagelser."""
    v = regn(GUIDE)
    assert v["antagelser"]["beregningsgrundlag"] == "egne"
    assert v["hovedtal"]["prognose"] is None
    assert v["grundlag"] == {"type": "egne", "saet": None}


def test_branchestandard_giver_tre_tal():
    v = regn(med(GUIDE, "branchestandard"))
    h = v["hovedtal"]
    assert h["prognose"]["lav"] < h["maaned"] < h["prognose"]["hoej"]
    assert all(x % 100 == 0 for x in (h["prognose"]["lav"], h["prognose"]["hoej"]))
    assert v["grundlag"] == {"type": "branchestandard", "saet": "1. halvår 2027"}


def test_ukendt_grundlag_afvises():
    r = app.beregn(json.dumps(med(GUIDE, "gaet")), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "antagelser.beregningsgrundlag"


def test_par_faar_tre_tal_for_begge():
    v = regn(med(PAR, "branchestandard"))
    assert v["hovedtal"]["prognose"] is not None
    assert v["husstand"]["partner"]["hovedtal"]["prognose"] is not None


def test_scenarier_med_branchestandard_er_kun_levetid():
    """Afkast- og inflationsscenarierne gælder egne antagelser; branchestandarden har sit eget spænd."""
    s = app.scenarier(json.dumps(med(GUIDE, "branchestandard")))
    assert s and all(x["noegle"].startswith("levetid") for x in s)


def test_levetidsscenarie_med_branchestandard():
    s = next(x for x in app.scenarier(json.dumps(med(GUIDE, "branchestandard"))) if x["noegle"] == "levetid_95")
    r = app.scenarie(json.dumps(med(GUIDE, "branchestandard")), IDAG, s["afkast"], s["inflation"], s["plan_slut_alder"])
    assert r["ok"] and r["data"]["dig"] > 0


# ── 035c: bufferens afkast ───────────────────────────────────────────────────

ALDERS = {"id": "o2", "type": "aldersopsparing", "saldo": 300000, "aarlig_indbetaling": 0, "udbetaling_start_alder": 67}


def med_buffer(guide, **antagelser):
    g = med(guide, "branchestandard")
    return {**g, "ordninger": g["ordninger"] + [ALDERS], "antagelser": {**g["antagelser"], **antagelser}}


def test_besked_om_bufferens_afkast_ved_beloebet():
    v = regn(med_buffer(GUIDE))
    assert "BUFFER_AFKAST_BRANCHE" in {a["kode"] for a in v["hovedtal_advarsler"]}
    assert v["antagelser"]["buffer_afkast_efter_pal"] is not None


def test_eget_afkast_ingen_besked():
    v = regn(med_buffer(GUIDE, afkast_angivet=True))
    assert "BUFFER_AFKAST_BRANCHE" not in {a["kode"] for a in v["hovedtal_advarsler"]}
    assert v["antagelser"]["afkast_angivet"] is True and v["antagelser"]["buffer_afkast_efter_pal"] is None
