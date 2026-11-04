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
from dataclasses import dataclass, replace
from datetime import date
from statistics import NormalDist
from typing import Callable, Sequence

from .model import Antagelser, Fremskrivning, Ordning, Pensionsprofil
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


# ── Trin 3: de tre forløb gennem fremskrivningen ─────────────────────────────

STIER = ("hoej", "forventet", "lav")


def aktieandel(o: Regelopslag, aar_til_pension: int) -> float:
    """Standardprofilens aktieandel (registret): lineært mellem punkterne (år til pension, andel);
    uden for punkterne gælder det nærmeste."""
    punkter = sorted(o.v("branchestandard.standardprofil"), reverse=True)
    if aar_til_pension >= punkter[0][0]:
        return punkter[0][1]
    for (a1, v1), (a2, v2) in zip(punkter, punkter[1:]):
        if aar_til_pension >= a2:
            return v2 + (v1 - v2) * (aar_til_pension - a2) / (a1 - a2)
    return punkter[-1][1]


def _udbetalingsaar(ordning: Ordning, alder_nu: int, o: Regelopslag, antagelser: Antagelser) -> tuple[int, int]:
    """Første udbetalingsalder og antal udbetalinger, som fremskrivningen regner dem."""
    s = max(ordning.udbetaling_start_alder, alder_nu)
    form = ordning.udbetalingsform if ordning.type == "kapitalpension" else ordning.type
    if form == "ratepension":
        aar = ordning.udbetaling_aar or o.v("ordning.ratepension.min_aar")
        return s, max(1, aar - max(0, alder_nu - ordning.udbetaling_start_alder))
    if form == "livsvarig":
        return s, max(antagelser.livsvarig_min_aar, antagelser.livsvarig_horisont_alder - s)
    if form == "portioner":
        return s, ordning.udbetaling_aar or 1
    return s, 1  # engangsbeløb


def ordningens_stier(ordning: Ordning, profil: Pensionsprofil, beregningsdato: date, o: Regelopslag,
                     antagelser: Antagelser = Antagelser()) -> dict[str, dict[int, float]]:
    """Ordningens tre afkaststier efter PAL-skat pr. kalenderår (trin 1–2 og PAL i trin 3).

    Tidspunkt k er k år fra i dag. Indbetalingen i året lægges til ved årets slutning, som i
    fremskrivningen, og reguleres med satsreguleringen. Udbetalingsfaktoren er 1 i opsparingen og
    (n − i − 1)/(n − i) ved den i'te af n udbetalinger (henstillingen appendix 1)."""
    alder_nu = beregningsdato.year - profil.foedselsdato.year
    s, n = _udbetalingsaar(ordning, alder_nu, o, antagelser)
    bidrag_slut = s if profil.loen is None or profil.loen.stop_alder is None else min(s, profil.loen.stop_alder)
    blanding = o.v("branchestandard.blanding")
    foerste_udbetaling = s - alder_nu
    tider: list[Tidspunkt] = []
    for k in range(foerste_udbetaling + n):
        andel = ordning.aktieandel if ordning.aktieandel is not None else aktieandel(o, s - (alder_nu + k))
        mu, sigma = mu_sigma({blanding["aktier"]: andel, blanding["obligationer"]: 1 - andel},
                             forudsaetninger(o, k + 1))
        i = k - foerste_udbetaling
        faktor = 1.0 if i < 0 else (n - i - 1) / (n - i)
        indbetaling = (ordning.aarlig_indbetaling * (1 + o.satsregulering) ** (k - 1)
                       if 0 < k and alder_nu + k - 1 < bidrag_slut else 0.0)
        tider.append(Tidspunkt(indbetaling=indbetaling, udbetalingsfaktor=faktor, mu=mu, sigma=sigma))
    if len(tider) < 2:
        return {navn: {} for navn in STIER}
    stier = trin2(tider, trin1(ordning.saldo, tider), o.v("branchestandard.fraktiler"))
    pal = o.v("pal.sats")
    efter_pal = lambda sti: {beregningsdato.year + k: r * (1 - pal) for k, r in enumerate(sti)}  # noqa: E731
    return {"hoej": efter_pal(stier.hoej), "forventet": efter_pal(stier.forventet), "lav": efter_pal(stier.lav)}


def beregn_branchestandard(profil: Pensionsprofil, antagelser: Antagelser, satsaar: int, beregningsdato: date,
                           beregn: Callable[..., Fremskrivning], *, buffer_start: Fremskrivning | None = None,
                           med_spaend: bool = True) -> Fremskrivning:
    """Branchestandarden: hver ordning får sine tre stier, og den almindelige fremskrivning regnes på
    hver (FR-006). Satser reguleres og omregnes til dagens kroner med Rådets langsigtede inflation
    (forenkling: én inflation). Bufferen og opsparing uden for pension følger det faste afkast.
    Uden spænd (optimeringen) regnes kun det forventede forløb."""
    inflation = Regelopslag(satsaar, beregningsdato.year, 0.0).v("raadet.inflation")["aar_11"]
    o = Regelopslag(satsaar, beregningsdato.year, inflation)
    stier = {x.id: ordningens_stier(x, profil, beregningsdato, o, antagelser) for x in profil.ordninger}
    egne = replace(antagelser, beregningsgrundlag="egne", inflation=inflation, satsregulering=None)

    def forloeb(navn: str, start: Fremskrivning | None) -> Fremskrivning:
        ordninger = tuple(replace(x, afkast_forloeb=stier[x.id][navn]) for x in profil.ordninger)
        return beregn(replace(profil, ordninger=ordninger), egne, satsaar, beregningsdato, buffer_start=start)

    o.marker("forenkling:branchestandard_en_inflation")
    if profil.opsparing:
        o.marker("forenkling:branchestandard_opsparing_fast_afkast")

    def med_spor(f: Fremskrivning, prognose: dict[str, Fremskrivning] | None = None) -> Fremskrivning:
        forenklinger = tuple(x for x in o.flag if x not in f.aar[0].flag) if f.aar else ()
        aar = ((replace(f.aar[0], flag=f.aar[0].flag + forenklinger),) + f.aar[1:]) if f.aar else f.aar
        return replace(f, aar=aar, antagelser=replace(f.antagelser, beregningsgrundlag="branchestandard"),
                       prognose=prognose, sporing_samlet=tuple(dict.fromkeys(f.sporing_samlet + tuple(o.brugt))))

    res = forloeb("forventet", buffer_start)
    prognose = {navn: med_spor(forloeb(navn, res)) for navn in ("hoej", "lav")} if med_spaend else None
    return med_spor(res, prognose)
