"""Jævn udbetaling (US7) — en præsentationsmodel, ikke lovgivning.

Engangsbeløb (der ikke er fravalgt) lægges i en buffer — opsparing uden for pension, der
forrentes med afkastet før skat (feature 009). Skatten af afkastet (kapitalindkomst) regnes i
kernens år-for-år-beregning og betales af bufferen: den trækkes fra årets almindelige
nettoudbetaling her. Ud fra bufferen og nettoudbetalingerne beregnes ét niveau, der stiger med
inflationen (konstant i dagens købekraft):

- Grundniveauet finansieres af nutidsværdien af alle almindelige nettoudbetalinger plus
  engangsbeløb, der er modtaget i det første år.
- Hvert senere engangsbeløb giver et selvstændigt tillæg fra det år, det modtages. Niveauet
  kan derfor kun stige, og der regnes ikke med et engangsbeløb, før det er modtaget.

Betalinger sker primo året. Beløb er kr. pr. år (månedligt = / 12 i præsentationen).
"""
from __future__ import annotations

from .model import Aarsresultat, JaevnAar, JaevnUdbetaling

# Bufferens fastpunkt (feature 009) — modelparametre, ikke lovsatser: stop, når den jævne
# udbetaling ændrer sig mindre end 1 kr. om måneden, og giv op (med advarsel) efter 8 iterationer.
BUFFER_TOLERANCE_KR = 1.0  # pr. måned
BUFFER_MAKS_ITERATIONER = 8


def _faktor(aar: int, vaekst: float, rente: float) -> float:
    return sum((vaekst / (1 + rente)) ** i for i in range(aar))


def beregn_jaevn(
    raekker: tuple[Aarsresultat, ...],
    engangs_i_buffer: dict[int, float],
    rente: float,
    inflation: float,
    beregningsaar: int,
) -> JaevnUdbetaling | None:
    if not raekker:
        return None
    vaekst = 1 + inflation
    n = len(raekker)
    foerste_alder = raekker[0].alder
    normal = [r.netto_i_alt - r.skat_kapitalindkomst for r in raekker]

    nv_normal = sum(x / (1 + rente) ** i for i, x in enumerate(normal))
    grund = (engangs_i_buffer.get(foerste_alder, 0.0) + nv_normal) / _faktor(n, vaekst, rente)
    tillaeg = {
        alder - foerste_alder: beloeb / _faktor(n - (alder - foerste_alder), vaekst, rente)
        for alder, beloeb in engangs_i_buffer.items()
        if foerste_alder < alder < foerste_alder + n
    }

    buffer = 0.0
    aar: list[JaevnAar] = []
    for i, r in enumerate(raekker):
        buffer += engangs_i_buffer.get(r.alder, 0.0)
        jaevn = grund * vaekst ** i + sum(t * vaekst ** (i - j) for j, t in tillaeg.items() if j <= i)
        forskel = jaevn - normal[i]
        buffer = (buffer - forskel) * (1 + rente)
        aar.append(JaevnAar(
            alder=r.alder, jaevn=jaevn, normal=normal[i],
            fra_buffer=max(0.0, forskel), til_buffer=max(0.0, -forskel), buffer_rest=buffer,
        ))

    niveau_real = grund / vaekst ** (raekker[0].kalenderaar - beregningsaar)
    return JaevnUdbetaling(niveau_foerste_aar=grund, niveau_real=niveau_real, aar=tuple(aar))
