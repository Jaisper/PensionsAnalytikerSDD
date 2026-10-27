# Feature Specification: 017b Nettoløn til sammenligning og regulerede indbetalinger

**Feature Branch**: `017b-nettoloen` | **Oprettet**: 2026-10-27 | **Status**: Implementeret 2026-10-27
**Input**: Brugerønske: "giver det ikke god mening at angive månedligt netto beløb til rådighed efter
skat, så man bedre kan sammenligne med pensionsudbetalingerne? … det beløb [indbetalingen] skal
reguleres med inflation, og afkast deraf være det samme som for pensionerne."

## Krav

- **FR-001**: Med løn viser resultatet lønnen efter AM-bidrag, skat og pensionsindbetaling pr. måned
  i dagens kroner ved hovedtallet. Det er gennemsnittet af lønkildens netto i årene før stopalderen.
  Det faste beløb vises også som en procentdel af nettolønnen. Visningen omformaterer kun kernens tal.
- **FR-002**: Den årlige pensionsindbetaling er i dagens kroner og reguleres med satsreguleringen
  (standard: inflationen), som lønnen. `loenvaekst` er realvækst oven i (standard 0).
- **FR-003**: Afkastet af indbetalingerne er det samme som for ordningen (uændret fra 001).
- **FR-004**: Uden løn vises ingen nettoløn. I den samlede visning for et par vises den ikke.

## Afvigelse fra legacy

Legacy holdt indbetalingen fast i kroner (lønvækst 0), så indbetalingen faldt i købekraft hvert år.
Det er en modelantagelse, ikke lov. Differentialtesten mod legacy bruger inflation 0 og er uændret.

## Succeskriterier

- **SC-001**: Indbetalingen i et år er lig startbeløbet gange reguleringsfaktoren (golden test).
- **SC-002**: Nettolønnen i visningen er lig gennemsnittet af lønkildens netto i dagens kroner
  afrundet til hele hundrede (app-test), og den står ved hovedtallet (browsertest).
