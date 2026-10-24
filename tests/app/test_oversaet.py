"""T004 — guidedata → kernens Pensionsprofil/Antagelser."""
from datetime import date

import pytest

from pensionskerne import UgyldigtInput
from pensionsoverblik.oversaet import til_kerne

GUIDE = {
    "person": {"foedselsdato": "1963-05-01", "civilstand": "enlig", "kommune": "Aarhus",
               "folkekirkemedlem": True, "likvid_formue": 50000, "atp_aarlig": None},
    "ordninger": [{"id": "o1", "type": "ratepension", "saldo": 1000000, "aarlig_indbetaling": 0,
                   "udbetaling_start_alder": 65, "udbetaling_aar": 10, "oprettet": "2010-01-01"}],
    "antagelser": {"afkast_efter_pal": 0.03, "inflation": 0.02},
}


def test_enlig():
    profil, antagelser = til_kerne(GUIDE)
    assert profil.foedselsdato == date(1963, 5, 1)
    assert profil.folkekirkemedlem and profil.kommune == "Aarhus"
    assert profil.ordninger[0].oprettet == date(2010, 1, 1)
    assert profil.ordninger[0].udbetaling_aar == 10
    assert antagelser.afkast_efter_pal == 0.03
    assert antagelser.folkepension_opsaettelse_aar == 0


def test_partner_med_fast_indkomst_for_alle_aar():
    guide = {**GUIDE, "person": {**GUIDE["person"], "civilstand": "gift_samlevende",
                                 "partner": {"foedselsdato": "1965-02-01", "oevrig_indkomst_aar": 120000}}}
    profil, _ = til_kerne(guide)
    assert profil.partner.foedselsdato == date(1965, 2, 1)
    assert profil.partner.indkomst_pr_aar[2040].oevrig_indkomst == 120000
    assert profil.partner.indkomst_pr_aar[2026].am_pligtig_arbejdsindkomst == 0


def test_manglende_felt_giver_feltfejl():
    guide = {**GUIDE, "person": {k: v for k, v in GUIDE["person"].items() if k != "foedselsdato"}}
    with pytest.raises(UgyldigtInput) as e:
        til_kerne(guide)
    assert e.value.felt == "person.foedselsdato"


def test_ugyldig_dato_giver_feltfejl():
    guide = {**GUIDE, "ordninger": [{**GUIDE["ordninger"][0], "oprettet": "1.1.2010"}]}
    with pytest.raises(UgyldigtInput) as e:
        til_kerne(guide)
    assert e.value.felt == "ordninger[o1].oprettet"


def test_tom_streng_er_ukendt_dato():
    guide = {**GUIDE, "ordninger": [{**GUIDE["ordninger"][0], "oprettet": ""}]}
    profil, _ = til_kerne(guide)
    assert profil.ordninger[0].oprettet is None
