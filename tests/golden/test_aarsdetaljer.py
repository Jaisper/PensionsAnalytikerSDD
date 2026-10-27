"""Feature 020 — kernens årsdetaljer til forklaringen (FR-003, FR-004, SC-002).

For hvert år skal forklaringens regnestykke afstemme med kernens tal:
- skat pr. type (bund, kommune, kirke, mellem, top, toptop) − skatteloft − ægtefællenedsættelse
  + AM-bidrag = årets skat (inkl. skat af kapitalindkomst)
- kildernes netto = årets netto
- pensionstillæg før modregning ≥ det udbetalte
- ældrecheck kun, når formuen pr. 1. januar er inden for grænsen
"""
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Loen, Ordning, beregn
from pensionskerne.husstand import beregn_husstand
from tests.conftest import BEREGNINGSDATO, enlig_profil
from tests.golden.test_husstand import A, A_ANT, B

ANT = Antagelser(afkast_efter_pal=0.04, inflation=0.02)


def profiler():
    yield "enlig", beregn(enlig_profil(), ANT, 2026, BEREGNINGSDATO)
    yield "opsparing", beregn(enlig_profil(opsparing=(Aktiv("b", 400_000, i_plan=False),), folkekirkemedlem=True),
                              ANT, 2026, BEREGNINGSDATO)
    yield "loen", beregn(enlig_profil(loen=Loen(650_000, stop_alder=64), ordninger=(
        Ordning("r", "ratepension", 1_500_000, 64, oprettet=date(2010, 1, 1), udbetaling_aar=10, aarlig_indbetaling=50_000),)),
        ANT, 2026, BEREGNINGSDATO)
    h = beregn_husstand(A, A_ANT, B, A_ANT, 2026, BEREGNINGSDATO)
    yield "par_a", h.a
    yield "par_b", h.b


@pytest.mark.parametrize("navn, res", list(profiler()))
def test_skatten_afstemmer(navn, res):
    for a in res.aar:
        d = a.detaljer
        s = d.skat
        sum_ = (s.bundskat + s.kommuneskat + s.kirkeskat + s.mellemskat + s.topskat + s.toptopskat
                - s.skatteloft_nedslag - s.aegtefaelle_nedsaettelse + d.am_bidrag)
        if a.skat_i_alt + a.skat_kapitalindkomst > 0:
            assert sum_ == pytest.approx(a.skat_i_alt + a.skat_kapitalindkomst, abs=0.01), (navn, a.alder)
        assert sum(k.netto for k in a.kilder) == pytest.approx(a.netto_i_alt, abs=0.01)


@pytest.mark.parametrize("navn, res", list(profiler()))
def test_tillaeg_og_aeldrecheck(navn, res):
    for a in res.aar:
        d = a.detaljer
        tillaeg = next((k.brutto for k in a.kilder if k.type == "pensionstillaeg"), 0.0)
        assert d.pensionstillaeg_foer_modregning >= tillaeg - 1e-6
        if any(k.type == "aeldrecheck" for k in a.kilder):
            assert d.formue_primo is not None and d.formue_primo <= d.formuegraense


def test_loenaar_har_fradragene():
    res = dict(profiler())["loen"]
    d = res.aar_ved(res.aar[0].alder).detaljer
    assert d.am_bidrag > 0 and d.ligningsmaessige_fradrag > 0 and d.pensionsindbetaling > 0
