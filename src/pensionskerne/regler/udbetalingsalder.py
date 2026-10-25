"""Tidligste lovlige udbetalingsalder for private ordninger (pensionsbeskatningsloven § 1 A).

Afhænger af, hvornår aftalen er oprettet (research R2). Er oprettelsesdatoen ukendt,
bruges den mest restriktive (seneste) af reglerne, og resultatet markeres som usikkert.
Oplyser pensionsselskabet selv alderen (PensionsInfo), har den forrang (se validering).
"""
from __future__ import annotations

from datetime import date

from ..register.opslag import Regelopslag


def tidligste_udbetalingsalder(
    foedselsdato: date, oprettet: date | None, folkepensionsalder: int, o: Regelopslag
) -> tuple[float, bool]:
    fra_2018 = o.v("ordning.udbetalingsalder.fra_2018")
    fra_2007 = o.v("ordning.udbetalingsalder.2007_2017")
    foer_2007 = float(o.v("ordning.udbetalingsalder.foer_2007")["alder"])
    if oprettet is None:
        kandidater = (
            folkepensionsalder - fra_2018["aar_foer_fp"],
            folkepensionsalder - fra_2007["aar_foer_fp"],
            foer_2007,
        )
        return float(max(kandidater)), True
    if oprettet >= fra_2018["oprettet_fra"]:
        return float(folkepensionsalder - fra_2018["aar_foer_fp"]), False
    if oprettet >= fra_2007["oprettet_fra"]:
        return float(folkepensionsalder - fra_2007["aar_foer_fp"]), False
    return foer_2007, False
