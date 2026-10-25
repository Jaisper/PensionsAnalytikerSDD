"""Feature 009 T008 — kapitalpensionens felter gennem oversættelse, grænser og visning."""
import json
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, beregn
from pensionsoverblik import app
from pensionsoverblik.oversaet import til_kerne
from pensionsoverblik.visning import byg_visning, graenser
from tests.app.test_oversaet import GUIDE
from tests.conftest import BEREGNINGSDATO, enlig_profil

KAP = {"id": "k1", "type": "kapitalpension", "saldo": 600000, "aarlig_indbetaling": 0, "udbetaling_start_alder": 65,
       "oprettet": "2000-01-01"}


def test_oversaet_standard_er_engangs_uden_betalt_afgift():
    profil, _ = til_kerne({**GUIDE, "ordninger": [KAP]})
    o = profil.ordninger[0]
    assert o.udbetalingsform == "engangs" and o.afgift_betalt is False


def test_oversaet_former_og_afgift():
    profil, _ = til_kerne({**GUIDE, "ordninger": [{**KAP, "udbetalingsform": "portioner", "udbetaling_aar": 6,
                                                  "afgift_betalt": True}]})
    o = profil.ordninger[0]
    assert (o.udbetalingsform, o.udbetaling_aar, o.afgift_betalt) == ("portioner", 6, True)


def test_ugyldig_form_giver_feltfejl():
    """Kernen validerer (ét sted); fejlen kommer som feltfejl gennem indgangen."""
    r = app.beregn(json.dumps({**GUIDE, "ordninger": [{**KAP, "udbetalingsform": "lotteri"}]}), "2026-10-25")
    assert r["ok"] is False and r["fejl"]["felt"] == "ordninger[k1].udbetalingsform"


def test_graenser_for_kapitalpension():
    kap = Ordning("k1", "kapitalpension", 1, 65, oprettet=date(2000, 1, 1))
    betalt = Ordning("k2", "kapitalpension", 1, 65, oprettet=date(2000, 1, 1), afgift_betalt=True)
    g = graenser(enlig_profil(ordninger=(kap, betalt)), 2026)
    assert g["ordninger"]["k1"]["seneste"] == 80  # pensionsudbetalingsalder 60 + 20 år
    assert g["ordninger"]["k1"]["kan_omlaegges"] is True
    assert g["ordninger"]["k2"]["kan_omlaegges"] is False
    assert "seneste" not in g["ordninger"].get("k3", {})


def test_visning_har_kapitalindkomst_i_aarstabellen():
    kap = Ordning("k1", "kapitalpension", 1_000_000, 69, oprettet=date(2000, 1, 1))
    res = beregn(enlig_profil(foedselsdato=date(1958, 2, 1), ordninger=(kap,)), Antagelser(), 2026, BEREGNINGSDATO)
    v = byg_visning(res)
    for raekke, a in zip(v["aar"], res.aar):
        assert raekke["kapitalindkomst"] == a.kapitalindkomst
        assert raekke["skat_kapitalindkomst"] == a.skat_kapitalindkomst
    assert any(r["kapitalindkomst"] > 0 for r in v["aar"])
    # Tabellens kolonne "Skat af buffer pr. md." i dagens kroner.
    assert v["graf"]["skat_buffer"] == [a.skat_kapitalindkomst * a.realfaktor / 12 for a in res.aar]


def test_portioner_i_grafens_engangsbeloeb():
    guide = {**GUIDE, "ordninger": [{**KAP, "udbetalingsform": "portioner", "udbetaling_aar": 5}]}
    v = app.beregn(json.dumps(guide), "2026-10-25")["data"]
    assert [e["alder"] for e in v["graf"]["engangs"]] == [65, 66, 67, 68, 69]
    assert {e["ordning_id"] for e in v["graf"]["engangs"]} == {"k1"}


def test_optimer_beskriver_formaendring():
    guide = {**GUIDE, "ordninger": [{**KAP, "udbetaling_start_alder": 70}]}
    d = app.optimer(json.dumps(guide), "2026-10-25")["data"]
    ordning = d["plan"]["ordninger"]["k1"]
    assert {"udbetaling_start_alder", "udbetalingsform"} <= set(ordning)
    for a in d["aendringer"]:
        if a["felt"] == "form":
            assert set(a["fra"]) == {"form", "aar"} and set(a["til"]) == {"form", "aar"}
