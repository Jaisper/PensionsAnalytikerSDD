# Feature Specification: Udjævning uden lån

**Feature Branch**: `010-ingen-laan`

**Created**: 2026-10-25

**Status**: Draft

**Input**: "Buffergraf ikke særlig intuitiv – den går i minus over lange stræk; bør vises og
forklares bedre." (Skærmbillede: bufferen var cirka −1,4 mio. kr. fra 65 til 75 år.)

## Clarifications

### Session 2026-10-25

- Q: Hvordan håndteres år, hvor det faste beløb kræver penge, man først får senere? → A: **Aldrig
  lån.** Det faste beløb kan kun stige, når pengene er kommet. Bufferen er altid 0 eller mere.

## Problem

Den jævne udbetaling (feature 001, US7) finansierede grundniveauet med nutidsværdien af *alle*
løbende udbetalinger, også dem, der kommer senere. I planer med store senere udbetalinger lånte de
første år derfor af fremtiden. Bufferen blev negativ, og det faste beløb kunne ikke nås uden lån.
For engangsbeløb gjaldt allerede reglen "ingen lån på forhånd". Nu gælder den alt.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Det faste beløb kan altid betales (Priority: P1)

Borgeren ser det højeste beløb, der kan bruges hvert år uden nogensinde at låne. Det er konstant i
dagens kroner og stiger kun, når der kommer flere penge (fx når en senere pension begynder).
Bufferen går aldrig i minus og ender i 0.

**Acceptance Scenarios**:

1. **Given** en plan, hvor de senere år giver mere end de første, **Then** er bufferen ≥ 0 i alle
   år. Det faste beløb er lavere de første år og stiger, når pengene kommer.
2. **Given** en plan, hvor de første år giver mest (fx ratepension først), **Then** er det faste
   beløb konstant i hele perioden (som før).
3. **Given** hovedtallet, **Then** er det det laveste faste beløb (det første niveau), og teksten
   siger, hvornår og til hvad det stiger.

### User Story 2 - Buffergrafen forstås uden forklaring udefra (Priority: P1)

Grafen hedder "Din opsparing uden for pension". Under grafen står, hvordan den skal læses: Den
vokser, når du får mere udbetalt end det faste beløb, og den bruges, når du får mindre. Den går
aldrig i minus. Når den rammer 0, stiger det faste beløb, så snart flere penge kommer.

### Edge Cases

- Ingen udbetalinger i de første år: Det faste beløb er 0, indtil pengene kommer. Grafen og
  hovedtallet viser det ærligt.
- Kapitalindkomst og formue (009) følger den nye buffer. Fastpunktet er uændret.

## Requirements *(mandatory)*

- **FR-001**: Den jævne udbetaling MUST være det højeste ikke-faldende (i dagens kroner) forløb,
  hvor bufferen aldrig er negativ og ender i 0. Det beregnes segmentvis: niveau = min over k af
  (buffer + nutidsværdi af indbetalinger til og med år k) / (nutidsværdi af niveauets vækst til
  og med år k).
- **FR-002**: Advarslen `JAEVN_FORUDSAETTER_SENERE_UDBETALINGER` udgår, fordi der ikke længere
  lånes.
- **FR-003**: Hovedtallets tekst siger, at beløbet stiger, når flere udbetalinger begynder, og
  ikke kun ved engangsbeløb.
- **FR-004**: Buffergrafens titel og forklaring som i US2. axe 0 fejl og ingen vandret scroll ved
  360 px.

## Success Criteria *(mandatory)*

- **SC-001**: Bufferen er ≥ 0 (inden for 1 kr.) for alle golden cases, alle egenskabstest-profiler
  og den syntetiske rapport.
- **SC-002**: Det faste beløb er ikke-faldende i dagens kroner, og bufferen ender i 0.
- **SC-003**: Golden cases regnet i hånden for segmentalgoritmen.
