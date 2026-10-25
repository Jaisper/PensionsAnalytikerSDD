"""Feature 012 T003 — husstanden: to fulde profiler koblet efter loven (FR-002–FR-004, SC-001–SC-002).

- Pensionstillæg og tillægsprocent bygger på parrets samlede indtægtsgrundlag (lov om social
  pension § 29): partnerens private pension, ATP og kapitalindkomst indgår.
- Ældrechecks formuegrænse gælder husstandens samlede likvide formue (§ 72 d, stk. 2), også
  begges buffer.
- Kun ægtefæller: uudnyttet personfradrag (PSL § 10, stk. 3) og bundfradrag for kapitalindkomst
  (§ 7, stk. 5) overføres.
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, Pensionsprofil
from pensionskerne.husstand import beregn_husstand, partner_fra
from tests.conftest import BEREGNINGSDATO

A_ANT = Antagelser(afkast_efter_pal=0.04, inflation=0.02)


def person(foedt, *ordninger, civilstand="gift", formue=0, atp=15_000):
    return Pensionsprofil(foedselsdato=foedt, civilstand=civilstand, kommune="aarhus", likvid_formue=formue,
                          ordninger=ordninger, atp_aarlig=atp)


A = person(date(1958, 2, 1), Ordning("a1", "livsvarig", 600_000, 67, oprettet=date(2010, 1, 1)))
B = person(date(1962, 3, 1), Ordning("b1", "ratepension", 1_200_000, 64, oprettet=date(2010, 1, 1), udbetaling_aar=10))


def hus(a=A, b=B, ant_a=A_ANT, ant_b=A_ANT):
    return beregn_husstand(a, ant_a, b, ant_b, 2026, BEREGNINGSDATO)


def raekke(res, kalenderaar):
    return next(a for a in res.aar if a.kalenderaar == kalenderaar)


def test_partnerens_indkomst_er_privat_pension_atp_og_kapitalindkomst():
    h = hus()
    p = partner_fra(h.b, B, A_ANT)
    for a in h.b.aar:
        privat = sum(k.brutto for k in a.kilder if k.type in ("ratepension", "livsvarig", "atp"))
        assert p.indkomst_pr_aar[a.kalenderaar].oevrig_indkomst == pytest.approx(privat + a.kapitalindkomst)
    # År uden række hos partneren: 0 (ikke nærmeste år).
    assert p.indkomst_pr_aar[2026 + 60].oevrig_indkomst == 0
    assert p.pensionist_fra_aar == 1962 + h.b.folkepensionsalder


def test_partnerens_indkomst_indgaar_i_mit_indtaegtsgrundlag():
    h = hus()
    solo = hus(b=replace(B, ordninger=()))
    aar = 2032  # begge pensionister, B's ratepension udbetales
    assert raekke(h.a, aar).indtaegtsgrundlag > raekke(solo.a, aar).indtaegtsgrundlag + 50_000
    tillaeg = lambda a: next((k.brutto for k in a.kilder if k.type == "pensionstillaeg"), 0.0)
    assert tillaeg(raekke(h.a, aar)) < tillaeg(raekke(solo.a, aar))


def test_partner_der_udskyder_folkepension_er_ikke_pensionist_endnu():
    h = hus(ant_b=replace(A_ANT, folkepension_opsaettelse_aar=3))
    p = partner_fra(h.b, B, replace(A_ANT, folkepension_opsaettelse_aar=3))
    assert p.pensionist_fra_aar == 1962 + h.b.folkepensionsalder + 3


def test_faelles_formue_i_aeldrechecken():
    """Lave indkomster, så A har ret til ældrecheck — indtil B's buffer (en stor kapitalpension)
    tæller med i husstandens formue."""
    a = person(date(1958, 2, 1))
    b_buffer = person(date(1960, 3, 1), Ordning("b1", "kapitalpension", 1_000_000, 67, oprettet=date(2000, 1, 1)))
    b_direkte = replace(b_buffer, ordninger=(replace(b_buffer.ordninger[0], i_buffer=False),))
    ae = lambda r, aar: next((k.brutto for k in raekke(r, aar).kilder if k.type == "aeldrecheck"), 0.0)
    assert ae(hus(a, b_direkte).a, 2029) > 0
    assert ae(hus(a, b_buffer).a, 2029) == 0  # B's buffer pr. 1.1.2029 er langt over 108.000 kr.


def test_gift_overfoerer_personfradrag_samlevende_goer_ikke():
    """B (64–66 år) har kun en lille ratepension og bruger ikke hele sit personfradrag."""
    b_lav = person(date(1962, 3, 1), Ordning("b1", "ratepension", 200_000, 64, oprettet=date(2010, 1, 1), udbetaling_aar=10))
    gift, sam = hus(b=b_lav), hus(a=replace(A, civilstand="samlevende"), b=replace(b_lav, civilstand="samlevende"))
    aar = 2026
    overfoert = partner_fra(gift.b, b_lav, A_ANT).uudnyttet_personfradrag_pr_aar[aar]
    assert overfoert > 10_000
    assert raekke(sam.a, aar).skat_i_alt - raekke(gift.a, aar).skat_i_alt == pytest.approx(overfoert, abs=1)


def test_gift_deler_bundfradrag_for_kapitalindkomst():
    """Bundfradraget betyder kun noget, når personlig indkomst + kapitalindkomst over bundfradraget
    rammer mellemskattegrænsen (641.200 kr.) — derfor en stor livsvarig pension hos A."""
    a_rig = person(date(1958, 2, 1), Ordning("a1", "livsvarig", 12_000_000, 67, oprettet=date(2010, 1, 1)),
                   Ordning("a2", "kapitalpension", 2_500_000, 68, oprettet=date(2000, 1, 1)))
    gift = hus(a=a_rig, b=replace(B, ordninger=()))
    sam = hus(a=replace(a_rig, civilstand="samlevende"), b=replace(B, ordninger=(), civilstand="samlevende"))
    aar = max(gift.a.aar, key=lambda x: x.kapitalindkomst).kalenderaar
    assert raekke(gift.a, aar).kapitalindkomst > 55_000
    assert raekke(gift.a, aar).skat_kapitalindkomst < raekke(sam.a, aar).skat_kapitalindkomst


def test_konvergerer_og_er_symmetrisk():
    h = hus()
    assert h.konvergeret and 1 <= h.iterationer <= 4
    byttet = beregn_husstand(B, A_ANT, A, A_ANT, 2026, BEREGNINGSDATO)
    for x, y in ((h.a, byttet.b), (h.b, byttet.a)):
        for r, s in zip(x.jaevn.aar, y.jaevn.aar):
            assert r.jaevn == pytest.approx(s.jaevn, abs=12)  # inden for 1 kr./md.


def test_deterministisk():
    assert hus() == hus()


def test_partnerens_uroerte_opsparing_taeller_i_min_aeldrecheck():
    """Feature 013: partnerens opsparing pr. 1. januar indgår i husstandens formue (§ 72 d, stk. 2)."""
    from pensionskerne import Aktiv
    b_uden = replace(B, ordninger=())
    b_med = replace(b_uden, opsparing=(Aktiv("b-bank", 150_000, i_plan=False),))
    aeldrecheck = lambda res: next((k.brutto for k in raekke(res, 2030).kilder if k.type == "aeldrecheck"), 0.0)
    assert aeldrecheck(hus(b=b_uden).a) > 0
    assert aeldrecheck(hus(b=b_med).a) == 0
    p = partner_fra(hus(b=b_med).b, b_med, A_ANT)
    assert p.formue_pr_aar[2026] == pytest.approx(150_000)  # i dag: startsaldoen
