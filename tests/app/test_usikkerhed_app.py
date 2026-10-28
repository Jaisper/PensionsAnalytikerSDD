"""Feature 018 T001 — usikkerhed om afkast og inflation (FR-001, FR-002, SC-002)."""
import json

import pytest

from pensionsoverblik import app
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_oversaet import GUIDE  # afkast 3 %, inflation 2 %


def med_antagelser(guide, afkast, inflation):
    return {**guide, "antagelser": {**guide["antagelser"], "afkast_efter_pal": afkast, "inflation": inflation}}


def test_seks_scenarier_om_borgerens_valg():
    s = {x["noegle"]: (x["afkast"], x["inflation"]) for x in app.scenarier(json.dumps(GUIDE))
         if not x["noegle"].startswith("levetid") and not x.get("stress")}
    assert s == {
        "lavere_afkast": (pytest.approx(0.02), 0.02), "hoejere_afkast": (pytest.approx(0.04), 0.02),
        "hoejere_inflation": (0.03, pytest.approx(0.025)), "lavere_inflation": (0.03, pytest.approx(0.015)),
        "ugunstigt": (pytest.approx(0.02), pytest.approx(0.025)), "gunstigt": (pytest.approx(0.04), pytest.approx(0.015)),
    }
    assert all(x["titel"] for x in app.scenarier(json.dumps(GUIDE)))


def test_aldrig_under_nul():
    s = {x["noegle"]: (x["afkast"], x["inflation"]) for x in app.scenarier(json.dumps(med_antagelser(GUIDE, 0.0, 0.0)))}
    assert s["lavere_afkast"] == (0.0, 0.0) and s["lavere_inflation"] == (0.0, 0.0)
    assert s["ugunstigt"] == (0.0, pytest.approx(0.005))


def test_scenariet_er_beregn_med_de_aendrede_antagelser():
    r = app.scenarie(json.dumps(GUIDE), IDAG, 0.02, 0.025)
    forventet = app.beregn(json.dumps(med_antagelser(GUIDE, 0.02, 0.025)), IDAG)["data"]["hovedtal"]["maaned"]
    assert r["ok"] and r["data"] == {"dig": forventet, "partner": None, "samlet": None}


def test_hoejere_afkast_giver_mere():
    lav = app.scenarie(json.dumps(GUIDE), IDAG, 0.02, 0.02)["data"]["dig"]
    hoej = app.scenarie(json.dumps(GUIDE), IDAG, 0.04, 0.02)["data"]["dig"]
    assert hoej > lav


def test_par_giver_partner_og_samlet():
    d = app.scenarie(json.dumps(PAR), IDAG, 0.03, 0.02)["data"]
    assert d["partner"] > 0 and d["samlet"] == d["dig"] + d["partner"]


def test_fejl_giver_fejl():
    slet = {**GUIDE, "person": {**GUIDE["person"], "kommune": "Atlantis"}}
    r = app.scenarie(json.dumps(slet), IDAG, 0.03, 0.02)
    assert not r["ok"] and r["fejl"]["felt"] == "kommune"


def test_levetidsscenarier():  # feature 019
    s = {x["noegle"]: x for x in app.scenarier(json.dumps(GUIDE))}
    assert s["levetid_85"]["plan_slut_alder"] == 85 and s["levetid_95"]["plan_slut_alder"] == 95
    assert s["levetid_85"]["afkast"] == 0.03 and s["levetid_85"]["inflation"] == 0.02  # dit valg
    assert all(x.get("plan_slut_alder") is None for k, x in s.items() if not k.startswith("levetid"))


def test_kortere_plan_giver_mere_og_efter_plan_er_livslang_indkomst():
    kort = app.scenarie(json.dumps(GUIDE), IDAG, 0.03, 0.02, 85)["data"]
    lang = app.scenarie(json.dumps(GUIDE), IDAG, 0.03, 0.02, 95)["data"]
    assert kort["dig"] >= lang["dig"]
    assert lang["efter_plan"]["dig"] > 0 and lang["efter_plan"]["partner"] is None
    assert "efter_plan" not in kort
    # Indkomsten efter planen er kernens netto i året efter 90 år, uden ratepension og opsparing.
    v = app.beregn(json.dumps({**GUIDE, "antagelser": {**GUIDE["antagelser"], "plan_slut_alder": 95}}), IDAG)["data"]
    raekke = next(a for a in v["aar"] if a["alder"] == 91)
    assert lang["efter_plan"]["dig"] == round(raekke["netto_real"] / 12, -2)
