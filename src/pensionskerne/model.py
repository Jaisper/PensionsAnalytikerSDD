"""Input- og output-typer for beregningskernen (se specs/001-beregningskerne/data-model.md).

Alle typer er uforanderlige. Beløb er kr. pr. år, satser er brøker, aldre er hele år.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Mapping

# Feature 012: gift og samlevende behandles ens af ydelserne; kun ægtefæller har skatteoverførsler.
# "gift_samlevende" (før 012) læses som samlevende.
Civilstand = Literal["enlig", "gift", "samlevende", "gift_samlevende"]
Ordningstype = Literal["ratepension", "livsvarig", "aldersopsparing", "kapitalpension"]
# Feature 013: opsparing uden for pension. Bank (kapitalindkomst; også obligationsbaserede
# investeringsbeviser), frit depot (aktieindkomst ved salg) og aktiesparekonto (lagerskat) (013b).
Aktivtype = Literal["bank", "depot", "ask"]
AKTIVLAG = ("bank", "depot", "ask")
Kildetype = Literal[
    "ratepension", "livsvarig", "grundbeloeb", "pensionstillaeg", "atp", "aeldrecheck", "mediecheck", "loen"
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
    udbetaling_aar: int | None = None   # ratepension (None = registrets minimum); kapitalpension i portioner/omlagt
    i_buffer: bool = True               # kun engangsbeløb (US7)
    tidligste_udbetalingsalder: float | None = None  # oplyst af pensionsselskabet (PensionsInfo); overstyrer reglen
    afgift_betalt: bool = False         # kapitalpension, hvor afgiften er betalt (fx omlagt 2013–2014): skattefri (009)
    udbetalingsform: str = "engangs"    # kapitalpension: engangs | portioner | ratepension | livsvarig (009)


@dataclass(frozen=True)
class Aktiv:
    """Opsparing uden for pension (feature 013), ejet af den profil, den ligger i. Saldoen er likvid
    formue (LSP § 72 d, stk. 2). Bankens afkast er kapitalindkomst; depotets er kursgevinst, der
    beskattes ved salg; aktiesparekontoens lagerbeskattes (013b)."""
    id: str
    saldo: float                        # i dag
    type: Aktivtype = "bank"
    i_plan: bool = True                 # True: bruges i den faste udbetaling; False: står urørt og forrentes
    urealiseret_gevinst: float | None = None  # depot: heraf gevinst i dag; None = antagelsens andel (013b)
    aarligt_indskud: float = 0.0        # aktiesparekonto: indskud om året i dagens kroner, mens der er løn (013b)


@dataclass(frozen=True)
class Loen:
    """Løn (feature 017) i dagens kroner; reguleres med satsreguleringen (konstant købekraft)."""
    aarlig: float                           # årsløn før skat, inkl. egen pensionsindbetaling
    stop_alder: int | None = None           # første år uden løn; None = folkepensionsalderen
    deltid_aarlig: float = 0.0              # løn efter stop (fx ved siden af pensionen)
    deltid_til_alder: int | None = None     # første år uden deltidsløn


@dataclass(frozen=True)
class PartnerIndkomst:
    am_pligtig_arbejdsindkomst: float = 0.0
    oevrig_indkomst: float = 0.0        # private pensioner, kapitalindkomst, offentlige ydelser


@dataclass(frozen=True)
class Partner:
    foedselsdato: date
    indkomst_pr_aar: Mapping[int, PartnerIndkomst] = field(default_factory=dict)
    # Feature 012 — kendes partneren som fuld profil (husstanden), pr. kalenderår:
    formue_pr_aar: Mapping[int, float] = field(default_factory=dict)          # partnerens opsparing pr. 1. januar
    kapitalindkomst_pr_aar: Mapping[int, float] = field(default_factory=dict) # partnerens positive KI
    uudnyttet_personfradrag_pr_aar: Mapping[int, float] = field(default_factory=dict)  # skatteværdi
    aktieindkomst_pr_aar: Mapping[int, float] = field(default_factory=dict)   # partnerens aktieindkomst (013b)
    pensionist_fra_aar: int | None = None  # partnerens faktiske folkepensionsstart (None = ud fra alderen)


@dataclass(frozen=True)
class Pensionsprofil:
    foedselsdato: date
    civilstand: Civilstand
    kommune: str
    folkekirkemedlem: bool = False      # kirkeskat efter kommunens sats (registret)
    likvid_formue: float = 0.0          # fast likvid formue pr. 1. januar (§ 72 d, stk. 2); kun ældrechecken
    anden_kapitalindkomst: float = 0.0
    opsparing: tuple[Aktiv, ...] | list[Aktiv] = ()  # feature 013
    loen: Loen | None = None                          # feature 017
    ordninger: tuple[Ordning, ...] | list[Ordning] = ()
    atp_aarlig: float | None = None     # None = registrets fallback (markeres)
    partner: Partner | None = None


@dataclass(frozen=True)
class Antagelser:
    afkast_efter_pal: float = 0.04
    inflation: float = 0.02
    satsregulering: float | None = None  # None = samme som inflation (FR-060)
    loenvaekst: float = 0.0              # realvækst i pensionsindbetalingen oven i satsreguleringen (017b)
    livsvarig_horisont_alder: int = 90   # livrentens beregningshorisont (selskabets ydelse)
    plan_slut_alder: int | None = None   # planens sidste år (019); None = livsvarig_horisont_alder
    livsvarig_min_aar: int = 18
    folkepension_opsaettelse_aar: int = 0
    depot_urealiseret_andel: float = 0.5  # depotets gevinstandel, når den ikke er oplyst (013b)
    traekraekkefoelge: tuple[str, ...] = AKTIVLAG  # rækkefølgen, opsparingen bruges i (013b)

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
class SkatDetaljer:
    """Årets skat pr. type efter personfradrag (feature 020). Summen − skatteloftets nedslag −
    ægtefællens nedsættelse er indkomstskatten (inkl. skat af kapitalindkomst)."""
    bundskat: float = 0.0
    kommuneskat: float = 0.0
    kirkeskat: float = 0.0
    mellemskat: float = 0.0
    topskat: float = 0.0
    toptopskat: float = 0.0
    skatteloft_nedslag: float = 0.0
    aegtefaelle_nedsaettelse: float = 0.0


@dataclass(frozen=True)
class Aarsdetaljer:
    """Mellemresultater bag et år, så forklaringen ikke skal regne selv (feature 020, FR-003)."""
    skat: SkatDetaljer
    am_bidrag: float = 0.0
    ligningsmaessige_fradrag: float = 0.0
    pensionsindbetaling: float = 0.0            # fradraget i den personlige indkomst (017)
    pensionstillaeg_foer_modregning: float = 0.0
    formue_primo: float | None = None           # husstandens likvide formue pr. 1. januar (ældrecheck)
    formuegraense: float | None = None


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
    realfaktor: float           # gang et nominelt beløb i året med denne for at få dagens kroner
    engangsbeloeb_netto: float
    sporing: tuple[str, ...]
    flag: tuple[str, ...]
    kapitalindkomst: float = 0.0        # bufferens afkast (nominelt), positiv nettokapitalindkomst (009)
    skat_kapitalindkomst: float = 0.0   # merskatten af kapitalindkomsten; betales af bufferen (009)
    uudnyttet_personfradrag: float = 0.0  # skatteværdi, en ægtefælle kan bruge (PSL § 10, stk. 3) (012)
    detaljer: Aarsdetaljer | None = None  # feature 020
    # Feature 013b: realiseret gevinst fra frit depot og skatten af den (PSL § 8 a), lagerskat af
    # aktiesparekontoen og løbende indskud på den. Skatterne betales af årets udbetaling.
    aktieindkomst: float = 0.0
    skat_aktieindkomst: float = 0.0
    skat_aktiesparekonto: float = 0.0
    indskud_opsparing: float = 0.0

    @property
    def skat_opsparing(self) -> float:
        """Skatten af opsparingen uden for pension (kapitalindkomst, aktieindkomst og ASK)."""
        return self.skat_kapitalindkomst + self.skat_aktieindkomst + self.skat_aktiesparekonto

    @property
    def disponibel(self) -> float:
        """Årets nettoindkomst efter skat af opsparing og indskud på den: det, udjævningen fordeler."""
        return self.netto_i_alt - self.skat_opsparing - self.indskud_opsparing


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
class Engangsbeloeb:
    """Et engangsbeløb fra en ordning (feature 008) — oplysning, ingen ny beregning."""
    ordning_id: str
    type: str
    alder: int
    netto: float                # nominelt, i udbetalingsåret (efter evt. afgift)
    i_buffer: bool              # True = indgår i den jævne udbetaling; False = udbetales direkte


@dataclass(frozen=True)
class FormueAar:
    """Opsparing uden for pension ved årets udgang (feature 013), nominelt."""
    alder: int
    i_plan: float               # bruges i den faste udbetaling (bank i planen og bufferen fra engangsbeløb)
    uden_for_plan: float        # står urørt og forrentes
    realfaktor: float = 1.0     # som Aarsresultat.realfaktor: gang med den for dagens kroner


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
    engangsbeloeb: tuple[Engangsbeloeb, ...] = ()
    buffer_iterationer: int = 1         # fastpunkt-iterationer for bufferens kapitalindkomst og formue (009)
    formue: tuple[FormueAar, ...] = ()  # fra i dag til sidste år (013)
    formue_start: float = 0.0           # opsparingen i dag (013)
    jaevn_fra_alder: int | None = None  # første år i udjævningen (017: stopalderen); None = første række

    def formue_primo(self) -> dict[int, float]:
        """Opsparingen pr. 1. januar pr. alder: ultimo året før, og i dag startsaldoen (013)."""
        if not self.formue:
            return {}
        primo = {self.formue[0].alder: self.formue_start}
        primo.update({nu.alder: foer.i_plan + foer.uden_for_plan for foer, nu in zip(self.formue, self.formue[1:])})
        return primo

    def aar_ved(self, alder: int) -> Aarsresultat:
        return next(a for a in self.aar if a.alder == alder)
