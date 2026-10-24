"""Tidligste lovlige udbetalingsalder for private ordninger (pensionsbeskatningsloven § 1 A).

Afhænger af, hvornår aftalen er oprettet (research R2). Er oprettelsesdatoen ukendt,
bruges den mest restriktive (seneste) af reglerne, og resultatet markeres som usikkert.
"""
from __future__ import annotations

from datetime import date

from ..register.opslag import Regelopslag


def _foer_2007(foedselsdato: date, folkepensionsalder: int, o: Regelopslag) -> float:
    regel = o.v("ordning.udbetalingsalder.foer_2007")
    for raekke in regel["overgang"]:
        if foedselsdato <= raekke["foedt_til"]:
            return float(raekke["alder"])
    return float(folkepensionsalder - regel["aar_foer_fp"])


def tidligste_udbetalingsalder(
    foedselsdato: date, oprettet: date | None, folkepensionsalder: int, o: Regelopslag
) -> tuple[float, bool]:
    fra_2018 = o.v("ordning.udbetalingsalder.fra_2018")
    fra_2007 = o.v("ordning.udbetalingsalder.2007_2017")
    if oprettet is None:
        kandidater = (
            folkepensionsalder - fra_2018["aar_foer_fp"],
            folkepensionsalder - fra_2007["aar_foer_fp"],
            _foer_2007(foedselsdato, folkepensionsalder, o),
        )
        return float(max(kandidater)), True
    if oprettet >= fra_2018["oprettet_fra"]:
        return float(folkepensionsalder - fra_2018["aar_foer_fp"]), False
    if oprettet >= fra_2007["oprettet_fra"]:
        return float(folkepensionsalder - fra_2007["aar_foer_fp"]), False
    return _foer_2007(foedselsdato, folkepensionsalder, o), False
