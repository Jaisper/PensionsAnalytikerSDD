"""Feature 030 — uden en valgt stopalder stopper lønnen, når den første udbetaling, der bruges i det
faste beløb, begynder (højst ved folkepensionsalderen). Født 1. marts 1966: 60 år i 2026, folkepension 69."""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Antagelser, Loen, Ordning, beregn
from pensionskerne.model import stopalder
from tests.conftest import BEREGNINGSDATO, enlig_profil

FOEDT = date(1966, 3, 1)
FP = 69
RATE = Ordning("rate", "ratepension", 1_200_000, 65, oprettet=date(2000, 1, 1), udbetaling_aar=10)
LIV = Ordning("liv", "livsvarig", 1_000_000, 67, oprettet=date(2000, 1, 1))
KAP = Ordning("kap", "kapitalpension", 400_000, 62, oprettet=date(2000, 1, 1))


def profil(*ordninger, stop=None):
    return enlig_profil(foedselsdato=FOEDT, ordninger=ordninger, loen=Loen(480_000, stop_alder=stop))


@pytest.mark.parametrize(("ordninger", "stop", "forventet"), [
    ((RATE, LIV), None, 65),
    ((replace(RATE, udbetaling_start_alder=63), LIV), None, 63),
    ((RATE, LIV, replace(KAP, i_buffer=False)), None, 65),          # direkte udbetalt: tæller ikke
    ((RATE, LIV, KAP), None, 62),                                     # i bufferen: tæller
    ((RATE, LIV, replace(KAP, i_buffer=False, udbetalingsform="ratepension", udbetaling_aar=10)), None, 62),  # omlagt
    ((replace(RATE, udbetaling_start_alder=70), replace(LIV, udbetaling_start_alder=70)), None, FP),
    ((), None, FP),
    ((RATE, LIV), 66, 66),                                            # valgt stopalder gælder
])
def test_stopalder(ordninger, stop, forventet):
    assert stopalder(profil(*ordninger, stop=stop), FP) == forventet


def test_loennen_stopper_ved_foerste_udbetaling():
    res = beregn(profil(RATE, LIV), Antagelser(), 2026, BEREGNINGSDATO)
    assert res.jaevn_fra_alder == 65
    med_loen = [a.alder for a in res.aar if any(k.type == "loen" for k in a.kilder)]
    assert med_loen and max(med_loen) == 64
