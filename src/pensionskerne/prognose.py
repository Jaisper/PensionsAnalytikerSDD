"""Branchestandarden (feature 035): trin 1 og 2 i F&P's henstilling om pensionsprognoser.

Henstillingen (LP-information 20/20) pkt. 7.1 og appendix 1:

1. Middelværdi og varians af depotet fremregnes rekursivt uden omkostninger og PAL-skat, og 5 %- og
   95 %-fraktilerne findes ved en log-normal approksimation (Munk, bilag 3; Hessler, bilag 4).
2. Ud fra fraktildepoterne findes tre afkaststier: lav, forventet og høj.

Trin 3 (omkostninger, PAL-skat og kontoteknik på hver sti) er den almindelige fremskrivning.
Rene funktioner; satserne kommer fra registret via `Regelopslag`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Sequence

from .register.opslag import Regelopslag


@dataclass(frozen=True)
class Tidspunkt:
    """Et tidspunkt tₙ i fremregningen. `indbetaling` er I(tₙ). `udbetalingsfaktor` F(tₙ) er den del af
    depotet, der er tilbage lige efter udbetalingen (1 i opsparingen). `mu` (log-afkast efter
    investeringsomkostninger) og `sigma` gælder fra tₙ til tₙ₊₁."""
    indbetaling: float
    udbetalingsfaktor: float
    mu: float
    sigma: float
    laengde: float = 1.0  # tₙ₊₁ − tₙ i år


@dataclass(frozen=True)
class Fordeling:
    middel: float
    varians: float


@dataclass(frozen=True)
class Stier:
    """Afkast pr. skridt (fra tₙ₋₁ til tₙ, n = 1…), før omkostninger og PAL-skat."""
    lav: list[float]
    forventet: list[float]
    hoej: list[float]


def trin1(startdepot: float, tider: Sequence[Tidspunkt]) -> list[Fordeling]:
    """Middelværdi og varians af depotet ved hvert tidspunkt, efter indbetalingen (appendix 1):
    M(tₙ) = M(tₙ₋₁)·F(tₙ₋₁)·e^{μΔt} + I(tₙ) og
    V(tₙ) = F(tₙ₋₁)²·e^{2μΔt}·((V(tₙ₋₁) + M(tₙ₋₁)²)·e^{σ²Δt} − M(tₙ₋₁)²)."""
    m, v = startdepot + tider[0].indbetaling, 0.0
    ud = [Fordeling(m, v)]
    for forrige, nu in zip(tider, tider[1:]):
        f, dt = forrige.udbetalingsfaktor, forrige.laengde
        vaekst = math.exp(forrige.mu * dt)
        m, v = (m * f * vaekst + nu.indbetaling,
                f * f * vaekst * vaekst * ((v + m * m) * math.exp(forrige.sigma * forrige.sigma * dt) - m * m))
        ud.append(Fordeling(m, v))
    return ud


def fraktil(fordeling: Fordeling, p: float) -> float:
    """p-fraktilen af depotet under log-normal-antagelsen: exp(b·N⁻¹(p) + a − b²/2), hvor a = ln M og
    b² = ln(1 + V·e^{−2a}). Et tomt depot har fraktilen 0."""
    if fordeling.middel <= 0:
        return 0.0
    a = math.log(fordeling.middel)
    b2 = math.log(1 + fordeling.varians * math.exp(-2 * a))
    return math.exp(math.sqrt(b2) * NormalDist().inv_cdf(p) + a - b2 / 2)


def trin2(tider: Sequence[Tidspunkt], fordelinger: Sequence[Fordeling], fraktiler: Sequence[float]) -> Stier:
    """De tre afkaststier (appendix 1, trin 2). Middelstien er det forventede afkast e^{μΔt} − 1.
    Fraktilstien fra s til t er (depotₜ − præmieₜ) / (depotₛ · udbetalingsfaktorₛ) − 1. Er depotet
    tømt, så stien ikke kan beregnes, bruges afkastet fra seneste periode, hvor den kunne (løsning 1)."""
    p_lav, p_hoej = fraktiler

    def sti(p: float) -> list[float]:
        depoter = [fraktil(f, p) for f in fordelinger]
        ud: list[float] = []
        for n in range(1, len(tider)):
            grundlag = depoter[n - 1] * tider[n - 1].udbetalingsfaktor
            if grundlag > 0:
                ud.append((depoter[n] - tider[n].indbetaling) / grundlag - 1)
            else:
                ud.append(ud[-1] if ud else math.exp(tider[n - 1].mu * tider[n - 1].laengde) - 1)
        return ud

    forventet = [math.exp(t.mu * t.laengde) - 1 for t in tider[:-1]]
    return Stier(lav=sti(p_lav), forventet=forventet, hoej=sti(p_hoej))


# ── Rådets forudsætninger pr. år ─────────────────────────────────────────────

# Henstillingen pkt. 7.2: Rådets forudsætninger for år 1–5 bruges på de første fem år, for år 6–10 på
# årene 6–10 og for år 11+ på resten. Investeringsomkostningerne for år 1–10 bruges i alle ti år.
SIDSTE_AAR_KORT = 5
SIDSTE_AAR_MELLEM = 10


@dataclass(frozen=True)
class Forudsaetninger:
    """Rådets forudsætninger for ét år i fremregningen."""
    aktivklasser: list[str]
    afkast: list[float]
    investeringsomkostninger: list[float]
    standardafvigelse: list[float]
    korrelation: list[list[float]]
    inflation: float
    tilknytning: dict[str, str] | None = None  # 10 klasser → Rådets tre klasser fra år 11


def forudsaetninger(o: Regelopslag, aar: int) -> Forudsaetninger:
    """Forudsætningerne for år `aar` i fremregningen (1 = første år)."""
    inflation = o.v("raadet.inflation")
    if aar > SIDSTE_AAR_MELLEM:
        return Forudsaetninger(
            aktivklasser=o.v("raadet.lang.aktivklasser"), afkast=o.v("raadet.lang.afkast"),
            investeringsomkostninger=o.v("raadet.lang.investeringsomkostninger"),
            standardafvigelse=o.v("raadet.lang.standardafvigelse"), korrelation=o.v("raadet.lang.korrelation"),
            inflation=inflation["aar_11"], tilknytning=o.v("raadet.lang.tilknytning"))
    kort = aar <= SIDSTE_AAR_KORT
    return Forudsaetninger(
        aktivklasser=o.v("raadet.aktivklasser"),
        afkast=o.v("raadet.afkast.aar_1_5" if kort else "raadet.afkast.aar_6_10"),
        investeringsomkostninger=o.v("raadet.investeringsomkostninger.aar_1_10"),
        standardafvigelse=o.v("raadet.standardafvigelse"), korrelation=o.v("raadet.korrelation"),
        inflation=inflation["aar_1_5" if kort else "aar_6_10"])


def mu_sigma(vaegte: dict[str, float], f: Forudsaetninger) -> tuple[float, float]:
    """μ = ln(1 + Σ wᵢ·nettoafkastᵢ) og σ = √(wᵀSw) med S_ij = ρ_ij·σᵢ·σⱼ (appendix 1). Vægtene er pr.
    Rådets ti aktivklasser; fra år 11 lægges de sammen i de tre langsigtede klasser."""
    w = [0.0] * len(f.aktivklasser)
    for klasse, vaegt in vaegte.items():
        maal = f.tilknytning[klasse] if f.tilknytning is not None else klasse
        if maal not in f.aktivklasser:
            raise KeyError(klasse)
        w[f.aktivklasser.index(maal)] += vaegt
    netto = sum(wi * (a - c) for wi, a, c in zip(w, f.afkast, f.investeringsomkostninger))
    s = f.standardafvigelse
    varians = sum(w[i] * w[j] * f.korrelation[i][j] * s[i] * s[j] for i in range(len(w)) for j in range(len(w)))
    return math.log(1 + netto), math.sqrt(varians)
