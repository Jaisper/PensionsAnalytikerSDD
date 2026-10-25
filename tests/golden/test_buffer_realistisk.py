"""Feature 009 T006 — bufferen regnes som den virkelige opsparing (US4, FR-005–FR-007).

Engangsbeløb i bufferen står i bank/obligationer: afkastet (samme afkast før skat som pensionen,
dvs. afkast efter PAL / (1 − 15,3 %)) er positiv kapitalindkomst. Det beskattes efter
personskatteloven, indgår i indtægtsgrundlaget for pensionstillæg (lov om social pension § 29),
og opsparingen pr. 1. januar tæller med i ældrechecks formuegrænse (§ 72 d, stk. 2).
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, beregn
from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.skat import beregn_skat
from tests.conftest import BEREGNINGSDATO, enlig_profil

A = Antagelser(afkast_efter_pal=0.04, inflation=0.02)
PAL = 0.153
R = 0.04 / (1 - PAL)

# Født 1958: folkepension fra 67 år (2025) — pensionist i hele tabellen. Lille privat pension, så
# der er pensionstillæg og ældrecheck at miste.
LILLE = Ordning("liv", "livsvarig", 300_000, 67, oprettet=date(2010, 1, 1))
# Nok privat pension til, at indtægtsgrundlaget er over fradragsbeløbet, så kapitalindkomsten
# kan ses i pensionstillægget.
MELLEM = Ordning("liv", "livsvarig", 1_800_000, 67, oprettet=date(2010, 1, 1))
KAP = Ordning("kap", "kapitalpension", 1_000_000, 69, oprettet=date(2000, 1, 1))


def profil(*ordninger, **kw):
    return enlig_profil(foedselsdato=date(1958, 2, 1), ordninger=ordninger, atp_aarlig=15_000, likvid_formue=0, **kw)


def res(*ordninger, antagelser=A, **kw):
    return beregn(profil(*ordninger, **kw), antagelser, 2026, BEREGNINGSDATO)


def test_kapitalindkomst_er_bufferens_afkast():
    r = res(LILLE, KAP)
    for a, j in zip(r.aar, r.jaevn.aar):
        assert a.kapitalindkomst == pytest.approx(max(0.0, j.buffer_rest) * R / (1 + R), abs=5)
    assert max(a.kapitalindkomst for a in r.aar) > 10_000


def test_skat_af_kapitalindkomst_er_marginal_skat():
    r = res(LILLE, KAP)
    a = max(r.aar, key=lambda x: x.kapitalindkomst)
    o = Regelopslag(2026, a.kalenderaar, 0.02)
    s = beregn_skat(a.personlig_indkomst, o.kommuneskat("aarhus"), 0.0, o, kapitalindkomst=a.kapitalindkomst)
    assert a.skat_kapitalindkomst == pytest.approx(s.skat_kapitalindkomst, rel=1e-9)
    assert a.skat_kapitalindkomst > 0


def test_kapitalindkomst_nedsaetter_pensionstillaegget():
    med = res(MELLEM, KAP)
    uden = res(MELLEM, replace(KAP, i_buffer=False))  # udbetales direkte: ingen buffer
    a_med = max(med.aar, key=lambda x: x.kapitalindkomst)
    a_uden = next(a for a in uden.aar if a.alder == a_med.alder)
    tillaeg = lambda a: next((k.brutto for k in a.kilder if k.type == "pensionstillaeg"), 0.0)
    assert a_med.indtaegtsgrundlag > a_uden.indtaegtsgrundlag
    assert tillaeg(a_med) < tillaeg(a_uden)


def test_buffer_over_formuegraensen_fjerner_aeldrechecken():
    uden = res(LILLE, replace(KAP, i_buffer=False))
    med = res(LILLE, KAP)
    ae = lambda r, alder: next((k.brutto for a in r.aar if a.alder == alder for k in a.kilder if k.type == "aeldrecheck"), 0.0)
    # Året efter engangsbeløbet (formue pr. 1. januar) er bufferen langt over 108.000 kr.
    assert ae(uden, 70) > 0
    assert ae(med, 70) == 0


def test_portioner_giver_mindre_kapitalindkomst_end_engangsbeloeb():
    engangs = res(LILLE, KAP)
    portioner = res(LILLE, replace(KAP, udbetalingsform="portioner", udbetaling_aar=10))
    # Udjævningen sparer også portionerne op, så toppen kan ligge tæt på; men pengene står kortere
    # tid i banken, så den samlede kapitalindkomst er lavere.
    assert sum(a.kapitalindkomst for a in portioner.aar) < sum(a.kapitalindkomst for a in engangs.aar)


def test_konvergerer_hurtigt():
    for r in (res(LILLE, KAP), res(LILLE), res(LILLE, replace(KAP, udbetalingsform="portioner", udbetaling_aar=10))):
        assert 1 <= r.buffer_iterationer <= 6  # SC-002 (research R002)
        assert "BUFFER_IKKE_KONVERGERET" not in [a.kode for a in r.advarsler]


def test_bufferen_gaar_stadig_op_i_nul():
    r = res(LILLE, KAP)
    assert r.jaevn.aar[-1].buffer_rest == pytest.approx(0, abs=1)


def test_forudsaetning_erstatter_forenkling():
    koder = [a.kode for a in res(LILLE, KAP).advarsler]
    assert "BUFFER_SOM_OPSPARING" in koder and "BUFFER_YDELSE_FORENKLING" not in koder


def test_ingen_buffer_uden_afkast():
    r = res(LILLE, KAP, antagelser=Antagelser(afkast_efter_pal=0.0, inflation=0.0))
    assert all(a.kapitalindkomst == 0 and a.skat_kapitalindkomst == 0 for a in r.aar)


def test_antagelsen_om_fast_kapitalskat_er_vaek():
    assert not hasattr(Antagelser(), "buffer_kapitalskat")
