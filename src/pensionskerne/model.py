"""Input- og output-typer for beregningskernen (se specs/001-beregningskerne/data-model.md).

Alle typer er uforanderlige. Beløb er kr. pr. år, satser er brøker, aldre er hele år.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Mapping

Civilstand = Literal["enlig", "gift_samlevende"]
Ordningstype = Literal["ratepension", "livsvarig", "aldersopsparing", "kapitalpension"]
Kildetype = Literal[
    "ratepension", "livsvarig", "grundbeloeb", "pensionstillaeg", "atp", "aeldrecheck", "mediecheck"
]


# ── Fejl ─────────────────────────────────────────────────────────────────────

class UgyldigtInput(ValueError):
    """Input kan ikke beregnes. `felt` peger på det ugyldige felt (FR-003)."""

    def __init__(self, felt: str, besked: str):
        super().__init__(f"{felt}: {besked}")
        self.felt = felt
        self.besked = besked


class UverificeretRegel(RuntimeError):
    """Streng tilstand: beregningen ville bruge en registerpost uden status `verificeret` (FR-012)."""

    def __init__(self, id: str, kilde: str, status: str):
        super().__init__(f"Registerpost '{id}' har status '{status}' (kilde: {kilde})")
        self.id = id
        self.kilde = kilde
        self.status = status


# ── Input ────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Ordning:
    id: str
    type: Ordningstype
    saldo: float
    udbetaling_start_alder: int
    oprettet: date | None = None
    aarlig_indbetaling: float = 0.0
    udbetaling_aar: int | None = None   # kun ratepension; None = registrets minimum
    i_buffer: bool = True               # kun engangsbeløb (US7)


@dataclass(frozen=True)
class PartnerIndkomst:
    am_pligtig_arbejdsindkomst: float = 0.0
    oevrig_indkomst: float = 0.0        # private pensioner, kapitalindkomst, offentlige ydelser


@dataclass(frozen=True)
class Partner:
    foedselsdato: date
    indkomst_pr_aar: Mapping[int, PartnerIndkomst] = field(default_factory=dict)


@dataclass(frozen=True)
class Pensionsprofil:
    foedselsdato: date
    civilstand: Civilstand
    kommune: str
    kirkeskat: float | None = None      # None = ikke medlem af folkekirken
    likvid_formue: float = 0.0
    anden_kapitalindkomst: float = 0.0
    ordninger: tuple[Ordning, ...] | list[Ordning] = ()
    atp_aarlig: float | None = None     # None = registrets fallback (markeres)
    partner: Partner | None = None


@dataclass(frozen=True)
class Antagelser:
    afkast_efter_pal: float = 0.04
    inflation: float = 0.02
    satsregulering: float | None = None  # None = samme som inflation (FR-060)
    loenvaekst: float = 0.0
    livsvarig_horisont_alder: int = 90
    livsvarig_min_aar: int = 18
    buffer_kapitalskat: float = 0.27
    folkepension_opsaettelse_aar: int = 0

    @property
    def effektiv_satsregulering(self) -> float:
        return self.inflation if self.satsregulering is None else self.satsregulering


# ── Output ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Indkomstkilde:
    kilde_id: str
    type: Kildetype
    brutto: float
    skat: float
    netto: float


@dataclass(frozen=True)
class Aarsresultat:
    alder: int
    kalenderaar: int
    kilder: tuple[Indkomstkilde, ...]
    personlig_indkomst: float
    skat_i_alt: float
    indtaegtsgrundlag: float
    tillaegsprocent: int
    netto_i_alt: float
    netto_real: float
    engangsbeloeb_netto: float
    sporing: tuple[str, ...]
    flag: tuple[str, ...]


@dataclass(frozen=True)
class Advarsel:
    kode: str
    besked: str
    aldre: tuple[int, int] | None = None
    registerposter: tuple[str, ...] = ()


@dataclass(frozen=True)
class JaevnAar:
    alder: int
    jaevn: float
    normal: float
    fra_buffer: float
    til_buffer: float
    buffer_rest: float


@dataclass(frozen=True)
class JaevnUdbetaling:
    niveau_foerste_aar: float
    niveau_real: float
    aar: tuple[JaevnAar, ...]


@dataclass(frozen=True)
class Fremskrivning:
    satsaar: int
    beregningsdato: date
    folkepensionsalder: int
    aar: tuple[Aarsresultat, ...]
    advarsler: tuple[Advarsel, ...]
    antagelser: Antagelser
    sporing_samlet: tuple[str, ...]
    jaevn: JaevnUdbetaling | None = None

    def aar_ved(self, alder: int) -> Aarsresultat:
        return next(a for a in self.aar if a.alder == alder)
