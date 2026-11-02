"""Jævn udbetaling (US7) — en præsentationsmodel, ikke lovgivning.

Det faste beløb er det højeste forløb, der er konstant i dagens købekraft og kun stiger, når der
kommer flere penge — uden nogensinde at låne (feature 010). Bufferen er opsparing uden for
pension (engangsbeløb og det, der spares op i år med høje udbetalinger). Den forrentes med
afkastet før skat; skatten af afkastet (kapitalindkomst, feature 009) regnes i år-for-år-
beregningen og trækkes fra årets nettoudbetaling her, sammen med skatten af aktieindkomst og
aktiesparekonto og løbende indskud på den (`Aarsresultat.disponibel`, 013b).

Algoritmen er forbrugsudjævning med likviditetsbegrænsning, segment for segment: fra år i med
buffer B er niveauet

    c = min over k ≥ i af (B + Σ_{t=i..k} I_t / (1+r)^(t−i)) / Σ_{t=i..k} g^(t−i) / (1+r)^(t−i)

hvor I_t er årets indbetaling til bufferen og g = 1 + inflation. Segmentet varer til og med det
sidste k, der giver minimum; her er bufferen netop opbrugt, og næste segment begynder. Bufferen
er derfor aldrig negativ, niveauet er ikke-faldende i dagens kroner, og bufferen ender i 0.
(Før 010 blev grundniveauet finansieret af nutidsværdien af alle senere udbetalinger, så de
første år kunne låne af fremtiden.)

Faldende udbetalinger (033): med en forbrugsprofil vægtes hvert år med w_t, så nævneren bliver
Σ w_t · g^(t−i) / (1+r)^(t−i), og niveauet i år t er c · w_t. Kravene ovenfor gælder for c: ingen
lån, ingen negativ buffer, og c er ikke-faldende. Uden profil er w_t = 1.

Betalinger sker primo året. Beløb er kr. pr. år (månedligt = / 12 i præsentationen).
"""
from __future__ import annotations

import math
from collections.abc import Sequence

from .model import Aarsresultat, JaevnAar, JaevnUdbetaling

# Bufferens fastpunkt (feature 009) — modelparametre, ikke lovsatser: stop, når den jævne
# udbetaling ændrer sig mindre end 1 kr. om måneden, og giv op (med advarsel) efter 12 iterationer.
# Ved ældrechecks formuegrænse flytter det sidste år over grænsen sig ét år pr. iteration; med
# depot og aktiesparekonto (013b) kan det tage op til ca. 10 (loftet var 8 før 013b).
BUFFER_TOLERANCE_KR = 1.0  # pr. måned
BUFFER_MAKS_ITERATIONER = 12

# Forbrugsprofilens bånd (033) — modelparametre, ikke lovsatser: fem år ad gangen fra stopalderen
# og et sidste bånd fra 85 til planens slutning.
BAAND_AAR = 5
SIDSTE_BAAND_FRA = 85
KORTESTE_BAAND = 3  # et kortere bånd før 85 lægges sammen med det foregående
FORBRUG_MIN = 0.5  # et senere bånd må højst falde til halvdelen af det første (FR-005)


def baand(start_alder: int, slut_alder: int) -> tuple[tuple[int, int], ...]:
    """Båndene (fra, til, begge med) fra `start_alder` til `slut_alder`. Et bånd før 85, der er
    kortere end `KORTESTE_BAAND`, lægges sammen med det foregående (fx 79–84 i stedet for 79–83 og 84)."""
    ud: list[tuple[int, int]] = []
    fra = start_alder
    while fra <= slut_alder:
        til = slut_alder if fra >= SIDSTE_BAAND_FRA else min(fra + BAAND_AAR - 1, SIDSTE_BAAND_FRA - 1, slut_alder)
        if ud and fra < SIDSTE_BAAND_FRA and til - fra + 1 < KORTESTE_BAAND:
            ud[-1] = (ud[-1][0], til)
        else:
            ud.append((fra, til))
        fra = til + 1
    return tuple(ud)


def vaegte(procenter: Sequence[float], start_alder: int, aldre: Sequence[int]) -> dict[int, float]:
    """Vægten pr. alder: 1.0 før stopalderen, ellers båndets procent. Er der flere bånd end
    procenter (stopalderen er flyttet frem), gælder den sidste procent."""
    if not procenter:
        return {alder: 1.0 for alder in aldre}
    starter = [fra for fra, _ in baand(start_alder, max([start_alder, SIDSTE_BAAND_FRA] + list(aldre)))]
    ud = {}
    for alder in aldre:
        nr = sum(1 for fra in starter if fra <= alder) - 1
        ud[alder] = 1.0 if nr < 0 else procenter[min(nr, len(procenter) - 1)]
    return ud


def beregn_jaevn(
    raekker: tuple[Aarsresultat, ...],
    engangs_i_buffer: dict[int, float],
    rente: float | Sequence[float],
    inflation: float,
    beregningsaar: int,
    vaegt: Sequence[float] | None = None,
) -> JaevnUdbetaling | None:
    if not raekker:
        return None
    vaekst = 1 + inflation
    n = len(raekker)
    # Bufferens rente pr. række (023a); fast rente er det samme hvert år.
    renter = list(rente) if isinstance(rente, Sequence) else [rente] * n
    w = list(vaegt) if vaegt is not None else [1.0] * n
    normal = [r.disponibel for r in raekker]
    indbetaling = [normal[t] + engangs_i_buffer.get(r.alder, 0.0) for t, r in enumerate(raekker)]

    niveau = [0.0] * n
    buffer = 0.0
    i = 0
    while i < n:
        bedste_c, bedste_k = math.inf, i
        nv_ind, nv_vaekst = buffer, 0.0
        faktor = 1.0
        for k in range(i, n):
            if k > i:
                faktor /= 1 + renter[k - 1]
            nv_ind += indbetaling[k] * faktor
            nv_vaekst += w[k] * vaekst ** (k - i) * faktor
            c = nv_ind / nv_vaekst
            if c <= bedste_c + 1e-12 * max(1.0, abs(c)):  # sidste minimum: så lange segmenter som muligt
                bedste_c, bedste_k = min(c, bedste_c), k
        for t in range(i, bedste_k + 1):
            niveau[t] = bedste_c * w[t] * vaekst ** (t - i)
            buffer = (buffer + indbetaling[t] - niveau[t]) * (1 + renter[t])
        i = bedste_k + 1

    buffer = 0.0
    aar: list[JaevnAar] = []
    for t, r in enumerate(raekker):
        forskel = niveau[t] - normal[t]
        buffer = (buffer + engangs_i_buffer.get(r.alder, 0.0) - forskel) * (1 + renter[t])
        aar.append(JaevnAar(
            alder=r.alder, jaevn=niveau[t], normal=normal[t],
            fra_buffer=max(0.0, forskel), til_buffer=max(0.0, -forskel), buffer_rest=buffer,
            ind_buffer=engangs_i_buffer.get(r.alder, 0.0), vaegt=w[t],
        ))

    niveau_real = niveau[0] / vaekst ** (raekker[0].kalenderaar - beregningsaar)
    return JaevnUdbetaling(niveau_foerste_aar=niveau[0], niveau_real=niveau_real, aar=tuple(aar))
