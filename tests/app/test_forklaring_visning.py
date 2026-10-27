"""Feature 020 — visningens data til "Dit år" (US2) og forklaringen af hovedtallet (US1)."""
import json

import pytest

from pensionsoverblik import app
from tests.app.test_husstand_app import IDAG
from tests.app.test_oversaet import GUIDE  # ratepension fra 65 i 10 år


@pytest.fixture(scope="module")
def v():
    return app.beregn(json.dumps(GUIDE), IDAG)["data"]


def test_hvert_aar_har_kilder_og_detaljer_der_afstemmer(v):
    for a in v["aar"]:
        assert sum(k["netto"] for k in a["kilder"]) == pytest.approx(a["netto"], abs=0.01)
        assert all(k["titel"] for k in a["kilder"])
        d = a["detaljer"]
        typer = sum(d["skat"][k] for k in ("bundskat", "kommuneskat", "kirkeskat", "mellemskat", "topskat", "toptopskat"))
        sum_ = typer - d["skat"]["skatteloft_nedslag"] - d["skat"]["aegtefaelle_nedsaettelse"] + d["am_bidrag"]
        if a["skat"] + a["skat_kapitalindkomst"] > 0:
            assert sum_ == pytest.approx(a["skat"] + a["skat_kapitalindkomst"], abs=0.01)
        assert {"jaevn", "til_opsparing", "fra_opsparing"} <= set(a)


def test_aendringen_naevner_den_stoerste_aarsag(v):
    # Ratepensionen udbetales 65–74 år. Som 75-årig falder den bort.
    a75 = next(a for a in v["aar"] if a["alder"] == 75)
    assert a75["aendring"]["titel"] == "Ratepension" and a75["aendring"]["maaned"] < 0
    foerste = v["aar"][0]
    assert foerste["aendring"] is None


def test_hovedtallets_forklaring(v):
    f = v["hovedtal"]["forklaring"]
    assert 1 <= len(f["drivere"]) <= 3
    assert all(d["titel"] and d["maaned"] > 0 for d in f["drivere"])
    assert f["drivere"] == sorted(f["drivere"], key=lambda d: -d["maaned"])
    assert f["iterationer"] >= 1
