# Feature Specification: Bjælker, der trækkes

**Feature Branch**: `006-traek-bjaelker`

**Created**: 2026-10-25

**Status**: Draft

**Input**: "De enkelte ordninger findes både som bar og som start og længde. Kan det hele ikke
bygges ind i bar/punkt, der så skal flyttes og skydes?"

**Grundlag**:
- Feature 004 (tidslinje)
- Åbent fund B1 i `specs/004-tidslinje/ux-evaluering.md`
- Legacy-tidslinjen, hvor bjælkerne kunne trækkes
- Princip X og WCAG 2.2 AA (2.5.7 Dragging Movements og 2.5.8 Target Size)

## Clarifications

### Session 2026-10-25

- Q: Hvordan flyttes en bjælke uden at trække (WCAG 2.5.7)? → A: Et klik eller tryk på
  bjælken vælger den og viser ‹ ›-knapper for start og eventuelt varighed. Tastaturet virker
  altid.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Flyt en ordning ved at trække i bjælken (Priority: P1)

Hver ordning er én bjælke under grafen. Ratepension og livsvarig vises som en bjælke, og
engangsbeløb som et punkt. Borgeren trækker bjælken til venstre eller højre for at ændre
startalderen. Bjælken følger musen eller fingeren år for år, og under trækket viser bjælken
alderen ("67–76 år"). Når borgeren slipper, regner kernen igen, og graf og hovedtal opdateres.

**Why this priority**: Én kontrol i stedet for to. Bjælken er både visningen og kontrollen, som
i legacy.

**Independent Test**: Træk en ratepensions bjælke 2 år mod højre. Starten flytter sig 2 år,
længden er uændret, og hovedtallet regnes igen.

**Acceptance Scenarios**:

1. **Given** en ratepension 65–74, **When** bjælken trækkes 2 år mod højre, **Then** er den
   67–76, og der regnes igen, når den slippes.
2. **Given** en ordning med tidligste alder 63, **When** bjælken trækkes længere mod venstre,
   **Then** stopper den ved 63.
3. **Given** en aldersopsparing (punkt), **When** punktet trækkes, **Then** ændres
   udbetalingsåret.
4. **Given** folkepensionsbjælken, **When** den trækkes mod højre, **Then** udskydes
   folkepensionen (0 til registrets maksimum), og den kan ikke trækkes før
   folkepensionsalderen.

---

### User Story 2 - Ændr ratepensionens varighed i bjælkens ende (Priority: P1)

Ratepensionens bjælke har et greb i højre ende. Trækker man i det, bliver udbetalingsperioden
længere eller kortere, inden for 10–30 år, mens starten er uændret.

**Acceptance Scenarios**:

1. **Given** en ratepension 65–74 (10 år), **When** grebet trækkes 5 år mod højre, **Then**
   er den 65–79 (15 år).
2. **Given** 10 år, **When** grebet trækkes mod venstre, **Then** stopper den ved 10 år
   (registrets minimum).

---

### User Story 3 - Uden at trække: klik, ‹ › og tastatur (Priority: P1)

Et klik eller tryk på en bjælke vælger den. Under bjælken vises "Start ‹ 65 år ›" og for
ratepension også "Varighed ‹ 10 år ›". Med tastaturet har bjælken og grebet fokus som skydere:
piletaster ±1 år, Page Up/Down ±5 og Home/End til grænserne. Skærmlæsere hører fx
"Velliv · Ratepension, start, 65 år".

**Why this priority**: WCAG 2.2 AA kræver et alternativ til at trække (2.5.7). Uden det
fjerner vi tilgængelighed i forhold til 004's skydere.

**Acceptance Scenarios**:

1. **Given** en bjælke, **When** den klikkes, **Then** vises ‹ ›-knapperne for netop den
   ordning, og › flytter starten 1 år.
2. **Given** fokus på en bjælke, **When** man trykker → to gange, **Then** er starten 2 år
   senere, og der regnes igen.
3. **Given** en skærmlæser, **When** bjælken får fokus, **Then** oplyses navn, rolle
   (skyder), værdi og grænser.

### Edge Cases

- Et klik uden bevægelse (under 4 px) er et klik og ikke et træk.
- Trækket fortsætter, selvom musen forlader sporet (pointer capture).
- Kernen afviser ændringen: bjælken springer tilbage, og kernens besked vises ved rækken (som
  i 004).
- På en smal skærm (360 px) er bjælken stadig mindst 24 px høj, og punkter er mindst 24 px
  brede (2.5.8).
- Engangsbeløb ved samme alder ligger oven i hinanden. Hver ordning har sin egen række, så de
  kan altid skelnes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hver ordnings bjælke eller punkt MUST være kontrollen for start. Der må ikke
  være separate start- eller varighedsskydere under tidslinjen.
- **FR-002**: Træk MUST ske år for år på grafens aldersakse (samme pixel pr. år som i 004) og
  holdes inden for grænserne fra API'et (tidligste alder og ratepensionens periode 10–30 år,
  Princip II).
- **FR-003**: Ratepension MUST have et greb i højre ende til varigheden.
- **FR-004**: Folkepensionsbjælken MUST kunne trækkes for udskydelse (0 til registrets
  maksimum).
- **FR-005**: Der MUST være et alternativ uden træk: klik for at vælge og ‹ ›-knapper (WCAG
  2.5.7).
- **FR-006**: Bjælke og greb MUST være `role="slider"` med `aria-valuemin`, `-max`, `-now` og
  `-valuetext` og kunne betjenes med pil, Page Up/Down og Home/End.
- **FR-007**: Mål for klik og tryk MUST være mindst 24×24 px (WCAG 2.5.8).
- **FR-008**: Kernen regner, når en ændring er afsluttet (slip, klik på ‹ › eller tast, med
  300 ms debounce som i 004). Under trækket vises kun brugerens valg (Princip I).
- **FR-009**: Datapanelet MUST forblive synkront med tidslinjen (som i 004).
- **FR-010**: Princip X gælder: axe 0 fejl og ingen vandret scroll ved 360 px.

## Success Criteria *(mandatory)*

- **SC-001**: Hver ordning har én kontrol (bjælke eller punkt) i stedet for 1–2 skydere.
  Tidslinjen fylder mindst 30 % mindre i højden end i 004 ved 1366 px.
- **SC-002**: Efter et træk vises et nyt hovedtal på under 1 sekund efter slip.
- **SC-003**: Bjælkens startkant ligger højst 2 px fra grafens søjle (som i 004).
- **SC-004**: axe 0 fejl. Alle mål er mindst 24 px.

## Assumptions

- Hver ordning har sin egen række (som i 004). Der stables ikke flere ordninger i én række.
- Finjustering med ‹ › og tastatur er godt nok på små skærme, hvor ét år kun er få pixel.
