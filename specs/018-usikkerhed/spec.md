# Feature Specification: Usikkerhed om afkast og inflation

**Feature Branch**: `018-usikkerhed`

**Created**: 2026-10-26

**Status**: Draft

**Input**: "Vi vil gerne have introduceret usikkerheder i forhold til afkastgrad og inflation –
ligesom i legacy. +/- 1 % i afkast og +/- 0,5 % i inflation."

**Grundlag**:
- Legacy: `generer_scenarier` i `legacy/engine.py` (tabel 4). Fire scenarier med afkast ±1 og ±2
  procentpoint fra borgerens eget valg. Inflationen holdes fast, og afkastet sættes ikke under 0.
- 007/008: hovedtallet er det faste beløb hele perioden (kr./md. efter skat, dagens kroner).
- 016 (Monte Carlo) i roadmappen er stadig en senere feature. 018 er den enkle, deterministiske
  udgave.

## Afvigelser fra legacy

| Legacy | 018 | Hvorfor |
|---|---|---|
| Afkast ±1 og ±2 procentpoint | Afkast ±1 procentpoint | Ønsket |
| Inflationen holdes fast | Inflation ±0,5 procentpoint, også kombineret med afkastet | Ønsket. Inflationen ændrer både købekraften og reguleringen af satserne |
| Tabel i den AI-genererede rapport | Spænd under hovedtallet og en tabel i "Prøv andre forudsætninger" | Ingen AI (Princip XI). Spændet ses der, hvor tallet står |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Se, hvor meget beløbet kan svinge (Priority: P1)

Under hovedtallet står spændet: "Hvis afkast og inflation bliver anderledes: mellem X og Y kr."
Et link fører til en tabel med alle scenarier.

**Acceptance Scenarios**:

1. **Given** et resultat, **Then** vises spændet, når scenarierne er regnet. Indtil da står
   "Regner usikkerheden …".
2. **Given** tabellen, **Then** har den syv rækker:
   - dit valg
   - lavere afkast og højere afkast (±1 procentpoint)
   - højere inflation og lavere inflation (±0,5 procentpoint)
   - ugunstigt (afkast −1, inflation +0,5) og gunstigt (afkast +1, inflation −0,5)
3. **Given** et par (012), **Then** følger spændet og tabellen den valgte fane (Dig, Partner,
   Samlet).

### User Story 2 - Siden forbliver hurtig (Priority: P1)

**Acceptance Scenarios**:

1. **Given** at borgeren ændrer noget, mens scenarierne regnes, **Then** droppes de gamle
   scenarier, og den nye beregning venter højst på ét scenarie.

### Edge Cases

- **Afkast eller inflation på 0 %**: Scenariet sættes til 0 og ikke negativt (som legacy). Er det
  lig dit valg, vises det stadig, så tabellen altid har syv rækker.
- **Beregningsfejl i et scenarie**: Rækken viser "–", og spændet bruger de øvrige.

## Requirements *(mandatory)*

- **FR-001**: Scenarierne MUST defineres ét sted (indgangslaget) med spændene 1 procentpoint for
  afkast og 0,5 procentpoint for inflation. Det er antagelser, ikke lov. De vises som antagelser.
- **FR-002**: Hvert scenarie MUST regnes med kernen præcis som hovedtallet. Kun afkast og
  inflation ændres (satsreguleringen følger inflationen som i dag).
- **FR-003**: Visningen MUST kun omformatere tallene (Princip I).
- **FR-004**: Scenarierne MUST regnes i baggrunden efter resultatet og afbrydes ved ændringer.
- **FR-005**: Princip X: tabellen har en caption og kolonneoverskrifter, axe 0 fejl og ingen
  vandret scroll ved 360 px.

## Success Criteria *(mandatory)*

- **SC-001**: Eksisterende tests og golden cases er uændrede.
- **SC-002**: Scenariernes beløb er lig `beregn` med de ændrede antagelser (test).
- **SC-003**: Samme beløb i Pyodide og CPython.
- **SC-004**: Alle seks scenarier er regnet inden for 3 s i browseren for en typisk profil.
