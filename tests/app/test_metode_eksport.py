"""Feature 020d — metodesiden (US4) og eksport af regnestykket (US6)."""
import csv
import io
import json
import re

from pensionskerne import register
from pensionsoverblik import app
from pensionsoverblik.forklaring import katalog
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_oversaet import GUIDE


def test_metoden_kraever_ingen_data_og_viser_hele_registret():
    m = app.metode()
    assert m["forklaringer"] == katalog()
    assert m["satsaar"] == max(register.satsaar())
    assert {s["id"] for s in m["satser"]} == {p.id for p in register.poster(m["satsaar"])}
    assert all({"id", "vaerdi", "enhed", "kilde", "status"} <= set(s) for s in m["satser"])
    assert {f["id"] for f in m["forenklinger"]} == {f.id for f in register.forenklinger()}
    json.dumps(m, allow_nan=False)


def test_eksport_json_og_csv():
    r = app.eksport(json.dumps(GUIDE), IDAG)
    assert r["ok"]
    d = r["data"]
    assert d["filnavn"] == f"pensionsoverblik-{IDAG}"
    data = json.loads(d["json"])
    assert {"satsaar", "beregnet", "input", "antagelser", "satser", "forenklinger", "hovedtal", "aar"} <= set(data)
    assert data["input"] == GUIDE and data["aar"][0]["detaljer"]["skat"]
    raekker = list(csv.reader(io.StringIO(d["csv"]), delimiter=";"))
    assert raekker[0][0] == "Alder" and len(raekker) == len(data["aar"]) + 1
    assert all(len(r) == len(raekker[0]) for r in raekker)


def test_eksport_for_et_par_har_begge():
    data = json.loads(app.eksport(json.dumps(PAR), IDAG)["data"]["json"])
    assert data["partner"]["aar"] and data["partner"]["hovedtal"]


def test_eksport_indeholder_ingen_cpr_navne_eller_aftalenumre():
    d = app.eksport(json.dumps(GUIDE), IDAG)["data"]

    def noegler(x):
        if isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from noegler(v)
        elif isinstance(x, list):
            for v in x:
                yield from noegler(v)

    assert not {k for k in noegler(json.loads(d["json"])) if re.search(r"cpr|navn|aftale|police", k, re.I)}
    assert not re.search(r"(?<![\d.])\d{6}-\d{4}(?!\d)", d["json"] + d["csv"])  # CPR med bindestreg


def test_eksport_fejl_giver_feltfejl():
    r = app.eksport(json.dumps({**GUIDE, "person": {**GUIDE["person"], "kommune": "Atlantis"}}), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "kommune"
