"""Feature 035 T006 — branchestandarden i en husstand: spændet regnes for begge til sidst."""
from datetime import date

from pensionskerne import Antagelser, Ordning, Pensionsprofil
from pensionskerne.husstand import beregn_husstand
from tests.conftest import BEREGNINGSDATO

BRANCHE = Antagelser(beregningsgrundlag="branchestandard")


def person(foedt):
    return Pensionsprofil(foedselsdato=foedt, civilstand="gift", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=(Ordning("rate", "ratepension", 800_000, 67, oprettet=date(2010, 1, 1),
                                             udbetaling_aar=10),))


def test_begge_har_tre_forloeb():
    h = beregn_husstand(person(date(1968, 3, 1)), BRANCHE, person(date(1970, 6, 1)), BRANCHE, 2026, BEREGNINGSDATO)
    for res in (h.a, h.b):
        assert res.prognose is not None
        assert res.prognose["lav"].jaevn.niveau_real < res.jaevn.niveau_real < res.prognose["hoej"].jaevn.niveau_real
