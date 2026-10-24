"""T010/T018 — HTTP-API og privatliv (contracts/api.md)."""
import logging

import pytest
from fastapi.testclient import TestClient

from pensionsoverblik.api import app
from tests.app.test_oversaet import GUIDE

klient = TestClient(app)


def test_forside():
    r = klient.get("/")
    assert r.status_code == 200 and 'lang="da"' in r.text


def test_kommuner_sorteret_med_navne():
    r = klient.get("/api/kommuner").json()
    assert len(r) == 98
    assert {"noegle": "kobenhavn", "navn": "København"} in r
    assert [k["navn"] for k in r] == sorted((k["navn"] for k in r), key=str.casefold)


def test_beregn_ok():
    r = klient.post("/api/beregn", json=GUIDE)
    assert r.status_code == 200
    v = r.json()
    assert v["hovedtal"]["maaned"] > 0 and v["folkepensionsalder"] == 68


def test_beregn_feltfejl_fra_kernen():
    guide = {**GUIDE, "person": {**GUIDE["person"], "foedselsdato": "1950-01-01"}}
    r = klient.post("/api/beregn", json=guide)
    assert r.status_code == 422
    assert r.json()["felt"] == "foedselsdato" and "1955" in r.json()["besked"]


def test_beregn_feltfejl_fra_oversaettelse():
    r = klient.post("/api/beregn", json={"person": {}, "ordninger": []})
    assert r.status_code == 422 and r.json()["felt"].startswith("person.")


def test_ingen_cookies_og_ingen_input_i_logs(caplog):
    with caplog.at_level(logging.DEBUG):
        r = klient.post("/api/beregn", json=GUIDE)
    assert not r.cookies
    assert "1963-05-01" not in caplog.text and "1000000" not in caplog.text


@pytest.mark.parametrize("sti", ["/static/app.css", "/static/app.js"])
def test_statiske_filer(sti):
    assert klient.get(sti).status_code == 200
