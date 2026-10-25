"""Feature 012 T005 — husstanden gennem oversættelse og indgang (FR-005)."""
import json

import pytest

from pensionsoverblik import app
from pensionsoverblik.oversaet import til_husstand, til_kerne
from tests.app.test_oversaet import GUIDE

IDAG = "2026-10-25"

PARTNER_PROFIL = {
    "ordninger": [{"id": "p1", "type": "ratepension", "saldo": 900000, "aarlig_indbetaling": 0,
                   "udbetaling_start_alder": 66, "udbetaling_aar": 10, "oprettet": "2010-01-01"}],
    "atp_aarlig": 18000, "folkekirkemedlem": False, "folkepension_opsaettelse_aar": 0,
}
PAR = {**GUIDE, "person": {**GUIDE["person"], "civilstand": "gift",
                           "partner": {"foedselsdato": "1965-02-01", "profil": PARTNER_PROFIL}}}


def test_overslag_er_uaendret_og_giver_ingen_husstand():
    guide = {**GUIDE, "person": {**GUIDE["person"], "civilstand": "samlevende",
                                 "partner": {"foedselsdato": "1965-02-01", "oevrig_indkomst_aar": 120000}}}
    assert til_husstand(guide) is None
    r = app.beregn(json.dumps(guide), IDAG)
    assert r["ok"] and "husstand" not in r["data"]


def test_gammel_civilstand_virker_stadig():
    guide = {**GUIDE, "person": {**GUIDE["person"], "civilstand": "gift_samlevende",
                                 "partner": {"foedselsdato": "1965-02-01", "oevrig_indkomst_aar": 0}}}
    assert app.beregn(json.dumps(guide), IDAG)["ok"]


def test_til_husstand_bygger_partnerens_profil():
    a, ant_a, b, ant_b = til_husstand(PAR)
    assert b.foedselsdato.isoformat() == "1965-02-01" and b.civilstand == "gift"
    assert b.kommune == a.kommune and b.likvid_formue == a.likvid_formue  # fælles for husstanden
    assert [o.id for o in b.ordninger] == ["p1"] and b.atp_aarlig == 18000
    assert ant_b.afkast_efter_pal == ant_a.afkast_efter_pal and ant_b.folkepension_opsaettelse_aar == 0


def test_beregn_giver_partner_og_samlet():
    r = app.beregn(json.dumps(PAR), IDAG)
    assert r["ok"]
    v = r["data"]
    h = v["husstand"]
    p = h["partner"]
    s = h["samlet"]
    assert p["hovedtal"]["maaned"] > 0 and "graenser" in p
    assert s["maaned"] == v["hovedtal"]["maaned"] + p["hovedtal"]["maaned"]
    assert s["dig"]["maaned"] == v["hovedtal"]["maaned"] and s["partner"]["maaned"] == p["hovedtal"]["maaned"]
    n = len(s["kalenderaar"])
    assert all(len(s[k]) == n for k in ("netto_dig", "netto_partner", "jaevn", "alder_dig", "alder_partner"))
    assert s["kalenderaar"] == sorted(s["kalenderaar"])
    assert s["alder_dig"][0] == s["kalenderaar"][0] - 1963 and s["alder_partner"][0] == s["kalenderaar"][0] - 1965
    json.dumps(r, allow_nan=False)


def test_partnerens_feltfejl_peger_paa_partnerens_felt():
    slet = {**PAR, "person": {**PAR["person"], "partner": {**PAR["person"]["partner"], "profil": {
        **PARTNER_PROFIL, "ordninger": [{**PARTNER_PROFIL["ordninger"][0], "udbetaling_start_alder": 40}]}}}}
    r = app.beregn(json.dumps(slet), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "ordninger[p1].udbetaling_start_alder"
    uden_dato = {**PAR, "person": {**PAR["person"], "partner": {"profil": PARTNER_PROFIL}}}
    r = app.beregn(json.dumps(uden_dato), IDAG)
    assert not r["ok"] and r["fejl"]["felt"] == "person.partner.foedselsdato"


def test_optimer_partneren_holder_dig_fast():
    d = app.optimer(json.dumps(PAR), IDAG, None, "partner")["data"]
    assert set(d["plan"]["ordninger"]) <= {"p1"}
    assert all(a["id"] in ("p1", "folkepension") for a in d["aendringer"])


def test_optimer_dig_med_partner():
    d = app.optimer(json.dumps(PAR), IDAG, None, "dig")["data"]
    assert set(d["plan"]["ordninger"]) <= {"o1"}
