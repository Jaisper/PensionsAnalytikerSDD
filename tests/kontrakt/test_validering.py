"""T007 — inputvalidering (FR-003): fejl med korrekt felt, aldrig et delvist resultat."""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, Partner, UgyldigtInput, beregn
from tests.conftest import BEREGNINGSDATO, enlig_profil


def fejlfelt(profil, antagelser=Antagelser(), satsaar=2026):
    with pytest.raises(UgyldigtInput) as e:
        beregn(profil, antagelser, satsaar, BEREGNINGSDATO)
    return e.value.felt


def test_foedt_foer_1955():
    assert fejlfelt(enlig_profil(foedselsdato=date(1954, 12, 31))) == "foedselsdato"
    # Født 1.1.–30.6.1955 har folkepensionsalder 66½ (§ 1 a) og er uden for scope
    assert fejlfelt(enlig_profil(foedselsdato=date(1955, 6, 30))) == "foedselsdato"


def test_ukendt_satsaar():
    assert fejlfelt(enlig_profil(), satsaar=2019) == "satsaar"


def test_ukendt_kommune():
    assert fejlfelt(enlig_profil(kommune="Atlantis")) == "kommune"


def test_gift_uden_partner():
    assert fejlfelt(enlig_profil(civilstand="gift_samlevende")) == "partner"


def test_negativ_formue():
    assert fejlfelt(enlig_profil(likvid_formue=-1)) == "likvid_formue"


def test_negativ_saldo():
    o = Ordning("x", "ratepension", -5, 65, oprettet=date(2010, 1, 1))
    assert fejlfelt(enlig_profil(ordninger=(o,))) == "ordninger[x].saldo"


def test_dublerede_ids():
    o = Ordning("x", "livsvarig", 1, 67, oprettet=date(2010, 1, 1))
    assert fejlfelt(enlig_profil(ordninger=(o, o))) == "ordninger[x]"


def test_ratepension_under_10_aar():
    o = Ordning("x", "ratepension", 1, 65, oprettet=date(2010, 1, 1), udbetaling_aar=9)
    assert fejlfelt(enlig_profil(ordninger=(o,))) == "ordninger[x].udbetaling_aar"


def test_ratepension_sidste_rate_for_sent():
    # fp 68, oprettet 2010 → udbetalingsalder 63 → sidste rate senest som 93-årig
    o = Ordning("x", "ratepension", 1, 85, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    assert fejlfelt(enlig_profil(ordninger=(o,))) == "ordninger[x].udbetaling_aar"


def test_start_foer_lovlig_alder():
    # oprettet 2020 → fp 68 − 3 = 65
    o = Ordning("x", "ratepension", 1, 64, oprettet=date(2020, 1, 1))
    assert fejlfelt(enlig_profil(ordninger=(o,))) == "ordninger[x].udbetaling_start_alder"


def test_opsaettelse_over_10_aar():
    assert fejlfelt(enlig_profil(), Antagelser(folkepension_opsaettelse_aar=11)) == \
        "antagelser.folkepension_opsaettelse_aar"


def test_partner_foedt_foer_1955():
    p = Partner(date(1950, 1, 1))
    assert fejlfelt(enlig_profil(civilstand="gift_samlevende", partner=p)) == "partner.foedselsdato"


def test_opsparing_valideres():  # feature 013
    from pensionskerne import Aktiv
    assert fejlfelt(enlig_profil(opsparing=(Aktiv("b", -1),))) == "opsparing[b].saldo"
    assert fejlfelt(enlig_profil(opsparing=(Aktiv("b", 1, type="aktier"),))) == "opsparing[b].type"
    # 013b: gevinst kun på depot og højst værdien; løbende indskud kun på ASK og kun med løn.
    assert fejlfelt(enlig_profil(opsparing=(Aktiv("b", 1, urealiseret_gevinst=1),))) == "opsparing[b].urealiseret_gevinst"
    assert fejlfelt(enlig_profil(opsparing=(Aktiv("d", 1, type="depot", urealiseret_gevinst=2),))) \
        == "opsparing[d].urealiseret_gevinst"
    assert fejlfelt(enlig_profil(opsparing=(Aktiv("a", 1, type="ask", aarligt_indskud=1000),))) \
        == "opsparing[a].aarligt_indskud"  # kræver løn
    assert fejlfelt(enlig_profil(opsparing=(Aktiv("b", 1), Aktiv("b", 2)))) == "opsparing[b]"
