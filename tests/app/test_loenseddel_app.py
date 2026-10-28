"""Feature 017c T006 — lønsedlen gennem oversættelse, PDF-hint og næste krone (FR-003, FR-005, FR-006)."""
import json

from pensionskerne.register.opslag import Regelopslag
from pensionsoverblik import app
from pensionsoverblik.oversaet import til_kerne
from tests.app.test_husstand_app import IDAG
from tests.app.test_loen_app import med_loen
from tests.app.test_oversaet import GUIDE
from tests.app.test_pdf_omsaet import guide as pdf_guide, ordning as pdf_ordning

SEDDEL = {"aarlig": 480000, "stop_alder": 65, "pension_eget": 0.04, "pension_firma": 0.08}


def fra_loen(guide):
    return {**guide, "ordninger": [{**o, "fra_loen": True} for o in guide["ordninger"]]}


def test_procenter_og_fra_loen_oversaettes():
    profil, _ = til_kerne(fra_loen(med_loen(GUIDE, SEDDEL)))
    assert (profil.loen.pension_eget, profil.loen.pension_firma) == (0.04, 0.08)
    assert all(o.fra_loen for o in profil.ordninger)
    assert not any(o.fra_loen for o in til_kerne(GUIDE)[0].ordninger)


def test_procenter_uden_ordning_fra_loennen_giver_feltfejl():
    r = app.beregn(json.dumps(med_loen(GUIDE, SEDDEL)), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "loen.pension_firma"


def test_nettoloennen_falder_med_egen_andel_ikke_med_firmaets():
    def maaned(loen):
        return app.beregn(json.dumps(fra_loen(med_loen(GUIDE, loen))), IDAG)["data"]["loen"]["maaned"]
    uden = maaned({**SEDDEL, "pension_eget": 0, "pension_firma": 0})
    # Firmaets pension øger kun grundlaget for beskæftigelsesfradraget lidt (LL § 9 J, stk. 1).
    assert 0 <= maaned({**SEDDEL, "pension_eget": 0}) - uden <= 100
    assert maaned(SEDDEL) < uden


def test_rapporten_giver_indbetaling_pr_maaned_foer_am_og_fra_loen():
    am = Regelopslag(2026, 2026, 0.0).v("skat.am_bidrag")
    g = pdf_guide(pdf_ordning(aarlig_indbetaling=46_000), pdf_ordning(aarlig_indbetaling=None, aftalenr="456"))
    assert g["indbetaling_maaned"] == round(46_000 / (1 - am) / 12)
    assert [o["fra_loen"] for o in g["ordninger"]] == [True, False]
    assert pdf_guide(pdf_ordning(aarlig_indbetaling=0))["indbetaling_maaned"] is None


def test_naeste_krone_med_loensedlen_giver_det_fulde_beloeb_til_det_nye_alternativ():
    """Næste krones nye ordning har ikke `fra_loen`, så den fordeles ikke sammen med lønnens pension."""
    r = app.naeste_krone(json.dumps(fra_loen(med_loen(GUIDE, SEDDEL))), IDAG, 12000)
    assert r["ok"], r
    alt = {a["noegle"]: a for a in r["data"]["alternativer"]}
    assert alt["ratepension"]["forskel"] > 0
