# Feature Specification: "Finder bedste plan …" i stedet for talrullen

**Feature Branch**: `032-finder-plan`

**Created**: 2026-11-01

**Status**: Draft

**Input**: "I stedet for de snurrende tal kan vi så ikke bare vise 'Finder bedste plan …'"

**Grundlag**:
- Feature 028 (talrullen), som denne erstatter. Problemet derfra står stadig: under søgningen må
  hovedtallet ikke vise den egne plans beløb (fx 0 kr.)
- Princip I (kun visning) og X (WCAG 2.2 AA)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tekst i stedet for tal under søgningen (Priority: P1)

Mens den bedste plan søges, står der "Finder bedste plan …" i stedet for hovedtallet. Når planen er
fundet, står beløbet der.

**Acceptance Scenarios**:

1. **Given** første resultat, **While** planen søges, **Then** står der "Finder bedste plan …" og
   ikke et beløb eller "om måneden efter skat".
2. **Given** at søgningen er færdig, **Then** står det endelige beløb, og planen meldes klar
   (`body[data-plan=klar]`).
3. **Given** at borgeren flytter en bjælke under søgningen, **Then** står den nye plans beløb, når
   det er regnet.

## Requirements *(mandatory)*

- **FR-001**: Teksten MUST være den samme med og uden "reducer bevægelse". Intet bevæger sig.
- **FR-002**: Linjen under hovedtallet viser kun fremdriften (`progress`), så teksten ikke står to gange.
- **FR-003**: FR-004 og FR-005 fra 028 gælder fortsat (afhængige tekster skjult, kasseret søgning).

## Success Criteria *(mandatory)*

- **SC-001**: `tests/browser/test_finder_plan.py` og hele browsersuiten er grønne.
