# Feature Specification: Arv modtaget og givet

**Feature Branch**: `015-arv`

**Created**: 2026-10-27

**Status**: Draft – besluttet 2026-10-27 (som foreslået); clarify med primærkilder før plan

**Input**: 013's afgrænsning: "015 Arv: forventet arv modtaget (tidspunkt og interval, vist med og
uden), boafgift og tillægsboafgift, pensioner til begunstigede og 'bevar X til arvinger' som
begrænsning i optimeringen."

**Grundlag**:
- 013: restformuen (US4) er grundlaget for arv givet.
- 010: udjævningen bruger opsparingen op. "Bevar X" er en ny begrænsning.
- 022: pensioner til begunstigede ved død (samme regler).

## Problem

Mange forventer en arv eller vil efterlade noget til deres børn. Det påvirker, hvor meget man kan
bruge, men en forventet arv er usikker og må ikke få hovedtallet til at se for godt ud.

## Lovgrundlag (første research 2026-10-27)

| Kobling | Kilde | Status |
|---|---|---|
| Boafgift 15 % efter bundfradrag; bundfradrag 392.300 kr. i 2026 (pr. bo) | Boafgiftsloven; Skatteministeriets faktaark; Ældre Sagen | sekundær |
| Tillægsboafgift 25 % for andre end nær familie | Samme | sekundær |
| Ægtefæller og registrerede partnere betaler ikke boafgift | Samme | sekundær |
| Søskende uden tillægsboafgift fra 2027; søskendebørn (forslag, ikke vedtaget) | Ændringslov 2024; finanslovsforslag 2026 | uverificeret |
| Rater til andre end ægtefælle, eller engangsbeløb, beskattes med 40 % afgift | Den juridiske vejledning C.A.10.2.2.4.3 | sekundær |

## Clarifications

- **Besluttet 2026-10-27 (som foreslået):** Vises arv modtaget i hovedtallet? → nej. Hovedtallet er uden arv.
  "Med forventet arv" vises som et scenarie i "Hvad hvis …" (som 018).
- **Besluttet 2026-10-27 (som foreslået):** Usikkerhed om tidspunktet. → et interval (tidligst–senest), og
  scenariet bruger det seneste år (forsigtigt).
- **Besluttet 2026-10-27 (som foreslået):** Er arven modtaget netto eller brutto? → borgeren angiver det
  forventede beløb efter boafgift. Boafgiften regnes kun for arv givet.
- **Besluttet 2026-10-27 (som foreslået):** "Bevar X til arvinger". → udjævningen ender med X i dagens kroner i
  stedet for 0 (en ny randbetingelse i 010-algoritmen). Det faste beløb falder tilsvarende.

## User Scenarios (kort)

- **US1 (P1)**: "Med forventet arv" som scenarie: det faste beløb med og uden.
- **US2 (P2)**: "Bevar X til arvinger": det faste beløb, der kan bruges, når X skal stå tilbage.
- **US3 (P3)**: Arv givet: restformuen og pensioner til begunstigede efter boafgift og 40 %
  afgift, pr. arvingklasse.

## Afhængigheder og størrelse

- Bygger på 013 (restformue) og 022 (begunstigede). US1 er lille. US2 kræver en ændring i
  udjævningen (010) med egne golden cases. US3 er mellemstor.
