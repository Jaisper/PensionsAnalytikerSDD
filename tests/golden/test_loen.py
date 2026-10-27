"""Feature 017 T002 — arbejdsår og løn (US1, US2, US4, SC-001, SC-003, SC-004).

Inflation 0, så satsreguleringen er 0 og 2026-satserne gælder i alle år. Borgeren er født
1. marts 1966: 60 år i 2026 og folkepensionsalder 68.
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Loen, Ordning, Pensionsprofil, beregn
from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.loen import beskaeftigelsesfradrag, jobfradrag, seniorfradrag
from pensionskerne.regler.skat import beregn_skat
from tests.conftest import BEREGNINGSDATO

ANT = Antagelser(afkast_efter_pal=0.03, inflation=0.0)
O = Regelopslag(2026, 2026, 0.0)
RATE = Ordning("rate", "ratepension", 1_000_000, 68, oprettet=date(2010, 1, 1), udbetaling_aar=10)


def person(loen=None, *, foedt=date(1966, 3, 1), ordninger=(RATE,), opsparing=()):
    return Pensionsprofil(foedselsdato=foedt, civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=ordninger, opsparing=opsparing, loen=loen)


def regn(profil, ant=ANT):
    return beregn(profil, ant, 2026, BEREGNINGSDATO)


def kilde(aar, type_):
    return next((k for k in aar.kilder if k.type == type_), None)


def test_uden_loen_er_alt_uaendret():
    uden = regn(person())
    nul = regn(person(Loen(0)))
    assert [a.netto_i_alt for a in nul.aar] == [a.netto_i_alt for a in uden.aar]
    assert nul.aar[0].alder == uden.aar[0].alder == 68
    assert uden.jaevn_fra_alder == 68


def test_loen_giver_raekker_fra_i_dag_med_am_bidrag_og_skat():
    res = regn(person(Loen(500_000, stop_alder=64)))
    assert res.aar[0].alder == 60
    a = res.aar_ved(60)
    loen = kilde(a, "loen")
    am = 500_000 * O.v("skat.am_bidrag")
    assert loen.brutto == pytest.approx(500_000)
    # Skatten af lønnen (der er ingen anden indkomst): AM-bidrag + indkomstskat af den personlige
    # indkomst, hvor de ligningsmæssige fradrag kun nedsætter kommune- og kirkeskat.
    pi = 500_000 - am
    lmf = beskaeftigelsesfradrag(500_000, O) + jobfradrag(500_000, O) + seniorfradrag(500_000, 60, 68, O)
    skat = beregn_skat(pi, O.kommuneskat("aarhus"), 0.0, O, ligningsmaessige_fradrag=lmf).total
    assert loen.skat == pytest.approx(am + skat)
    assert a.netto_i_alt == pytest.approx(500_000 - am - skat)
    assert kilde(res.aar_ved(64), "loen") is None


def test_seniorfradraget_gives_de_to_sidste_aar():
    res = regn(person(Loen(500_000, stop_alder=68)))
    skat = {alder: kilde(res.aar_ved(alder), "loen").skat for alder in (65, 66, 67)}
    # Folkepensionsalder 68: fradraget gives som 66- og 67-årig. 1,4 % af 500.000 = 7.000 kr. > loftet.
    forskel = O.v("skat.seniorfradrag.maks") * O.kommuneskat("aarhus")
    assert skat[65] - skat[66] == pytest.approx(forskel)
    assert skat[66] == pytest.approx(skat[67])


def test_pensionsindbetaling_fradrages_og_stopper_ved_stopalderen():
    rate = replace(RATE, aarlig_indbetaling=40_000)
    tidlig = regn(person(Loen(500_000, stop_alder=62), ordninger=(rate,)))
    sen = regn(person(Loen(500_000, stop_alder=66), ordninger=(rate,)))
    # Indbetalingen fradrages i den personlige indkomst i arbejdsårene.
    assert sen.aar_ved(60).personlig_indkomst == pytest.approx(500_000 * (1 - O.v("skat.am_bidrag")) - 40_000)
    # Flere år med indbetaling giver en større ratepension.
    assert kilde(sen.aar_ved(68), "ratepension").brutto > kilde(tidlig.aar_ved(68), "ratepension").brutto


def test_udjaevningen_begynder_ved_stopalderen_og_banken_bygger_bro():
    res = regn(person(Loen(500_000, stop_alder=64), opsparing=(Aktiv("bank", 400_000),)))
    assert res.jaevn_fra_alder == 64
    for j in res.jaevn.aar:
        if j.alder < 64:
            assert j.jaevn == pytest.approx(j.normal)        # arbejdsårene udjævnes ikke
    efter = [j for j in res.jaevn.aar if j.alder >= 64]
    assert min(j.jaevn for j in efter if j.alder < 68) > 0   # banken dækker 64–67
    assert all(j.buffer_rest >= -1e-6 for j in res.jaevn.aar)
    assert res.jaevn.aar[-1].buffer_rest == pytest.approx(0, abs=1e-6)
    # Bankens afkast i arbejdsårene er kapitalindkomst og beskattes sammen med lønnen.
    assert res.aar_ved(61).kapitalindkomst > 0 and res.aar_ved(61).skat_kapitalindkomst > 0


def test_indkomsthul_uden_opsparing():
    res = regn(person(Loen(500_000, stop_alder=62)))
    hul = next(a for a in res.advarsler if a.kode == "INDKOMSTHUL")
    assert hul.aldre == (62, 67)
    assert all(j.jaevn == pytest.approx(0, abs=1e-6) for j in res.jaevn.aar if 62 <= j.alder <= 67)


def test_folkepensionist_med_loen_beholder_tillaegget_men_tillaegsprocenten_falder():
    foedt = date(1958, 2, 1)  # 68 år, folkepensionist
    uden = regn(person(foedt=foedt, ordninger=()))
    med = regn(person(Loen(250_000, stop_alder=72), foedt=foedt, ordninger=()))
    for alder in (69, 70):
        u, m = uden.aar_ved(alder), med.aar_ved(alder)
        assert kilde(m, "pensionstillaeg").brutto == pytest.approx(kilde(u, "pensionstillaeg").brutto)  # L 117
        assert m.indtaegtsgrundlag == pytest.approx(u.indtaegtsgrundlag)
        assert m.tillaegsprocent < u.tillaegsprocent                    # løn over 122.004 kr.
    assert kilde(med.aar_ved(73), "loen") is None


def test_deltid_efter_stop():
    res = regn(person(Loen(500_000, stop_alder=64, deltid_aarlig=150_000, deltid_til_alder=67)))
    assert kilde(res.aar_ved(64), "loen").brutto == pytest.approx(150_000)
    assert kilde(res.aar_ved(66), "loen").brutto == pytest.approx(150_000)
    assert kilde(res.aar_ved(67), "loen") is None
    assert res.jaevn_fra_alder == 64
