# Feature Specification: Find bedste plan og engangsbeløb som buffer

**Feature Branch**: `007-optimering`

**Created**: 2026-10-25

**Status**: Draft

**Input**:
- "Hvad med min gamle optimeringsfunktion, der regner et skatteoptimalt udbetalingsforløb ud?"
- "Og man skal kunne vælge at bruge engangsudbetalinger som 'buffer' ligesom i legacy-løsningen."

**Grundlag**:
- `legacy/sekventering.py` (mål, værn og søgning)
- Legacy-spec US4 (`legacy/specs/001-pensionsanalytiker-baseline/spec.md`)
- Kernens jævne udbetaling (feature 001, US7) med `Ordning.i_buffer`
- Princip I, II, V og X

## Clarifications

### Session 2026-10-25

- Q: Hvad optimeres? → A: Som i legacy: det højeste faste månedsbeløb efter skat i dagens
  købekraft, uden et dybere eller længere indkomsthul end borgerens nuværende plan.
- Q: Hvordan vises forslaget? → A: Forskellen, hvad der flyttes, og knapperne "Anvend" og
  "Behold min plan". Forslaget vises også som spøgelsesbjælker i tidslinjen. Der er ingen
  top 5 eller følsomhedstal.
- Q: Engangsbeløb som buffer? → A: Ja, valgfrit pr. engangsbeløb og slået til fra start (som i
  legacy). Et engangsbeløb, der ikke er buffer, udbetales direkte og flyttes ikke af
  optimeringen.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find bedste plan (Priority: P1)

På resultatsiden trykker borgeren "Find bedste plan". Kernen afprøver kombinationer af
startalder pr. ordning, ratepensionens varighed, året for engangsbeløb (kun buffer-beløb) og
udskydelse af folkepensionen. Hver kombination regnes fuldt igennem med skat, modregning i
pensionstillæg og ældrecheck. Borgeren får forslaget med det højeste faste månedsbeløb, som
ikke giver et dybere eller længere hul end den nuværende plan.

**Why this priority**: Den største værdi ud over selve beregningen. Det var en kernefunktion i
legacy.

**Independent Test**: Kør optimeringen på en fast profil. Forslaget er mindst lige så godt som
udgangspunktet, overholder alle lovlige grænser, og samme input giver samme svar.

**Acceptance Scenarios**:

1. **Given** en beregnet plan, **When** borgeren trykker "Find bedste plan", **Then** vises
   "Med denne plan får du X kr. mere om måneden (Y kr. i stedet for Z kr.)" og en liste over
   ændringerne (fx "Velliv · Ratepension: start 67 → 70 år, varighed 10 → 15 år").
2. **Given** et forslag, **When** borgeren trykker "Anvend", **Then** flyttes ordningerne i
   tidslinje og datapanel, og hovedtallet bliver forslagets beløb.
3. **Given** et forslag, **When** borgeren trykker "Behold min plan", **Then** forsvinder
   forslaget, og intet ændres.
4. **Given** at den nuværende plan allerede er den bedste, der kan findes, **Then** står der
   "Din plan er allerede den bedste, vi kan finde".
5. **Given** at ikke alle kombinationer er afprøvet, **Then** oplyses det, fx "Vi har afprøvet
   1.500 af 2,1 mio. mulige kombinationer".
6. **Given** at optimeringen kører, **Then** vises fremdrift, og siden fryser ikke.

---

### User Story 2 - Engangsbeløb som buffer eller direkte udbetaling (Priority: P1)

For hver aldersopsparing og kapitalpension kan borgeren vælge "Brug som buffer". Det er slået
til fra start. Så fordeles beløbet over årene i det faste månedsbeløb. Slås det fra, udbetales
beløbet direkte det år og indgår ikke i det faste månedsbeløb.

**Acceptance Scenarios**:

1. **Given** en aldersopsparing, **When** "Brug som buffer" slås fra i guiden eller
   datapanelet, **Then** indgår beløbet ikke længere i hovedtallet, og det vises som
   engangsudbetaling.
2. **Given** tidslinjen, **Then** er et buffer-beløb et udfyldt punkt, og en direkte
   udbetaling er en ring. Rækken skriver "til buffer" eller "udbetales direkte".
