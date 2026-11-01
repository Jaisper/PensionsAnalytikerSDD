# Feature Specification: Talrullen

**Feature Branch**: `028-talrulle`

**Created**: 2026-10-31

**Status**: Draft

**Input**: "Der står, man kan forvente 0 kr., mens den regner på udbetaling … ikke så checket. Kan vi
ikke lave lidt sjov og lave en enarmet tyveknægt-talrulle, der ruller rundt, indtil beregningen er
færdig?"

**Grundlag**:
- Feature 007b: den bedste plan findes automatisk efter første beregning
- Princip I (kun visning, tallet kommer fra kernen) og X (WCAG 2.2 AA, fejl og tomme tilstande)

## Problem

Under søgningen efter den bedste plan viste hovedtallet beløbet for borgerens egen plan. Det kan være
0 kr. (fx stop med at arbejde før første udbetaling), og teksten under ("0 % af din løn") bygger på
det. Borgeren ser et forkert svar i op til 10 sekunder.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Talrullen under søgningen (Priority: P1)

Mens den bedste plan søges, ruller hovedtallet som en enarmet tyveknægt. Når planen er fundet,
stopper hjulene ét ad gangen fra venstre og lander på beløbet. Teksterne, der bygger på beløbet,
er skjult imens.

**Acceptance Scenarios**:

1. **Given** første resultat, **While** planen søges, **Then** ruller hovedtallet, og der står
   ikke "0 kr.".
2. **Given** at søgningen er færdig, **Then** står det endelige beløb, og planen meldes klar
   (`body[data-plan=klar]`), når hjulene er stoppet.
3. **Given** en skærmlæser, **Then** hører den "Regner …" og ikke cifrene.
4. **Given** "reducer bevægelse" (prefers-reduced-motion), **Then** står der "… kr." uden rulning.
5. **Given** at borgeren flytter en bjælke under søgningen, **Then** lander rullen på det nye beløb
   og ruller ikke videre.

## Requirements *(mandatory)*

- **FR-001**: Hjulene MUST kun være visning. Beløbet er `dataset.vaerdi` fra kernen.
- **FR-002**: Hjulene MUST være `aria-hidden`. Skærmlæsere får "Regner …".
- **FR-003**: Uden bevægelse MUST der ikke rulle noget (WCAG 2.3.3).
- **FR-004**: `#hovedtal-forklaring`, `#hovedtal-loen` og `#hovedtal-spaend` MUST være skjult under
  søgningen. `#hovedtal-aendring` (fx "gemte beregning") bygger ikke på beløbet og vises.
- **FR-005**: Ændrer borgeren planen under søgningen, MUST rullen lande på den nye plans beløb, når
  det er regnet. Søgningen kasseres som før (007b).

## Success Criteria *(mandatory)*

- **SC-001**: `tests/browser/test_talrulle.py` og hele browsersuiten er grønne.
