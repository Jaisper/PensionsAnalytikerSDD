"""Feature 009 T004 — kapitalpensionens udbetalingsformer (US1–US3).

Golden cases med afkast 0 og inflation 0, så tallene kan regnes i hånden. Personen er født
1.5.1963 (folkepensionsalder 68). Kapitalpensionen er oprettet før 2007, så
pensionsudbetalingsalderen er 60 år, og sidste udbetaling skal ligge senest som 80-årig
(PBL § 25, stk. 1, nr. 7: 20 år efter).
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, UgyldigtInput, beregn
from tests.conftest import BEREGNINGSDATO, enlig_profil

NUL = Antagelser(afkast_efter_pal=0.0, inflation=0.0)
KAP = Ordning("kap", "kapitalpension", 600_000, 65, oprettet=date(2000, 1, 1))


def res(ordning, antagelser=NUL):
    return beregn(enlig_profil(ordninger=(ordning,)), antagelser, 2026, BEREGNINGSDATO)


def kilde(r, alder, kid):
    a = next(x for x in r.aar if x.alder == alder)
    return next((k for k in a.kilder if k.kilde_id == kid), None)


# ── US1: afgiften er allerede betalt ──────────────────────────────────────────────────────────

def test_engangsbeloeb_med_40_procent_afgift():
    r = res(KAP)
    assert [(e.alder, e.netto) for e in r.engangsbeloeb] == [(65, pytest.approx(360_000))]


def test_afgift_betalt_er_skattefri():
    r = res(replace(KAP, afgift_betalt=True))
    assert [(e.alder, e.netto) for e in r.engangsbeloeb] == [(65, pytest.approx(600_000))]


def test_afgift_betalt_kan_ikke_omlaegges():
    for form in ("ratepension", "livsvarig"):
        with pytest.raises(UgyldigtInput) as e:
            res(replace(KAP, afgift_betalt=True, udbetalingsform=form, udbetaling_aar=10))
        assert e.value.felt == "ordninger[kap].udbetalingsform"


# ── US2: portioner ────────────────────────────────────────────────────────────────────────────

def test_portioner_efter_restvaerdi_formlen_og_afgift_pr_portion():
    # 600.000 over 6 år med afkast 0: 100.000 om året brutto, 60.000 netto efter 40 % afgift.
    r = res(replace(KAP, udbetalingsform="portioner", udbetaling_aar=6))
    assert [(e.alder, round(e.netto)) for e in r.engangsbeloeb] == [(a, 60_000) for a in range(65, 71)]
    assert all(e.ordning_id == "kap" and e.i_buffer for e in r.engangsbeloeb)
    # Portioner er ikke personlig indkomst og indgår ikke i indtægtsgrundlaget.
    assert all(kilde(r, a, "kap") is None for a in range(65, 71))


def test_portioner_med_afkast_folger_restvaerdi_formlen():
    # 300.000 over 3 år, 5 % afkast: 100.000; (200.000 × 1,05)/2 = 105.000; (105.000 × 1,05)/1 = 110.250.
    kap = Ordning("kap", "kapitalpension", 300_000, 63, oprettet=date(2000, 1, 1),
                  udbetalingsform="portioner", udbetaling_aar=3, afgift_betalt=True)
    r = beregn(enlig_profil(ordninger=(kap,)), Antagelser(afkast_efter_pal=0.05, inflation=0.0), 2026,
               BEREGNINGSDATO)
    assert [round(e.netto, 2) for e in r.engangsbeloeb] == [300_000 / 3, 105_000, 110_250]


def test_sidste_portion_senest_20_aar_efter_udbetalingsalderen():
    res(replace(KAP, udbetaling_start_alder=75, udbetalingsform="portioner", udbetaling_aar=6))  # 75–80 ok
    with pytest.raises(UgyldigtInput) as e:
        res(replace(KAP, udbetaling_start_alder=75, udbetalingsform="portioner", udbetaling_aar=7))  # 81
    assert e.value.felt == "ordninger[kap].udbetaling_aar"
    assert "20 år" in e.value.besked


def test_engangsbeloeb_efter_fristen_afvises():
    with pytest.raises(UgyldigtInput) as e:
        res(replace(KAP, udbetaling_start_alder=81))
    assert e.value.felt == "ordninger[kap].udbetaling_start_alder"


def test_portioner_kraever_mindst_to():
    with pytest.raises(UgyldigtInput):
        res(replace(KAP, udbetalingsform="portioner", udbetaling_aar=1))


def test_portioner_giver_advarsel_om_aftale():
    r = res(replace(KAP, udbetalingsform="portioner", udbetaling_aar=6))
    assert "PORTIONER_KRAEVER_AFTALE" in [a.kode for a in r.advarsler]


# ── US3: omlægning ────────────────────────────────────────────────────────────────────────────

def test_omlagt_til_ratepension_er_personlig_indkomst():
    r = res(replace(KAP, udbetalingsform="ratepension", udbetaling_aar=10))
    assert r.engangsbeloeb == ()
    k = kilde(r, 66, "kap")
    assert k.type == "ratepension" and k.brutto == pytest.approx(60_000)
    a69 = next(a for a in r.aar if a.alder == 69)  # efter folkepensionsalderen: i indtægtsgrundlaget
    assert a69.indtaegtsgrundlag >= 60_000
    assert "OMLAEGNING_KRAEVER_OVERFOERSEL" in [a.kode for a in r.advarsler]


def test_omlagt_til_livrente():
    r = res(replace(KAP, udbetalingsform="livsvarig"))
    k = kilde(r, 70, "kap")
    assert k.type == "livsvarig" and k.brutto > 0
    assert r.engangsbeloeb == ()


def test_omlagt_ratepension_folger_ratepensionens_regler():
    with pytest.raises(UgyldigtInput):
        res(replace(KAP, udbetalingsform="ratepension", udbetaling_aar=8))  # under 10 år


def test_udbetalingsform_kun_for_kapitalpension():
    ald = Ordning("ald", "aldersopsparing", 100_000, 65, oprettet=date(2010, 1, 1), udbetalingsform="portioner",
                  udbetaling_aar=3)
    with pytest.raises(UgyldigtInput) as e:
        beregn(enlig_profil(ordninger=(ald,)), NUL, 2026, BEREGNINGSDATO)
    assert e.value.felt == "ordninger[ald].udbetalingsform"
