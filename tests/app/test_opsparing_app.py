"""Feature 013 T004 — opsparing uden for pension gennem oversættelse, visning og indgang."""
import json

import pytest

from pensionsoverblik import app
from pensionsoverblik.oversaet import til_husstand, til_kerne
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_oversaet import GUIDE

BANK = {"id": "bank", "type": "bank", "saldo": 200000, "i_plan": False}


def med_opsparing(guide, *aktiver):
    return {**guide, "person": {**guide["person"], "opsparing": list(aktiver)}}


def test_opsparing_oversaettes_til_aktiver():
    profil, _ = til_kerne(med_opsparing(GUIDE, BANK, {"id": "b2", "saldo": 5000}))
    a, b = profil.opsparing
    assert (a.id, a.type, a.saldo, a.i_plan) == ("bank", "bank", 200000, False)
    assert (b.type, b.i_plan) == ("bank", True)  # standard: bank, bruges i planen
    assert profil.likvid_formue == 50000          # det gamle felt bevarer sin betydning


def test_partnerens_opsparing_er_partnerens_egen():
    par = {**PAR, "person": {**PAR["person"], "opsparing": [BANK], "partner": {
        **PAR["person"]["partner"], "profil": {**PAR["person"]["partner"]["profil"],
                                               "opsparing": [{"id": "p-bank", "saldo": 70000}]}}}}
    a, _, b, _ = til_husstand(par)
    assert [x.id for x in a.opsparing] == ["bank"] and [x.id for x in b.opsparing] == ["p-bank"]


def test_feltfejl_peger_paa_opsparingen():
    r = app.beregn(json.dumps(med_opsparing(GUIDE, {**BANK, "saldo": -1})), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "opsparing[bank].saldo"


def test_visningen_viser_formuen_i_dagens_kroner():
    v = app.beregn(json.dumps(med_opsparing(GUIDE, BANK)), IDAG)["data"]
    f = v["formue"]
    n = len(f["aldre"])
    assert n and len(f["i_plan"]) == n and len(f["uden_for_plan"]) == n
    assert f["aldre"][0] == 2026 - 1963                     # fra i dag
    assert f["rest_alder"] == f["aldre"][-1]
    assert f["rest"] == pytest.approx(f["i_plan"][-1] + f["uden_for_plan"][-1])
    assert f["uden_for_plan"][-1] > 200000                  # urørt: vokser også i dagens kroner (afkast > inflation)
    json.dumps(v, allow_nan=False)


def test_ingen_formue_uden_opsparing_og_ordninger():
    # Med ordninger kan udjævningen selv spare op (bufferen), og så er der en formue at vise.
    guide = {**GUIDE, "ordninger": [], "person": {**GUIDE["person"], "likvid_formue": 0}}
    assert app.beregn(json.dumps(guide), IDAG)["data"]["formue"] is None


def test_samlet_viser_husstandens_formue():
    par = {**PAR, "person": {**PAR["person"], "opsparing": [BANK], "partner": {
        **PAR["person"]["partner"], "profil": {**PAR["person"]["partner"]["profil"],
                                               "opsparing": [{"id": "p-bank", "saldo": 70000, "i_plan": False}]}}}}
    v = app.beregn(json.dumps(par), IDAG)["data"]
    s = v["husstand"]["samlet"]["formue"]
    assert s["rest"] == pytest.approx(v["formue"]["rest"] + v["husstand"]["partner"]["formue"]["rest"])
    assert len(s["kalenderaar"]) == len(s["i_alt"])
