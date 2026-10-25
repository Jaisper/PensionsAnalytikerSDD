# Feature Specification: Engangsbeløb og buffer i grafen, fast beløb som hovedtal

**Feature Branch**: `008-buffer-i-grafen`

**Created**: 2026-10-25

**Status**: Draft

**Input**:
- "Tæller kapitalpension med som buffer her? Eller hvordan skal jævnt beløb fortolkes?"
- "Lav feature 8, hovedtal viser også fast beløb."

**Grundlag**:
- Feature 001 US7 (jævn udbetaling)
- Feature 007 (fund E1 og målet "fast beløb hele perioden")
- Princip V (sporbarhed) og X (klarhed)

## Problem

Grafen viser den stiplede linje "Jævnt fordelt", men ikke engangsbeløbene, som finansierer
den. En kapitalpension på 925.000 kr. forsvinder fra billedet. Hovedtallet var desuden niveauet
efter det sidste engangsbeløb, mens optimeringen (007) bruger det faste beløb hele perioden. De
to tal kunne afvige.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Se hvor engangsbeløbet bliver af (Priority: P1)

I grafen står der ved udbetalingsåret fx "Kapitalpension 555.000 kr. → buffer". For en direkte
udbetaling står der "→ udbetales". Det samme står i listen under grafen, så skærmlæsere også
får det.

**Acceptance Scenarios**:

1. **Given** en kapitalpension som buffer ved 65 år, **Then** viser grafen en markør ved 65 med
   ordningens navn, nettobeløbet i dagens kroner og "→ buffer".
2. **Given** at "Brug som buffer" slås fra, **Then** står der "→ udbetales".

---

### User Story 2 - Se bufferen år for år (Priority: P1)

Under grafen viser en lille graf på samme aldersakse, hvor meget der står i bufferen hvert år:
- Den falder, når søjlerne er under linjen.
- Den vokser, når de er over.
- Den ender i 0.
- Negativ buffer (lån af senere udbetalinger) vises under 0-linjen i en advarselsfarve.

**Acceptance Scenarios**:

1. **Given** en plan med jævn udbetaling, **Then** vises buffergrafen med samme alder pr. kolonne
   som hovedgrafen (højst 2 px forskel).
2. **Given** en plan uden jævn udbetaling, **Then** vises den ikke.

---

### User Story 3 - Forstå linjen og hovedtallet (Priority: P1)

Linjen hedder "Fast beløb, hvis du udjævner". Under grafen står kort, hvordan den læses. Når
søjlen er under linjen, bruger du af bufferen. Når den er over, sparer du op. Hovedtallet er
det faste beløb hele perioden, som er det samme som optimeringen bruger. Hvis beløbet stiger
senere, når et engangsbeløb lander, nævnes det i teksten under hovedtallet.

**Acceptance Scenarios**:

1. **Given** en plan uden senere engangsbeløb, **Then** er hovedtallet lig linjen i hele
   perioden.
2. **Given** et engangsbeløb, der lander senere, **Then** er hovedtallet det laveste (første)
   niveau. Teksten siger "Fra du er X år, stiger det til ca. Y kr.".
3. **Given** "Find bedste plan" og "Anvend", **Then** er hovedtallet lig forslagets beløb
   (lukker E1).

## Requirements *(mandatory)*

- **FR-001**: Kernen MUST oplyse hvert engangsbeløb: ordning, type, alder, netto og om det er
  buffer (`Fremskrivning.engangsbeloeb`). Der må ikke være ny beregning (Princip I).
- **FR-002**: Visningen MUST levere `graf.engangs` (pr. ordning, i dagens kroner) og
  `graf.buffer` (bufferen pr. alder i dagens kroner). Det er ren omformatering.
- **FR-003**: Hovedtallet MUST være det laveste jævne beløb i perioden, dvs. det faste beløb hele
  perioden. Er der et senere spring, oplyses det som `senere`.
- **FR-004**: Grafen MUST vise markører for engangsbeløb med tekst. De står også i listen under
  grafen og i tabellen.
- **FR-005**: Buffergrafen MUST dele aldersakse med hovedgrafen.
- **FR-006**: Linjens navn og forklaringen MUST være på dansk og i klart sprog (Princip VIII og
  X).
- **FR-007**: axe 0 fejl og ingen vandret scroll ved 360 px.

## Success Criteria *(mandatory)*

- **SC-001**: Hovedtallet er lig optimeringens "fast beløb hele perioden" for samme plan (test).
- **SC-002**: Summen af engangsbeløbene i `graf.engangs` er lig kernens `engangsbeloeb_netto` pr.
  år (test).
- **SC-003**: Buffergrafens kolonner ligger højst 2 px fra hovedgrafens.
