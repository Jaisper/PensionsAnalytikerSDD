"""Feature 040 T003 — planens slutning og penge tilbage i app-laget: oversættelse pr. person, prisen og
levetidsscenarier relativt til borgerens egen slutalder."""
import json

from pensionsoverblik import app
from pensionsoverblik.oversaet import til_husstand, til_kerne
from tests.app.test_husstand_app import IDAG, PAR
from tests.app.test_oversaet import GUIDE


def med(guide, **antagelser):
    return {**guide, "antagelser": {**guide["antagelser"], **antagelser}}


def med_partner(guide, **antagelser):
    p = guide["person"]["partner"]
    return {**guide, "person": {**guide["person"], "partner": {**p, "antagelser": {**(p.get("antagelser") or {}),
                                                                                   **antagelser}}}}


def test_oversaettelse():
    _, a = til_kerne(med(GUIDE, plan_slut_alder=95, rest_ved_plan_slut=250000))
    assert a.plan_slut_alder == 95 and a.rest_ved_plan_slut == 250000
    _, a = til_kerne(GUIDE)
    assert a.plan_slut_alder is None and a.rest_ved_plan_slut == 0


def test_partneren_har_sine_egne_vaerdier():
    _, a, _, b = til_husstand(med_partner(med(PAR, plan_slut_alder=95, rest_ved_plan_slut=250000),
                                          plan_slut_alder=92, rest_ved_plan_slut=100000))
    assert (a.plan_slut_alder, a.rest_ved_plan_slut) == (95, 250000)
    assert (b.plan_slut_alder, b.rest_ved_plan_slut) == (92, 100000)
    # Gemt før 040: partneren regnes som standard, ikke med dine værdier (alderen er din egen).
    _, _, _, b = til_husstand(med(PAR, plan_slut_alder=95, rest_ved_plan_slut=250000))
    assert (b.plan_slut_alder, b.rest_ved_plan_slut) == (None, 0)


def test_fejl_i_partnerens_felt_peger_paa_partnerens_felt():
    r = app.beregn(json.dumps(med_partner(PAR, rest_ved_plan_slut=-5)), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "person.partner.antagelser.rest_ved_plan_slut"
    r = app.beregn(json.dumps(med(GUIDE, plan_slut_alder=120)), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "antagelser.plan_slut_alder"


def test_prisen_for_resten():
    uden = app.beregn(json.dumps(GUIDE), IDAG)["data"]
    assert uden["hovedtal"].get("rest") is None
    v = app.beregn(json.dumps(med(GUIDE, rest_ved_plan_slut=250000)), IDAG)["data"]
    rest = v["hovedtal"]["rest"]
    assert rest["beloeb"] == 250000 and rest["alder"] == 90
    # Resten binder de sidste år: det senere niveau falder, ikke det laveste (hovedtallet).
    assert rest["pris_maaned"] == uden["hovedtal"]["senere"]["maaned"] - v["hovedtal"]["senere"]["maaned"] > 0
    assert rest["fra_alder"] == v["hovedtal"]["senere"]["fra_alder"]


def test_prisen_pr_person_i_et_par():
    v = app.beregn(json.dumps(med_partner(PAR, rest_ved_plan_slut=200000, plan_slut_alder=95)), IDAG)["data"]
    assert v["hovedtal"].get("rest") is None
    rest = v["husstand"]["partner"]["hovedtal"]["rest"]
    assert rest["beloeb"] == 200000 and rest["alder"] == 95 and rest["pris_maaned"] > 0


def test_levetidsscenarierne_er_relative():
    s = {x["noegle"]: x for x in app.scenarier(json.dumps(med(GUIDE, plan_slut_alder=95)))}
    assert s["levetid_90"]["plan_slut_alder"] == 90 and s["levetid_100"]["plan_slut_alder"] == 100
    assert s["levetid_90"]["forskel"] == -5 and s["levetid_100"]["forskel"] == 5
    assert {x["noegle"] for x in app.scenarier(json.dumps(GUIDE)) if x["noegle"].startswith("levetid")} == {
        "levetid_85", "levetid_95"}


def test_afkastscenarier_beholder_borgerens_slutalder():
    g = json.dumps(med(GUIDE, plan_slut_alder=95))
    r = app.scenarie(g, IDAG, 0.03, 0.02)["data"]
    assert r["dig"] == app.beregn(g, IDAG)["data"]["hovedtal"]["maaned"]


def test_partneren_flyttes_lige_saa_meget():
    g = med_partner(med(PAR, plan_slut_alder=90), plan_slut_alder=88)
    r = app.scenarie(json.dumps(g), IDAG, 0.03, 0.02, 95)["data"]
    forventet = app.beregn(json.dumps(med_partner(med(PAR, plan_slut_alder=95), plan_slut_alder=93)), IDAG)["data"]
    assert r["partner"] == forventet["husstand"]["partner"]["hovedtal"]["maaned"]
    assert r["efter_plan"]["partner"] is not None


def test_efter_plan_er_aaret_efter_borgerens_egen_slutning():
    g = json.dumps(med(GUIDE, plan_slut_alder=88))
    lang = app.scenarie(g, IDAG, 0.03, 0.02, 93)["data"]
    v = app.beregn(json.dumps(med(GUIDE, plan_slut_alder=93)), IDAG)["data"]
    raekke = next(a for a in v["aar"] if a["alder"] == 89)
    assert lang["efter_plan"]["dig"] == round(raekke["netto_real"] / 12, -2)
    assert "efter_plan" not in app.scenarie(g, IDAG, 0.03, 0.02, 83)["data"]


def test_ratepension_efter_planens_slutning():
    # 040b: ratepensionen udbetales 75–84, planen slutter som 80-årig. Tabellen går til 84, men hovedtal og
    # rest hører til planen, og årene efter tæller ikke i hovedtallet.
    g = json.loads(json.dumps(GUIDE))
    g["ordninger"][0].update(udbetaling_start_alder=75, udbetaling_aar=10)
    v = app.beregn(json.dumps(med(g, plan_slut_alder=80, rest_ved_plan_slut=50000)), IDAG)["data"]
    assert v["aar"][-1]["alder"] == 84 and v["hovedtal"]["til_alder"] == 80
    assert v["hovedtal"]["rest"]["alder"] == 80
    assert any(a["kode"] == "UDBETALING_EFTER_PLAN" for a in v["hovedtal_advarsler"])
