"""Feature 020b — forklaring af præsentationen, kortene og ordlisten (US3, FR-002, FR-006, FR-009),
og data til skifteren mellem dagens kroner og årets kroner."""
import json

import pytest

from pensionsoverblik import app
from pensionsoverblik.forklaring import katalog
from pensionsoverblik.katalog import KORT
from tests.app.test_forklaringer import BELOEB, LANGE_TAL, NIVEAUER, lix
from tests.app.test_husstand_app import IDAG
from tests.app.test_oversaet import GUIDE

VISNINGER = ("hovedtal", "graf", "tidslinje", "opsparingsgraf", "faner", "statusikoner", "usikkerhed", "beloeb")


def test_hver_visning_har_et_laesevejledningsemne():
    visninger = {v for e in katalog()["emner"] for v in e.get("visninger", [])}
    assert set(VISNINGER) <= visninger


def test_hvert_kort_har_mindst_et_emne():
    kort = {k for e in katalog()["emner"] for k in e.get("kort", [])}
    assert set(KORT) | {"engangsbeloeb"} <= kort


def test_ordlisten_har_tre_niveauer_klarsprog_og_ingen_beloeb():
    ord_ = katalog()["ordliste"]
    assert len(ord_) >= 12 and len({o["ord"] for o in ord_}) == len(ord_)
    for o in ord_:
        for n in NIVEAUER:
            assert o[n].strip() and not BELOEB.search(o[n]), (o["ord"], n)
        assert not LANGE_TAL.search(o["niveau1"] + o["niveau2"]), o["ord"]
        assert lix(o["niveau1"]) < 35, (o["ord"], round(lix(o["niveau1"]), 1))


def test_grafen_har_realfaktor_pr_alder():
    g = app.beregn(json.dumps(GUIDE), IDAG)["data"]["graf"]
    assert len(g["realfaktor"]) == len(g["aldre"])
    v = app.beregn(json.dumps(GUIDE), IDAG)["data"]
    pr_alder = {a["alder"]: a["realfaktor"] for a in v["aar"]}
    for alder, f in zip(g["aldre"], g["realfaktor"]):
        assert f == pytest.approx(pr_alder.get(alder, 1.0))


def test_formuen_har_realfaktor():
    guide = {**GUIDE, "person": {**GUIDE["person"], "opsparing": [{"id": "bank", "saldo": 100000, "i_plan": False}]}}
    f = app.beregn(json.dumps(guide), IDAG)["data"]["formue"]
    assert len(f["realfaktor"]) == len(f["aldre"]) and f["realfaktor"][0] == pytest.approx(1.0)
