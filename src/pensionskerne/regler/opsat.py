"""Opsat folkepension — ventetillæg (lov om social pension § 15 a ff.; BEK nr. 930/2018 § 8).

Venteprocent = opsatte måneder / middellevetid i måneder ved den alder, opsættelsen
ophører (officiel tabel i registret). Den ganges på både grundbeløb og pensionstillæg
og udbetales livsvarigt (FR-051).
"""
from __future__ import annotations

from ..register.opslag import Regelopslag

MAANEDER = 12


def ventefaktor(folkepensionsalder: int, opsaettelse_aar: int, o: Regelopslag) -> float:
    """1 + venteprocent ved opsættelse i hele år fra folkepensionsalderen."""
    if opsaettelse_aar <= 0:
        return 1.0
    middellevetid = o.v("opsat.middellevetid_livsvarig")[str(folkepensionsalder + opsaettelse_aar)][0]
    venteprocent = round(opsaettelse_aar * MAANEDER / middellevetid, o.v("opsat.venteprocent_decimaler"))
    return 1 + venteprocent
