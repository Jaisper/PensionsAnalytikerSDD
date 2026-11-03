"""Forsikringer fra PensionsInfo efter skat (feature 034).

Rapporten giver hver dækning en skattekode: A (afgiftspligtig), F (skatte- og afgiftsfri) eller S
(skattepligtig som personlig indkomst). Afgiften kommer fra registret (`forsikring.afgift`).
Skattepligtige beløb til efterladte regnes ikke: skatten afhænger af modtagerens indkomst, som er
ukendt. Tab af arbejdsevne er borgerens egen indkomst og regnes som årets eneste personlige indkomst,
fordi dækningen erstatter lønnen. Pensionsudbetalinger er ikke arbejdsmarkedsbidragspligtige.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from .regler.skat import beregn_skat
from .register.opslag import Regelopslag

Beskatning = Literal["afgift", "skattefri", "indkomst", "modtager", "ukendt"]


@dataclass(frozen=True)
class EfterSkat:
    netto: float | None      # pr. udbetaling (engangsbeløb) eller pr. år (løbende); None = regnes ikke
    beskatning: Beskatning


def efter_skat(type_: str, skattekode: str | None, form: str | None, beloeb: float | None, kommune: str,
               folkekirkemedlem: bool, satsaar: int, beregningsdato: date) -> EfterSkat:
    if skattekode == "F":
        return EfterSkat(beloeb, "skattefri")
    if skattekode == "A":
        o = Regelopslag(satsaar, beregningsdato.year, 0.0)
        return EfterSkat(None if beloeb is None else beloeb * (1 - o.v("forsikring.afgift")), "afgift")
    if skattekode == "S" and type_ == "erhvervsevne" and form in ("aarraekke", "livsvarig"):
        if beloeb is None:
            return EfterSkat(None, "indkomst")
        o = Regelopslag(satsaar, beregningsdato.year, 0.0)
        kirke = o.kirkeskat(kommune) if folkekirkemedlem else 0.0
        return EfterSkat(beloeb - beregn_skat(beloeb, o.kommuneskat(kommune), kirke, o).total, "indkomst")
    if skattekode == "S":
        return EfterSkat(None, "modtager")
    return EfterSkat(None, "ukendt")
