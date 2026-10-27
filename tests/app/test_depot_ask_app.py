"""Feature 013b T005 — frit depot og aktiesparekonto gennem oversættelse, visning og eksport."""
import json

from pensionsoverblik import app
from pensionsoverblik.oversaet import til_kerne
from tests.app.test_husstand_app import IDAG
from tests.app.test_opsparing_app import med_opsparing
from tests.app.test_oversaet import GUIDE

DEPOT = {"id": "depot", "type": "depot", "saldo": 300000, "urealiseret_gevinst": 120000}
ASK = {"id": "ask", "type": "ask", "saldo": 100000, "i_plan": False}


def test_depot_og_ask_oversaettes():
    profil, _ = til_kerne(med_opsparing(GUIDE, DEPOT, ASK, {"id": "d2", "type": "depot", "saldo": 1000,
                                                             "urealiseret_gevinst": ""}))
    d, a, d2 = profil.opsparing
    assert (d.type, d.saldo, d.urealiseret_gevinst, d.i_plan) == ("depot", 300000, 120000, True)
    assert (a.type, a.i_plan, a.aarligt_indskud) == ("ask", False, 0)
    assert d2.urealiseret_gevinst is None       # tomt felt: antagelsens andel


def test_feltfejl_peger_paa_gevinsten():
    r = app.beregn(json.dumps(med_opsparing(GUIDE, {**DEPOT, "urealiseret_gevinst": 400000})), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "opsparing[depot].urealiseret_gevinst"


def test_indskud_uden_loen_giver_feltfejl():
    r = app.beregn(json.dumps(med_opsparing(GUIDE, {**ASK, "aarligt_indskud": 10000})), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "opsparing[ask].aarligt_indskud"


def test_visningen_har_aktieindkomst_og_skat_af_opsparing():
    v = app.beregn(json.dumps(med_opsparing(GUIDE, DEPOT, ASK)), IDAG)["data"]
    assert sum(a["aktieindkomst"] for a in v["aar"]) > 0
    assert all(a["skat_aktieindkomst"] >= 0 and a["skat_aktiesparekonto"] >= 0 for a in v["aar"])
    # Grafens skat af opsparing er summen af de tre skatter pr. måned i dagens kroner.
    g = v["graf"]
    i = g["aldre"].index(v["aar"][0]["alder"])
    a = v["aar"][0]
    forventet = (a["skat_kapitalindkomst"] + a["skat_aktieindkomst"] + a["skat_aktiesparekonto"]) * a["realfaktor"] / 12
    assert g["skat_buffer"][i] == forventet
    ids = {f["id"] for f in v["forenklinger"]}
    assert "aktieafkast_som_kursgevinst" in ids


def test_eksporten_har_kolonnerne_for_aktier():
    r = app.eksport(json.dumps(med_opsparing(GUIDE, DEPOT, ASK)), IDAG)
    assert r["ok"]
    hoved = r["data"]["csv"].splitlines()[0]
    assert "Aktieindkomst" in hoved and "Skat af aktiesparekonto" in hoved


def test_traekraekkefoelgen_kan_angives():
    guide = {**med_opsparing(GUIDE, DEPOT), "antagelser": {"traekraekkefoelge": ["depot", "bank", "ask"]}}
    _, ant = til_kerne(guide)
    assert ant.traekraekkefoelge == ("depot", "bank", "ask")
    r = app.beregn(json.dumps({**guide, "antagelser": {"traekraekkefoelge": ["aktier"]}}), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "antagelser.traekraekkefoelge"
