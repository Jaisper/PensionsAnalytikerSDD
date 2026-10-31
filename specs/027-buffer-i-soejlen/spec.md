# Feature Specification: Bufferen i søjlerne

**Feature Branch**: `027-buffer-i-soejlen`

**Created**: 2026-10-31

**Status**: Draft

**Input**: "Jeg synes buffergrafen – den under hovedgrafen – er lidt ulogisk. Ville det ikke give
mere mening at vise, hvor meget der er i bufferen, og så i grafen ovenpå vise, hvilken andel – ny
farve for buffer – der kommer fra bufferen?"

**Grundlag**:
- Feature 008 (engangsbeløb og buffer i grafen) og 010 (ingen lån)
- Kernens jævne udbetaling: `JaevnAar.fra_buffer` og `til_buffer` (ingen ny beregning, Princip I)
- Princip X: konsekvent farvelogik og svaret først

## Problem

Hovedgrafen viste kun indtægterne pr. kilde og en stiplet linje for det faste beløb. Når søjlen var
under linjen, skulle man selv regne ud, at forskellen kom fra bufferen. Buffergrafen nedenunder viste
saldoen. Hvor pengene til det faste beløb kom fra, stod ingen steder.

## Clarifications

### Session 2026-10-31

- Q: Hvordan vises de år, hvor indtægterne er over linjen, og resten sættes til side? → A: Delen
  over linjen skraveres og hedder "Sættes til side".
- Q: Hvad står over linjen ud over det, der sættes til side? → A: Skat af opsparingen og indskud
  på den (013b). Udjævningen fordeler `disponibel`, dvs. netto efter de to. De skraveres også, og
  tooltippet og tabellen viser dem hver for sig.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Se hvad der kommer fra bufferen (Priority: P1)

I år, hvor indtægterne er under det faste beløb, får søjlen et stykke øverst i en ny farve, "Fra din
buffer". Søjlen når så op til linjen.

**Acceptance Scenarios**:

1. **Given** en kapitalpension i bufferen og ingen andre indtægter ved 65 år, **Then** er hele
   søjlen ved 65 "Fra din buffer" og når linjen.
2. **Given** et år under linjen, **Then** er kilderne plus "Fra din buffer" lig linjen plus skat af
   opsparingen og indskud.

### User Story 2 - Se hvad der sættes til side (Priority: P1)

I år, hvor indtægterne er over det faste beløb, er delen over linjen skraveret: "Sættes til side".

**Acceptance Scenarios**:

1. **Given** et år, hvor kernen sætter noget til side, **Then** er søjlen skraveret fra linjen til
   toppen.
2. **Given** tooltippet for året, **Then** står beløbet, der sættes til side, og skatten af
   opsparingen hver for sig.

### User Story 3 - Bufferens saldo nedenunder (Priority: P2)

Grafen under hovedgrafen hedder "Din buffer" og har samme farve som "Fra din buffer".

## Requirements *(mandatory)*

- **FR-001**: Visningen MUST levere `graf.fra_buffer` og `graf.til_side` (`buffer`, `skat`,
  `indskud`) pr. år i dagens kroner pr. måned. Det er ren omformatering af kernens tal.
- **FR-002**: "Fra din buffer" MUST være en serie i søjlens stak med farven `--kilde-buffer`.
- **FR-003**: Delen over linjen MUST skraveres. Skraveringen er kun tegning.
- **FR-004**: Farveforklaringen, tabellen, tooltippet, "Sådan læser du grafen" og diagrammets
  `aria-label` MUST nævne "Fra din buffer" og "Sættes til side".
- **FR-005**: Buffergrafen MUST bruge `--kilde-buffer`.
- **FR-006**: Dagens og årets kroner (020b) MUST gælde for de nye tal.

## Success Criteria *(mandatory)*

- **SC-001**: Kilder plus "Fra din buffer" er lig linjen plus det, der står over den, i alle profiler
  i `tests/app/test_visning.py`.
- **SC-002**: Browsertestene for 008 og 027 er grønne, og axe finder ingen fejl.
