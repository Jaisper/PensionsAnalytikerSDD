"""Aflæsning af rapporttekst til strukturerede data.

Princip XI: aflæsningen SKAL ske lokalt og deterministisk. Intet fra rapporten må sendes til en
AI/LLM-tjeneste. Den lokale parser til PensionsInfo-formatet er endnu ikke bygget (den kræver
mindst én rigtig rapport at udvikle og teste mod). Indtil da er PDF-indlæsningen slået fra.
Strukturen herunder er kontrakten, som parseren skal levere.
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

    async def aflaes(self, tekst: str) -> Aflaesning: ...


def vaelg_aflaeser() -> Aflaeser | None:
    """Ingen lokal parser endnu → PDF-indlæsningen er slået fra, og guiden udfyldes manuelt."""
    return None
