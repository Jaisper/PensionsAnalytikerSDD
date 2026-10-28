"""Feature 023a T001 — afkast pr. kalenderår (FR-001, FR-002, SC).

Inflation 0. `afkast_forloeb` er afkast efter PAL-skat pr. kalenderår; mangler et år, bruges
`afkast_efter_pal`.
"""
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Loen, Ordning, Pensionsprofil, beregn
from pensionskerne.jaevn import beregn_jaevn
from pensionskerne.regler.ordninger import rateplan
from tests.conftest import BEREGNINGSDATO

A = Antagelser(afkast_efter_pal=0.03, inflation=0.0)


def person(*ordninger, foedt=date(1958, 3, 1), opsparing=(), loen=None):
    return Pensionsprofil(foedselsdato=foedt, civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=ordninger, opsparing=opsparing, loen=loen)


def regn(profil, forloeb=None):
    ant = A if forloeb is None else Antagelser(afkast_efter_pal=0.03, inflation=0.0, afkast_forloeb=forloeb)
    return beregn(profil, ant, 2026, BEREGNINGSDATO)


def rate(start=68, saldo=1_000_000):
    return Ordning("rate", "ratepension", saldo, start, oprettet=date(2010, 1, 1), udbetaling_aar=10)


def brutto(res, alder, type_="ratepension"):
    return sum(k.brutto for k in res.aar_ved(alder).kilder if k.type == type_)


def test_rateplan_med_forloeb_haandregnet():
    """PBL § 11 A: raten er restværdien divideret med de resterende år. Et dårligt første år giver
    lavere rater bagefter: 100.000; 810.000 / 9 = 90.000; 720.000 × 1,03 / 8 = 92.700."""
    rater = rateplan(1_000_000, 10, [-0.10] + [0.03] * 9)
    assert rater[:3] == pytest.approx([100_000, 90_000, 92_700])
    assert rateplan(1_000_000, 10, [0.03] * 10) == pytest.approx(rateplan(1_000_000, 10, 0.03))


def test_ratepension_efter_et_daarligt_aar():
    """SC: borgeren er 68 i 2026, og raten begynder i år."""
    res = regn(person(rate()), {2026: -0.10})
    assert [brutto(res, a) for a in (68, 69, 70)] == pytest.approx([100_000, 90_000, 92_700])


def test_opsparingen_foer_start_vokser_med_aarets_afkast():
    """Født 1966 (60 år i 2026), raten begynder som 63: saldoen er 1.000.000 × 0,9 × 1,03²."""
    res = regn(person(rate(63), foedt=date(1966, 3, 1)), {2026: -0.10})
    assert brutto(res, 63) == pytest.approx(1_000_000 * 0.9 * 1.03 ** 2 / 10)


def test_uden_forloeb_og_med_samme_afkast_er_alt_uaendret():
    """FR-002."""
    p = person(rate(), Ordning("liv", "livsvarig", 500_000, 68),
               opsparing=(Aktiv("bank", 300_000),))
    uden = regn(p)
    samme = regn(p, {aar: 0.03 for aar in range(2026, 2060)})
    assert [a.netto_i_alt for a in samme.aar] == pytest.approx([a.netto_i_alt for a in uden.aar])
    assert samme.jaevn.niveau_real == pytest.approx(uden.jaevn.niveau_real)


def test_livsvarig_ydelse_aendres_ikke_af_forloebet():
    """Besluttet: selskaberne udjævner; ydelsen følger det forventede afkast (forenkling)."""
    p = person(Ordning("liv", "livsvarig", 500_000, 68))
    uden, med = regn(p), regn(p, {2026: -0.10, 2027: -0.10})
    assert brutto(med, 70, "livsvarig") == pytest.approx(brutto(uden, 70, "livsvarig"))
    assert any("forenkling:livsvarig_uden_aarets_afkast" in a.flag for a in med.aar)
    assert not any("forenkling:livsvarig_uden_aarets_afkast" in a.flag for a in uden.aar)


def test_daarlige_aar_foerst_giver_lavere_fast_beloeb_end_gode_aar_foerst():
    """Sekvensrisiko: samme gennemsnit, men rækkefølgen betyder noget."""
    p = person(rate(), opsparing=(Aktiv("bank", 400_000),))
    daarlig = regn(p, {2026: -0.10, 2027: -0.10, 2028: 0.16, 2029: 0.16})
    god = regn(p, {2026: 0.16, 2027: 0.16, 2028: -0.10, 2029: -0.10})
    assert daarlig.jaevn.niveau_real < god.jaevn.niveau_real


def test_jaevn_med_rente_pr_aar_er_som_fast_rente_naar_den_er_konstant():
    res = regn(person(rate(), opsparing=(Aktiv("bank", 200_000),)))
    raekker = tuple(res.aar)
    fast = beregn_jaevn(raekker, {68: 100_000}, 0.035, 0.0, 2026)
    pr_aar = beregn_jaevn(raekker, {68: 100_000}, [0.035] * len(raekker), 0.0, 2026)
    assert [a.jaevn for a in pr_aar.aar] == pytest.approx([a.jaevn for a in fast.aar])
    assert pr_aar.aar[-1].buffer_rest == pytest.approx(fast.aar[-1].buffer_rest, abs=1e-6)


def test_jaevn_bruger_aarets_rente_til_bufferen():
    """Et tab i bufferen det første år sænker niveauet; bufferen går stadig op i nul."""
    res = regn(person(rate(), opsparing=(Aktiv("bank", 200_000),)))
    raekker = tuple(res.aar)
    fast = beregn_jaevn(raekker, {68: 200_000}, 0.035, 0.0, 2026)
    tab = beregn_jaevn(raekker, {68: 200_000}, [-0.12] + [0.035] * (len(raekker) - 1), 0.0, 2026)
    assert tab.niveau_real < fast.niveau_real
    assert tab.aar[-1].buffer_rest == pytest.approx(0, abs=1)


def test_loen_og_stop_med_forloeb_regner():
    p = person(rate(64), foedt=date(1966, 3, 1), loen=Loen(480_000, stop_alder=64))
    res = regn(p, {2030: -0.12, 2031: -0.12})
    assert res.jaevn_fra_alder == 64
    assert res.jaevn.niveau_real < regn(p).jaevn.niveau_real
