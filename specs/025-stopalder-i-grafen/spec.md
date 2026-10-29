# Feature Specification: Stopalderen i grafen

**Feature Branch**: `025-stopalder-i-grafen`

**Created**: 2026-10-29

**Status**: Draft

**Input**: "Vil også gerne have, man kan rykke rundt på pensionsalder direkte i grafik, f.eks. ved
en dot under alder, der så kan rykkes fra tidligste pensionsudbetaling kan foretages."

**Grundlag**:
- Feature 006 (bjælker, der trækkes): samme kontrol, samme tastatur og samme ‹ ›
- Feature 017 (arbejdsår og løn): `loen.stop_alder` er det første år uden løn
- Princip X og WCAG 2.2 AA (2.5.7 Dragging Movements og 2.5.8 Target Size)

## Clarifications

### Session 2026-10-29

- Q: Hvad er "pensionsalder"? → A: Stopalderen fra feature 017, dvs. den alder, hvor lønnen
  stopper. Den står i guiden som "Jeg stopper med at arbejde som".
- Q: Hvilke grænser gælder? → A: Den laveste er den tidligste alder, hvor en af borgerens
  ordninger kan udbetales (oplyst af selskabet eller udledt efter loven). Har borgeren ingen
  ordninger, gælder lovens alder for en ordning uden oprettelsesdato. Den højeste er
  folkepensionsalderen. Står der allerede en stopalder uden for grænserne i guiden, er den selv
  grænsen. Grænserne kommer fra kernen (`graenser`), ikke fra brugerfladen (Princip II).
- Q: Finder vi den bedste plan igen, når punktet flyttes? → A: Nej. Det gør de andre bjælker
  heller ikke. Kernen regner igen, og "Find bedste plan" virker som før.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Flyt stopalderen i tidslinjen (Priority: P1)

Har borgeren en løn, får tidslinjen under grafen en øverste række, "Du stopper med at arbejde",
med et punkt ved stopalderen. Borgeren trækker punktet til venstre eller højre. Når punktet
slippes, regner kernen igen, og graf, hovedtal og feltet i guiden opdateres.

**Independent Test**: Med løn og stopalder 64 trækkes punktet 2 år mod venstre. Stopalderen er
62, og der regnes igen.

**Acceptance Scenarios**:

1. **Given** stopalder 64, **When** punktet trækkes 2 år mod venstre, **Then** er stopalderen 62,
   feltet "Jeg stopper med at arbejde som" viser 62, og kernen regner igen.
2. **Given** en tidligste udbetalingsalder på 63, **When** punktet trækkes længere mod venstre,
   **Then** stopper det ved 63.
3. **Given** folkepensionsalder 69, **When** punktet trækkes længere mod højre, **Then** stopper
   det ved 69.
4. **Given** ingen stopalder i guiden, **Then** står punktet ved folkepensionsalderen.
5. **Given** ingen løn, **Then** er der ingen række for stopalderen.

---

### User Story 2 - Uden at trække (Priority: P1)

Som i 006: klik vælger rækken og viser "Stopper ‹ 64 år ›". Punktet er en skyder for tastaturet
(pile, Page Up/Down og Home/End). Skærmlæsere hører "Du stopper med at arbejde, 64 år".

## Requirements *(mandatory)*

- **FR-001**: `graenser` giver `stopalder: {min, maks}` fra kernens regler.
- **FR-002**: Rækken vises kun, når den viste person har en løn. Under fanen "Partner" ændrer den
  partnerens stopalder.
- **FR-003**: Ændringen skrives i `person.loen.stop_alder` (eller partnerens) og i guidens felt.
- **FR-004**: Punktet følger grafens aldersakse som de andre rækker, er mindst 24×24 px og har
  `role="slider"`.

## Success Criteria *(mandatory)*

- **SC-001**: Browsertestene for 006 er uændret grønne (rapporten uden løn har stadig 5 rækker).
- **SC-002**: axe finder ingen fejl i tidslinjen med stopalder.