3. **Given** et engangsbeløb, der ikke er buffer, **When** optimeringen kører, **Then** flyttes
   det ikke.

### Edge Cases

- Ingen ordninger: kun folkepensionens udskydelse optimeres.
- Et forslag, kernen afviser (fx under tidligste alder), indgår aldrig. Det tæller som ikke
  gennemførligt.
- Borgeren ændrer planen, mens optimeringen kører: forslaget hører til den gamle plan og
  vises ikke.
- Ventetillægget ved udskudt folkepension er kernens beregning med de advarsler, der allerede
  findes (750 timer og andre udbetalingsformer).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Optimeringen MUST ligge i kernen som en ren, deterministisk funktion
  (`pensionskerne.optimering.optimer`). Hver kandidat regnes med `beregn` (Princip I). Der må
  ikke være AI eller tilfældighed.
- **FR-002**: **Mål**: det faste månedsbeløb efter skat i dagens kroner, som borgeren kan leve af
  i hele perioden, dvs. det laveste jævne beløb fra udgangspunktets første udbetaling. År uden
  udbetaling tæller som 0. *Ændret i T003:* Hovedtallet alene (niveauet efter det sidste
  engangsbeløb) belønnede at skubbe engangsbeløb sent, så de første år blev lavere.
- **FR-003**: **Værn** i forhold til borgerens nuværende plan (fra legacy, tilpasset kernens
  jævne model). En kandidat forkastes, hvis den:
  1. har et lavere fast beløb end 70 % af udgangspunktets hovedtal i et år fra den første
     udbetaling
  2. har en lavere laveste rå udbetaling (uden udjævning) end 97 % af udgangspunktets laveste
     (dybde)
  3. har flere år med rå udbetaling under 85 % af sit eget faste beløb end udgangspunktet
     (varighed)
  4. har en dybere negativ buffer end udgangspunktets værste plus én måneds fast beløb
     (bufferdækning)
  5. har flere år med negativ buffer end udgangspunktet (buffer-varighed)
- **FR-004**: **Søgerum**:
  - startalder pr. ordning fra den tidligste lovlige alder til folkepensionsalderen plus
    registrets maksimale opsættelse
  - ratepensionens varighed inden for registrets grænser
  - folkepensionens udskydelse fra 0 til maksimum
  - engangsbeløb, der ikke er buffer, er faste
  Grænserne kommer fra registret og kernens regler (Princip II).
- **FR-005**: **Søgning**: Alle kombinationer afprøves, hvis der er højst
  `maks_evalueringer`. Ellers bruges en deterministisk grådig koordinatsøgning fra flere
  startpunkter (som legacy): nuværende plan og kvantilerne 0, ¼, ½, ¾ og 1. Udgangspunktet
  indgår altid.
- **FR-006**: Resultatet MUST oplyse udgangspunktets og forslagets månedsbeløb, ændringerne,
  antal afprøvede og mulige kombinationer, og om søgningen var udtømmende.
- **FR-007**: Optimeringen MUST køre i workeren med fremdrift. Andre beregninger venter på den.
- **FR-008**: `i_buffer` MUST kunne vælges pr. engangsbeløb i guiden og datapanelet. Det er
  slået til fra start.
- **FR-009**: Princip X: axe 0 fejl og ingen vandret scroll ved 360 px, også med forslaget vist.

## Success Criteria *(mandatory)*

- **SC-001**: Forslaget er altid mindst lige så godt som udgangspunktet og overholder alle
  grænser og værn (egenskabstest).
- **SC-002**: Samme input giver samme forslag i CPython og Pyodide.
- **SC-003**: Optimeringen er færdig på under 10 s i browseren for en profil med 4 ordninger.
- **SC-004**: Efter "Anvend" er det faste beløb hele perioden lig forslagets beløb.

## Assumptions

- Legacy kunne også sprede et engangsbeløb over flere år ("kapital_rate"). Kernen har ikke
  den udbetalingsform, så den er ikke med.
- Partnerens plan optimeres ikke. Partnerens indkomst indgår, som den er (som i legacy).
- Legacy viste top 5 og følsomhed. Det er fravalgt (Princip X: klarhed før fuldstændighed).
