"""Feature 017 T003 — løn gennem oversættelse, visning og "Hvornår kan jeg stoppe?" (US3)."""
import json

import pytest

from pensionsoverblik import app
from pensionsoverblik.oversaet import til_husstand, til_kerne
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_oversaet import GUIDE  # født 1963-05-01, ratepension fra 65

LOEN = {"aarlig": 450000, "stop_alder": 65}


def med_loen(guide, loen=LOEN):
    return {**guide, "person": {**guide["person"], "loen": loen}}


def test_loen_oversaettes():
    profil, _ = til_kerne(med_loen(GUIDE, {**LOEN, "deltid_aarlig": 100000, "deltid_til_alder": 68}))
    assert (profil.loen.aarlig, profil.loen.stop_alder) == (450000, 65)
    assert (profil.loen.deltid_aarlig, profil.loen.deltid_til_alder) == (100000, 68)
    assert til_kerne(GUIDE)[0].loen is None


def test_partnerens_loen():
    par = {**PAR, "person": {**PAR["person"], "partner": {**PAR["person"]["partner"], "profil": {
        **PAR["person"]["partner"]["profil"], "loen": {"aarlig": 300000, "stop_alder": 64}}}}}
    _, _, b, _ = til_husstand(par)
    assert b.loen.aarlig == 300000


def test_feltfejl_peger_paa_loennen():
    r = app.beregn(json.dumps(med_loen(GUIDE, {"aarlig": -1})), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "loen.aarlig"


def test_visningen_har_et_loenkort_og_hovedtal_fra_stopalderen():
    v = app.beregn(json.dumps(med_loen(GUIDE)), IDAG)["data"]
    assert any(k["noegle"] == "loen" for k in v["kort"])
    assert v["hovedtal"]["fra_alder"] == 65
    g = v["graf"]
    i65 = g["aldre"].index(65)
    assert all(x is None for x in g["jaevn"][:i65]) and g["jaevn"][i65] is not None


def test_hvornaar_kan_jeg_stoppe():
    guide = json.dumps(med_loen(GUIDE))
    lavt = app.stopalder(guide, IDAG, 1000)["data"]
    assert lavt["kunne"] and lavt["maaned"] >= 1000
    assert lavt["afproevet"] == lavt["til"] - lavt["fra"] + 1
    assert lavt["fra"] == 2026 - 1963
    # Det tidligste: en alder før giver mindre end ønsket.
    hoej = app.stopalder(guide, IDAG, 10**7)["data"]
    assert not hoej["kunne"] and hoej["bedste"]["maaned"] > 0


def test_hvornaar_kan_jeg_stoppe_kraever_loen():
    r = app.stopalder(json.dumps(GUIDE), IDAG, 10000)
    assert not r["ok"] and r["fejl"]["felt"] == "loen.aarlig"
