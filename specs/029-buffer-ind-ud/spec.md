# Feature Specification: Bufferen ind, ud og saldo

**Feature Branch**: `028-talrulle` (sammen med 028)

**Created**: 2026-10-31

**Status**: Draft

**Input**: "Buffer fremgår ikke af buffer?! Ser ud som vi starter i nul … se på begge – de skulle gerne
følges ad. Men jeg synes ikke, det giver mening!"

**Grundlag**:
- Feature 027 (bufferen i søjlerne) og 008 (buffergrafen)
- Princip I: kernen bogfører, hvad der kommer ind i bufferen. Visningen regner ikke.

## Problem

Søjlegrafen viste "Fra din buffer" fra 64 år, mens buffergrafen stod på næsten 0. Begge var
korrekte: buffergrafen viste saldoen ved årets udgang, efter at årets engangsbeløb var kommet ind og
forbruget trukket fra. Men det, der kom ind, så man ikke. Derfor lignede det et forbrug af en tom
buffer.

## Clarifications

### Session 2026-10-31

- Q: Hvordan skal buffergrafen følge søjlegrafen? → A: Søjler pr. år i samme kolonner: op er det,
  der kommer ind (engangsbeløb og opsparing) og sættes til side, ned er "Fra din buffer". Linjen er
  saldoen.
- Q: Er saldoen fra arbejdsårene "ind" ved stopalderen? → A: Nej. Den er allerede i bufferen. Kun nye
  penge tæller som ind.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Se pengene komme ind og gå ud (Priority: P1)

Under søjlegrafen viser buffergrafen pr. år: "Ind i bufferen" (engangsbeløb og opsparing), "Sættes
til side" (skraveret) og "Fra din buffer" (nedad, samme farve som i søjlegrafen). Linjen er saldoen
ved årets udgang.

**Acceptance Scenarios**:

1. **Given** en kapitalpension i bufferen ved 65 år, **Then** står den som "Ind i bufferen" ved 65.
2. **Given** et år med "Fra din buffer" i søjlegrafen, **Then** har buffergrafen en søjle nedad
   samme år og omvendt.
3. **Given** afkast 0, **Then** er saldoen sidste års saldo plus ind og til side minus fra bufferen.

## Requirements *(mandatory)*

- **FR-001**: Kernen MUST bogføre `JaevnAar.ind_buffer`: engangsbeløb og opsparing, der kommer ind
  i året. Saldoen, der føres videre fra arbejdsårene ved stopalderen, tæller ikke med. Ingen ny regel.
- **FR-002**: Visningen MUST levere `graf.buffer_ind` pr. år i dagens kroner.
- **FR-003**: Buffergrafen MUST dele kolonner med søjlegrafen.
- **FR-004**: Farveforklaring, tabel, forklaringstekst og `aria-label` MUST nævne ind, ud og saldo.

## Success Criteria *(mandatory)*

- **SC-001**: `tests/golden/test_buffer_ind.py`: saldoen går op med ind, til side og fra bufferen,
  også med arbejdsår, bank og løbende indskud.
- **SC-002**: Browsertestene for 008, 027 og 029 er grønne.
