"""Feature 021 T003 — "Hvor skal næste krone hen?" (US1–US3, FR-001–FR-003)."""
import json

import pytest

from pensionsoverblik import app
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_loen_app import med_loen
from tests.app.test_oversaet import GUIDE  # født 1963-05-01, ratepension fra 65

NOEGLER = {"ratepension", "aldersopsparing", "ask", "bank"}


def naeste(guide, beloeb=10_000):
    r = app.naeste_krone(json.dumps(guide), IDAG, beloeb)
    assert r["ok"], r
    return r["data"]


def test_kraever_loen():
    r = app.naeste_krone(json.dumps(GUIDE), IDAG, 10_000)
    assert not r["ok"] and r["fejl"]["felt"] == "loen.aarlig"


def test_alle_alternativer_afproeves_og_sorteres():
    d = naeste(med_loen(GUIDE))
    alt = d["alternativer"]
    assert {a["noegle"] for a in alt} == NOEGLER and d["afproevet"] == len(NOEGLER)
    assert [a["maaned"] for a in alt] == sorted((a["maaned"] for a in alt), reverse=True)
    # Målet er det faste beløb i gennemsnit fra stopalderen: mindst hovedtallet (det laveste niveau).
    i_dag = app.beregn(json.dumps(med_loen(GUIDE)), IDAG)["data"]["hovedtal"]["maaned"]
    assert d["i_dag"] >= i_dag - 50                          # hovedtallet er afrundet til 100 kr.
    for a in alt:
        assert a["forskel"] == pytest.approx(a["maaned"] - d["i_dag"], abs=1)
        assert a["forskel"] > 0                              # en ekstra krone hjælper altid lidt
    assert "Afdrag" in d["kommer"]


def test_samme_pris_efter_skat_og_fradrag_nu():
    d = naeste(med_loen(GUIDE))
    rate = next(a for a in d["alternativer"] if a["noegle"] == "ratepension")
    # Prisen er det, ratepensionen koster efter skat: under beløbet, fordi der er fradrag.
    assert 0 < d["pris"] < 10_000
    assert rate["fradrag_nu_aar"] == pytest.approx(10_000 - d["pris"], abs=1)
    assert all(a["fradrag_nu_aar"] == 0 for a in d["alternativer"] if a["noegle"] != "ratepension")
    # Ratepensionen beskattes senere og nedsætter pensionstillægget; aldersopsparingen gør ingen af delene.
    alders = next(a for a in d["alternativer"] if a["noegle"] == "aldersopsparing")
    assert rate["skat_senere_maaned"] > 0 and alders["modregning_senere_maaned"] == pytest.approx(0, abs=1)


def test_ratepensionsfaelden_ved_lav_pension():
    # Lav løn og lille pension: fradraget er lille, og ratepensionen nedsætter pensionstillægget.
    lav = {**med_loen(GUIDE, {"aarlig": 280000, "stop_alder": 66}),
           "ordninger": [{**GUIDE["ordninger"][0], "saldo": 150000}]}
    d = naeste(lav)
    rate = next(a for a in d["alternativer"] if a["noegle"] == "ratepension")
    alders = next(a for a in d["alternativer"] if a["noegle"] == "aldersopsparing")
    assert alders["maaned"] > rate["maaned"]
    assert d["faelde"] is not None
    assert d["faelde"]["modregning_maaned"] == pytest.approx(rate["modregning_senere_maaned"])
    assert d["faelde"]["fradrag_aar"] == pytest.approx(rate["fradrag_nu_aar"])


def test_loftet_vises_som_fuldt_udnyttet():
    d = naeste(med_loen(GUIDE), beloeb=200_000)
    alders = next(a for a in d["alternativer"] if a["noegle"] == "aldersopsparing")
    assert alders["loft_naaet"]
    ask = next(a for a in d["alternativer"] if a["noegle"] == "ask")
    assert ask["loft_naaet"]


def test_for_et_par_maales_husstandens_samlede_beloeb():
    par = {**PAR, "person": {**PAR["person"], "loen": {"aarlig": 450000, "stop_alder": 66}}}
    d = naeste(par)
    assert d["par"]
    samlet = app.beregn(json.dumps(par), IDAG)["data"]["husstand"]["samlet"]["maaned"]
    assert d["i_dag"] >= samlet - 100                        # begge personers gennemsnit
