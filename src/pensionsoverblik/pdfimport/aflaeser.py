"""Aflæsning af rapporttekst til strukturerede data.

Princip XI: aflæsningen SKAL ske lokalt og deterministisk. Intet fra rapporten må sendes til en
AI/LLM-tjeneste. Parseren til PensionsInfo-formatet ligger i pensionsinfo.py. Strukturen herunder
er kontrakten, som den leverer.
"""
from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel

Kategori = Literal["ratepension", "livsvarig", "aldersopsparing", "kapitalpension", "atp", "folkepension",
                   "forsikring", "ukendt"]


class Periode(BaseModel):
    etiket: str
    aarligt_beloeb: int | None


class AflaestOrdning(BaseModel):
    selskab: str | None
    aftalenr: str | None
    produkttype: str
    kategori: Kategori
    saldo: int | None
    aarlig_indbetaling: int | None
    tidligste_udbetalingsalder: int | None
    aftalt_udbetalingsalder: int | None
    udbetalingsperioder: list[Periode]
    afgift_betalt: bool | None
    noter: list[str] = []


class Aflaesning(BaseModel):
    atp_aarlig: int | None
    ordninger: list[AflaestOrdning]


class AflaesningFejl(RuntimeError):
    def __init__(self, kode: str, besked: str):
        super().__init__(besked)
        self.kode = kode
        self.besked = besked


class Aflaeser(Protocol):
    """En lokal, deterministisk aflæser. Må ikke kalde eksterne tjenester (Princip XI)."""

    async def aflaes(self, data: bytes) -> Aflaesning: ...


def vaelg_aflaeser() -> Aflaeser | None:
    """Den lokale PensionsInfo-parser. Lofter og satser hentes fra regelregistret (Princip II)."""
    from pensionskerne import register
    from pensionskerne.register.opslag import Regelopslag

    from .pensionsinfo import PensionsInfoAflaeser

    satsaar = max(register.satsaar())
    o = Regelopslag(satsaar, satsaar, 0.0)
    return PensionsInfoAflaeser(rateloft=o.v("ordning.ratepension.indbetalingsloft"), am_bidrag=o.v("skat.am_bidrag"))
