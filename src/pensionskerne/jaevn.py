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


def beregn_jaevn(
    raekker: tuple[Aarsresultat, ...],
    engangs_i_buffer: dict[int, float],
    rente: float | Sequence[float],
    inflation: float,
    beregningsaar: int,
) -> JaevnUdbetaling | None:
    if not raekker:
        return None
    vaekst = 1 + inflation
    n = len(raekker)
    # Bufferens rente pr. række (023a); fast rente er det samme hvert år.
    renter = list(rente) if isinstance(rente, Sequence) else [rente] * n
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
            nv_vaekst += vaekst ** (k - i) * faktor
            c = nv_ind / nv_vaekst
            if c <= bedste_c + 1e-12 * max(1.0, abs(c)):  # sidste minimum: så lange segmenter som muligt
                bedste_c, bedste_k = min(c, bedste_c), k
        for t in range(i, bedste_k + 1):
            niveau[t] = bedste_c * vaekst ** (t - i)
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
            ind_buffer=engangs_i_buffer.get(r.alder, 0.0),
        ))

    niveau_real = niveau[0] / vaekst ** (raekker[0].kalenderaar - beregningsaar)
    return JaevnUdbetaling(niveau_foerste_aar=niveau[0], niveau_real=niveau_real, aar=tuple(aar))
