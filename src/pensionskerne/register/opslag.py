"""Regelopslag: eneste vej fra beregningen ind i registret (research T5).

Hvert opslag registreres i sporingen, flag for ikke-verificerede poster sættes
automatisk, og streng tilstand afviser dem. Beløb med `reguleres = true` fremskrives
med satsreguleringen fra satsåret til kalenderåret (FR-060).
"""
from __future__ import annotations

from typing import Any

from ..model import UverificeretRegel
from . import kommuneregister, kommune_noegle, post


class Regelopslag:
    def __init__(self, satsaar: int, kalenderaar: int, satsregulering: float, streng: bool = False):
        self.satsaar = satsaar
        self.kalenderaar = kalenderaar
        self.satsregulering = satsregulering
        self.streng = streng
        self.brugt: list[str] = []
        self.flag: list[str] = []
        self._vaerdier: dict[str, Any] = {}  # samme post giver altid samme værdi for samme år

    # ── intern registrering ──────────────────────────────────────────────
    def _registrer(self, id: str, status: str, kilde: str) -> None:
        if self.streng and status != "verificeret":
            raise UverificeretRegel(id, kilde, status)
        if id not in self.brugt:
            self.brugt.append(id)
        if status != "verificeret":
            self.marker(f"{status}:{id}")

    def marker(self, flag: str) -> None:
        if flag not in self.flag:
            self.flag.append(flag)

    @property
    def reguleringsfaktor(self) -> float:
        return (1 + self.satsregulering) ** max(0, self.kalenderaar - self.satsaar)

    # ── opslag ───────────────────────────────────────────────────────────
    def v(self, id: str) -> Any:
        """Værdien for kalenderåret (satsreguleret, hvis posten er et beløb, der reguleres)."""
        if id in self._vaerdier:  # allerede registreret i sporingen
            return self._vaerdier[id]
        p = post(self.satsaar, id)
        self._registrer(p.id, p.status, p.kilde)
        vaerdi = p.vaerdi * self.reguleringsfaktor if p.reguleres else p.vaerdi
        self._vaerdier[id] = vaerdi
        return vaerdi

    def husk(self, noegle: str, lav):
        """Afledte værdier (fx listen af skattetrin), lavet én gang pr. år af `lav()` — kun ud fra
        opslag i dette år, så de registreres i sporingen første gang."""
        if noegle not in self._vaerdier:
            self._vaerdier[noegle] = lav()
        return self._vaerdier[noegle]

    def antagelse(self, navn: str, vaerdi: Any) -> Any:
        id = f"antagelse.{navn}"
        if id not in self.brugt:
            self.brugt.append(id)
        return vaerdi

    def kommuneskat(self, navn: str) -> float:
        reg, noegle = self._kommune(navn)
        self._registrer(f"kommune.{noegle}", reg.status, reg.kilde)
        return reg.satser[noegle]

    def kirkeskat(self, navn: str) -> float:
        reg, noegle = self._kommune(navn)
        self._registrer(f"kirkeskat.{noegle}", reg.status, reg.kilde)
        return reg.kirkeskat[noegle]

    def _kommune(self, navn: str):
        reg = kommuneregister(self.satsaar)
        noegle = kommune_noegle(self.satsaar, navn)
        if noegle is None:
            raise KeyError(navn)
        return reg, noegle

    def overtag(self, andet: "Regelopslag") -> None:
        for id in andet.brugt:
            if id not in self.brugt:
                self.brugt.append(id)
        for f in andet.flag:
            self.marker(f)
