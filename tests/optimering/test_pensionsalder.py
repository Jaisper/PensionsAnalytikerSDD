"""Feature 007b T001 — den bedste plan begynder tidligst ved pensionsalderen (stopalderen, ellers
folkepensionsalderen). Borgeren er født 1. maj 1963: 63 år i 2026 og folkepensionsalder 68."""
from dataclasses import replace
from datetime import date

from pensionskerne import Antagelser, Loen, Ordning
from pensionskerne.optimering import optimer, pensionsalder, soegerum
from tests.conftest import BEREGNINGSDATO, enlig_profil

A = Antagelser(afkast_efter_pal=0.03, inflation=0.02)
RATE = Ordning("rate", "ratepension", 900_000, 64, oprettet=date(2010, 1, 1), udbetaling_aar=10)
LIV = Ordning("liv", "livsvarig", 1_200_000, 64, oprettet=date(2010, 1, 1))


def starter(dimensioner, oid):
    return [d[2] for dim in dimensioner for d in dim if d[0] == "start" and d[1] == oid]


def test_pensionsalderen_er_stopalderen_ellers_folkepensionsalderen():
    assert pensionsalder(enlig_profil(), 68) == 68
    assert pensionsalder(enlig_profil(loen=Loen(480_000)), 68) == 68
    assert pensionsalder(enlig_profil(loen=Loen(480_000, stop_alder=65)), 68) == 65


def test_uden_stopalder_starter_ingen_ordning_foer_folkepensionen():
    _, dim = soegerum(enlig_profil(ordninger=(RATE, LIV)), A, 2026, BEREGNINGSDATO)
    assert min(starter(dim, "rate")) == 68 and min(starter(dim, "liv")) == 68


def test_med_stopalder_starter_ingen_ordning_foer_stop():
    p = enlig_profil(ordninger=(RATE,), loen=Loen(480_000, stop_alder=65))
    _, dim = soegerum(p, A, 2026, BEREGNINGSDATO)
    assert min(starter(dim, "rate")) == 65


def test_en_ordning_der_allerede_udbetaler_flyttes_ikke():
    loebende = replace(RATE, udbetaling_start_alder=60)
    _, dim = soegerum(enlig_profil(ordninger=(loebende, LIV)), A, 2026, BEREGNINGSDATO)
    assert starter(dim, "rate") == [60]


def test_den_bedste_plan_maales_fra_pensionsalderen():
    r = optimer(enlig_profil(ordninger=(RATE, LIV)), A, 2026, BEREGNINGSDATO, maks_evalueringer=300)
    assert r.bedste is not None
    assert min(r.bedste.starter.values()) >= 68
    assert r.bedste_maaned > r.udgangspunkt_maaned


def test_bufferen_goer_ikke_en_plan_daarligere_end_at_skubbe_engangsbeloeb_sent():
    """Fejl fundet 2026-10-28: ordningerne starter efter stopalderen, så egen plan har år uden
    indkomst (fast beløb 0). Værnet VARIGHED målte "lave år" mod kandidatens eget faste beløb, så
    planer, der bruger engangsbeløbene i bufferen, blev afvist, og engangsbeløb og folkepension
    blev skubbet sent. Nu måles mod udgangspunktets faste beløb."""
    from pensionskerne import Loen
    from pensionskerne.optimering import anvend, fast_niveau, maalvindue, Plan
    from pensionskerne import beregn

    t = dict(tidligste_udbetalingsalder=60)
    p = enlig_profil(foedselsdato=date(1971, 3, 1), atp_aarlig=20_000, loen=Loen(850_000, stop_alder=63),
                     ordninger=(Ordning("rate", "ratepension", 2_000_000, 66, oprettet=date(2012, 1, 1), udbetaling_aar=10, **t),
                                Ordning("liv", "livsvarig", 3_000_000, 70, oprettet=date(2012, 1, 1), **t),
                                Ordning("kap", "kapitalpension", 1_500_000, 66, oprettet=date(2005, 1, 1), **t),
                                Ordning("ald", "aldersopsparing", 450_000, 66, oprettet=date(2012, 1, 1), **t)))
    a = Antagelser(afkast_efter_pal=0.04, inflation=0.02)
    r = optimer(p, a, 2026, BEREGNINGSDATO)
    alt_ved_stop = Plan(starter={"rate": 63, "liv": 63, "kap": 63, "ald": 63}, varighed={"rate": 10},
                        opsaettelse=0, form={"kap": ("engangs", None)})
    p2, a2 = anvend(p, a, alt_ved_stop)
    res = beregn(p2, a2, 2026, BEREGNINGSDATO)
    assert r.bedste_maaned >= fast_niveau(res, maalvindue(res, p2)) - 1
    # Ingen trappe: før rettelsen 22.065 → 27.360 → 32.933 kr./md.; nu fladt.
    from pensionskerne.optimering import slutniveau
    p3, a3 = anvend(p, a, r.bedste)
    assert r.bedste_maaned >= 0.95 * slutniveau(beregn(p3, a3, 2026, BEREGNINGSDATO))


def test_ved_uafgjort_vinder_det_flade_forloeb():
    """Valgt 2026-10-28: kan det laveste beløb ikke blive højere, foretrækkes det mindste spring
    op, ikke det højeste senere niveau. Den livsvarige kan tidligst udbetales som 75, så et
    spring er uundgåeligt; at starte den senere gør kun springet større."""
    p = enlig_profil(foedselsdato=date(1971, 3, 1), atp_aarlig=20_000, loen=Loen(600_000, stop_alder=63),
                     ordninger=(Ordning("rate", "ratepension", 600_000, 66, oprettet=date(2012, 1, 1), udbetaling_aar=10,
                                        tidligste_udbetalingsalder=63),
                                Ordning("liv", "livsvarig", 3_000_000, 80, oprettet=date(2012, 1, 1),
                                        tidligste_udbetalingsalder=75)))
    a = Antagelser(afkast_efter_pal=0.04, inflation=0.02)
    r = optimer(p, a, 2026, BEREGNINGSDATO)
    assert r.bedste is not None and r.bedste.starter["liv"] == 75
