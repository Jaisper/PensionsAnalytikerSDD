# Feature Specification: Usikkerhed med Monte Carlo

**Feature Branch**: `016-monte-carlo`

**Created**: 2026-10-27

**Status**: Draft – modnes

**Input**: Roadmappen: "Kræver kilde til udsving (Rådet for Afkastforventninger) og en hurtigere
beregning: ca. 200 forløb i baggrunden, vifte med 10/50/90 %."

**Grundlag**:
- 023: afkast pr. år i kernen. Uden den er Monte Carlo ikke mulig.
- 018 og 019: deterministiske scenarier. De forbliver standard.
- Rådet for Afkastforventninger: forventet afkast og standardafvigelse pr. aktivklasse (1–5 år,
  6–10 år og over 10 år).

## Problem

Faste scenarier viser ikke, hvor sandsynligt et udfald er. En vifte (10 %, 50 % og 90 % af
forløbene) gør usikkerheden synlig, men den er let at misforstå og bygger på statistiske
antagelser, som skal være tydelige.

## Forslag til metode

- Afkast pr. år trækkes fra en normalfordeling med Rådets forventede afkast og standardafvigelse
  for en antaget portefølje, fast frø (deterministisk, Princip VI).
- Inflationen holdes fast i første omgang (et fald i inflation og afkast følges ofte ad; den
  sammenhæng kræver en kilde).
- 200 forløb regnes i baggrunden som 018, med afbrydelse.
- Visningen er en vifte for det faste beløb pr. år og en sætning: "I 9 af 10 forløb er det faste
  beløb mindst X kr."

## Clarifications (forslag i kursiv)

- [NEEDS CLARIFICATION: Porteføljen. Rådet giver tal pr. aktivklasse, ikke for en pension.
  *Forslag: en antaget fordeling efter alder (fx mere obligationer tæt på pension), vist som
  antagelse. Alternativt én standardafvigelse, som borgeren kan ændre.*]
- [NEEDS CLARIFICATION: Ydelse. 200 beregninger à 50–150 ms er 10–30 s i browseren. *Forslag: en
  forenklet hurtig vej i kernen for forløbene (fx uden fastpunktets ekstra runder, varm start fra
  hovedberegningen) med en målt tolerance mod den fulde beregning.*]
- [NEEDS CLARIFICATION: Levetid som tilfældig? *Forslag: nej i første omgang. Levetid forbliver et
  scenarie (019).*]

## Requirements (udvalg)

- **FR-001**: Fast frø og samme resultat i Pyodide og CPython.
- **FR-002**: Fordeling, parametre og kilde vises (Princip V). Ingen sandsynlighed uden kilde.
- **FR-003**: Viften er tilvalg og må ikke forsinke hovedtallet.
- **SC**: 200 forløb på under 10 s for en enlig i browseren, eller viften vises gradvist.

## Afhængigheder og størrelse

- Forudsætter 023. Stor, især ydelsen. Den har størst risiko for misforståelse og bør have
  brugertest (som 020 SC-004).
