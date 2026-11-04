"""Feature 035 T006 — beregningsgrundlaget og de tre forløb (FR-001, FR-002, FR-006, SC-001).

Med `branchestandard` finder kernen tre afkaststier pr. ordning (trin 1–2) og kører den almindelige
fremskrivning på hver (trin 3). Resultatet er det forventede forløb; `prognose` har det høje og lave.
"""
import math
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Ordning, Pensionsprofil, beregn
from pensionskerne.prognose import ordningens_stier
from pensionskerne.register.opslag import Regelopslag
from tests.conftest import BEREGNINGSDATO

EGNE = Antagelser()
BRANCHE = Antagelser(beregningsgrundlag="branchestandard")


def person(*ordninger, foedt=date(1971, 3, 1), opsparing=()):
    return Pensionsprofil(foedselsdato=foedt, civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=ordninger, opsparing=opsparing)


def rate(**kw):
    return Ordning("rate", "ratepension", 1_000_000, 67, oprettet=date(2010, 1, 1), udbetaling_aar=10,
                   aarlig_indbetaling=50_000, **kw)


def regn(profil, antagelser=BRANCHE, **kw):
    return beregn(profil, antagelser, 2026, BEREGNINGSDATO, **kw)


def test_egne_er_standard_og_giver_ingen_prognose():
    assert Antagelser().beregningsgrundlag == "egne"
    assert regn(person(rate()), EGNE).prognose is None


def test_tre_forloeb_i_raekkefoelge():
    res = regn(person(rate(), opsparing=(Aktiv("bank", 200_000),)))
    hoej, lav = res.prognose["hoej"], res.prognose["lav"]
    assert lav.jaevn.niveau_real < res.jaevn.niveau_real < hoej.jaevn.niveau_real


def test_skat_regnes_paa_hvert_forloeb_for_sig():
    """US2-2: Spændet efter skat er ikke spændet før skat skaleret, for skatten er progressiv."""
    res = regn(person(rate()))
    alder = 68
    skatteandel = {k: f.aar_ved(alder).skat_i_alt / (f.aar_ved(alder).skat_i_alt + f.aar_ved(alder).netto_i_alt)
                   for k, f in (("hoej", res.prognose["hoej"]), ("forv", res), ("lav", res.prognose["lav"]))}
    assert skatteandel["hoej"] > skatteandel["forv"] > skatteandel["lav"]


def test_uden_spaend_er_det_forventede_forloeb():
    """Optimeringen bruger kun det forventede forløb (FR-006)."""
    p = person(rate())
    fuld, kun = regn(p), regn(p, med_spaend=False)
    assert kun.prognose is None
    assert [a.netto_i_alt for a in kun.aar] == pytest.approx([a.netto_i_alt for a in fuld.aar])


def test_forventet_foerste_aar_haandregnet():
    """Aktieandel 50 %, år 1: μ = ln(1 + ½·(0,066 − 0,0045) + ½·(0,034 − 0,0022)); stien er e^μ − 1,
    og efter PAL-skat (15,3 %) gange 0,847."""
    o = Regelopslag(2026, 2026, 0.02)
    stier = ordningens_stier(rate(aktieandel=0.5), person(rate()), BEREGNINGSDATO, o)
    brutto = 0.5 * (0.066 - 0.0045) + 0.5 * (0.034 - 0.0022)
    assert stier["forventet"][2026] == pytest.approx(brutto * (1 - 0.153))
    assert stier["lav"][2026] < stier["forventet"][2026] < stier["hoej"][2026]


def test_stierne_daekker_til_sidste_rate():
    o = Regelopslag(2026, 2026, 0.02)
    stier = ordningens_stier(rate(), person(rate()), BEREGNINGSDATO, o)
    # Født 1971: 55 år i 2026, raten 67–76 (2038–2047). Stien går fra 2026 til året før sidste rate.
    assert min(stier["lav"]) == 2026 and max(stier["lav"]) == 2046
    assert all(math.isfinite(x) for s in stier.values() for x in s.values())


def test_engangsbeloeb_har_en_sti_til_udbetalingen():
    o = Regelopslag(2026, 2026, 0.02)
    alders = Ordning("alders", "aldersopsparing", 300_000, 67)
    stier = ordningens_stier(alders, person(alders), BEREGNINGSDATO, o)
    assert max(stier["forventet"]) == 2026 + 67 - 55 - 1


def test_egen_aktieandel_giver_hoejere_spaend():
    o = Regelopslag(2026, 2026, 0.02)
    lav_risiko = ordningens_stier(rate(aktieandel=0.2), person(rate()), BEREGNINGSDATO, o)
    hoej_risiko = ordningens_stier(rate(aktieandel=0.9), person(rate()), BEREGNINGSDATO, o)
    spaend = lambda s: s["hoej"][2026] - s["lav"][2026]  # noqa: E731
    assert spaend(hoej_risiko) > spaend(lav_risiko)


def test_branchestandard_bruger_raadets_inflation():
    res = regn(person(rate()))
    assert res.antagelser.inflation == 0.02
    assert res.antagelser.beregningsgrundlag == "branchestandard"


def test_opslagene_spores():
    res = regn(person(rate()))
    assert {"raadet.afkast.aar_1_5", "branchestandard.fraktiler", "branchestandard.standardprofil"} <= set(res.sporing_samlet)


def test_ordning_uden_saldo_og_indbetaling():
    res = regn(person(rate(), Ordning("tom", "ratepension", 0.0, 67, oprettet=date(2010, 1, 1))))
    assert res.prognose is not None


def test_samme_ordning_med_egne_er_uaendret():
    """SC-001: felterne til branchestandarden ændrer intet med `egne`."""
    p = person(rate())
    assert [a.netto_i_alt for a in regn(p, EGNE).aar] == \
        pytest.approx([a.netto_i_alt for a in regn(replace(p, ordninger=(rate(aktieandel=0.9),)), EGNE).aar])
