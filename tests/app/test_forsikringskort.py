"""Feature 034 — forsikringerne som kort med beløb efter skat. Opdigtede dækninger som i den syntetiske
rapport (031)."""
import json

import pytest

from pensionsoverblik import app
from tests.app.test_husstand_app import IDAG
from tests.app.test_oversaet import GUIDE  # Aarhus, medlem af folkekirken


def daekning(type_, selskab, skat, form, beloeb, modtager=None, til_alder=None):
    return {"type": type_, "selskab": selskab, "aftalenr": None, "skat": skat, "modtager": modtager, "form": form,
            "beloeb": beloeb, "til_alder": til_alder, "praemiefritagelse": None, "noter": []}


SYNTETISK = [
    daekning("doed", "ATP", "A", "engang", 40_000, "Ægtefælle"),
    daekning("doed", "Danica", "A", "aarraekke", 60_000, "Ægtefælle", 70),
    daekning("doed", "Testselskab", "F", "engang", 1_500_000, "Begunstiget oplyst", 67),
    daekning("erhvervsevne", "Testselskab", "S", "aarraekke", 300_000, til_alder=67),
    daekning("kritisk_sygdom", "Testselskab", "F", "engang", 150_000, til_alder=67),
    daekning("kritisk_sygdom_boern", "Testselskab", "F", "engang", 50_000),
    daekning("sundhed", "Testselskab", None, "engang", 100_000, til_alder=67),
]


def kort(daekninger=SYNTETISK, guide=GUIDE):
    r = app.forsikringer(json.dumps(guide), json.dumps(daekninger), IDAG)
    assert r["ok"], r
    return {k["id"]: k for k in r["data"]["kort"]}


def test_et_kort_pr_situation_i_fast_raekkefoelge():
    r = app.forsikringer(json.dumps(GUIDE), json.dumps(SYNTETISK), IDAG)["data"]["kort"]
    assert [k["id"] for k in r] == ["doed", "erhvervsevne", "kritisk_sygdom", "sundhed"]
    assert r[0]["titel"] == "Hvis du dør"


def test_doed_efter_afgift_og_skattefri():
    d = kort()["doed"]
    assert d["hoved"] == "engang"
    assert d["engang"]["foer_skat"] == 1_540_000
    assert d["engang"]["efter_skat"] == pytest.approx(24_000 + 1_500_000)   # ATP med 40 % afgift
    assert d["engang"]["hos_modtager"] == 0
    assert d["loebende"]["foer_skat"] == 60_000                             # ægtefællepensionen om året
    assert d["ophoer"] == {"tidligst": 67, "alle_ens": False}


def test_bjaelke_pr_selskab_efter_skat():
    d = kort()["doed"]
    assert d["selskaber"] == [{"selskab": "Testselskab", "beloeb": 1_500_000, "efter_skat": True},
                              {"selskab": "ATP", "beloeb": pytest.approx(24_000), "efter_skat": True}]


def test_skattepligtigt_til_efterladte_vises_foer_skat():
    d = kort([daekning("doed", "Pension A", "S", "engang", 1_000_000, "Nærmeste pårørende"),
              daekning("doed", "Pension B", "F", "engang", 200_000)])["doed"]
    assert d["engang"]["efter_skat"] == 200_000
    assert d["engang"]["hos_modtager"] == 1_000_000
    assert d["selskaber"][0] == {"selskab": "Pension A", "beloeb": 1_000_000, "efter_skat": False}


def test_tab_af_arbejdsevne_efter_skat_af_summen():
    # To dækninger beskattes samlet (skatten er progressiv), og nettoen fordeles efter beløbene.
    to = kort([daekning("erhvervsevne", "X", "S", "aarraekke", 200_000),
               daekning("erhvervsevne", "Y", "S", "aarraekke", 100_000)])["erhvervsevne"]
    en = kort([daekning("erhvervsevne", "X", "S", "aarraekke", 300_000)])["erhvervsevne"]
    assert to["hoved"] == "loebende"
    assert to["loebende"]["efter_skat"] == pytest.approx(en["loebende"]["efter_skat"])
    assert 0 < to["loebende"]["efter_skat"] < 300_000
    x, y = to["selskaber"]
    assert x["beloeb"] == pytest.approx(2 * y["beloeb"])


def test_kritisk_sygdom_boern_for_sig():
    k = kort()["kritisk_sygdom"]
    assert k["engang"]["efter_skat"] == 150_000 and k["boern"]["efter_skat"] == 50_000


def test_sundhed_uden_beloeb_i_hovedet():
    s = kort()["sundhed"]
    assert s["hoved"] is None and s["daekninger"][0]["selskab"] == "Testselskab"


def test_ingen_daekninger_ingen_kort():
    assert kort([]) == {}


def test_kirkeskat_foelger_borgeren():
    med = kort([daekning("erhvervsevne", "X", "S", "aarraekke", 300_000)])["erhvervsevne"]
    uden = kort([daekning("erhvervsevne", "X", "S", "aarraekke", 300_000)],
                {**GUIDE, "person": {**GUIDE["person"], "folkekirkemedlem": False}})["erhvervsevne"]
    assert uden["loebende"]["efter_skat"] > med["loebende"]["efter_skat"]
