# Feature Specification: Kapitalpensionens muligheder og en realistisk buffer

**Feature Branch**: `009-kapitalpension`

**Created**: 2026-10-25

**Status**: Draft

**Input** (produktejer):
- "Kapitalpension kan ændres til en ratepension eller livrente, så længe afgiften ikke er
  betalt. Det er ikke nødvendigt for at bevare PAL-beskatningen: du kan vælge engangsbeløb eller
  udbetaling i mindre portioner i højst 20 år. Ved omlægning til rate skifter beskatningen fra
  40 % afgift til personlig indkomst. Ratepension modregnes i pensionstillægget; det gør
  kapitalpension ikke."
- "Man skal også kunne angive, om der tidligere er svaret afgift på en kapitalpension (37,3 % i
  2013)."
- "Kør den fulde 009 – det skal være best practice."

## Lovgrundlag (Princip III, verificeret 2026-10-25, se research.md)

| Regel | Kilde | Status |
|---|---|---|
| Kapitalpension udbetales tidligst ved pensionsudbetalingsalderen og senest 20 år efter | PBL § 12, stk. 1, nr. 3, og § 10. JV C.A.10.2.5.4.1 (PBL § 25, stk. 1, nr. 7; forlænget fra 15 til 20 år 1.1.2018) | verificeret |
| Delvis udbetaling (en del ad gangen) | PBL § 26. JV C.A.10.2.5.4.1 | verificeret |
| Afgift 40 % af det udbetalte beløb | PBL § 25, stk. 1, nr. 1 (allerede i registret) | verificeret |
| Overførsel af kapitalpension til ordning med løbende udbetalinger (livrente) eller rateordning behandles ikke som ud- og indbetaling | PBL § 41, stk. 1, nr. 4 og 6 | verificeret |
| Ratepensionens udbetalingsperiode (10 år til 30 år efter pensionsudbetalingsalderen) | PBL § 11 A (allerede i registret) | verificeret |
| Afgiftsberigtiget kapitalpension (omlagt 2013–2014 mod 37,3 % afgift) udbetales skattefrit | Skatteministeriet, notat 5.10.2013. PBL § 10 A / § 12 A | sekundær |
| PAL 15,3 % af afkastet | Pensionsafkastbeskatningsloven § 2 | verificeret |
| Positiv nettokapitalindkomst indgår i grundlaget for bundskat og kommuneskat. I mellem- og topskat kun over et bundfradrag på 55.000 kr. (2026). Skatteloft 42 % | PSL §§ 6, 7, stk. 1, og 19, stk. 2. Skatteministeriets satsoversigt 2026 | verificeret |
| Kapitalindkomst indgår i indtægtsgrundlaget for pensionstillæg | Lov om social pension § 29 (domænegrundlag A5) | verificeret |
| Likvid formue pr. 1. januar over grænsen giver ingen ældrecheck | Lov om social pension § 72 d, stk. 2 (allerede i registret) | verificeret |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Afgiften er allerede betalt (Priority: P1)

På kapitalpensionens kort kan borgeren markere "Afgiften er allerede betalt (fx ved omlægning i
2013–2014)". Udbetalingen er så skattefri. Ordningen hedder stadig kapitalpension. Den laves ikke
stille om til aldersopsparing, som PDF-indlæsningen gjorde.

**Acceptance Scenarios**:

1. **Given** 500.000 kr. kapitalpension med betalt afgift, **Then** er nettoudbetalingen
   500.000 kr. og ikke 300.000 kr.
2. **Given** en PensionsInfo-rapport med betalt afgift, **Then** er markeringen sat, og typen er
   kapitalpension.
3. **Given** betalt afgift, **Then** kan ordningen ikke omlægges til rate eller livrente. Der er
   ingen afgift at spare, og den er nu en aldersforsikring.

---

### User Story 2 - Udbetaling i portioner (Priority: P1)

Borgeren vælger "I portioner over N år". Hvert år udbetales en lige stor andel af restværdien.
Der er 40 % afgift af hver portion, eller 0 %, hvis afgiften er betalt. Resten bliver i ordningen
og forrentes med afkast efter PAL. Sidste portion skal ligge senest 20 år efter
pensionsudbetalingsalderen.

**Why this priority**: Pengene bliver i pensionen (15,3 % PAL) i stedet for i banken. Der er
skat af kapitalindkomst, pensionstillægget nedsættes, og der er formue i forhold til ældrechecken.
Det er ofte bedre, og det har været usynligt.

**Acceptance Scenarios**:

1. **Given** kapitalpension 600.000 kr. i portioner over 6 år, **Then** er der 6 udbetalinger
   efter § 11 A-formlen (restværdi divideret med resterende år), og hver nettoportion er 60 % af
   bruttoportionen.
2. **Given** at den sidste portion ville ligge mere end 20 år efter pensionsudbetalingsalderen,
   **Then** afviser kernen med en dansk feltbesked.
3. **Given** portioner, **Then** nedsætter de ikke pensionstillægget (de er ikke personlig
   indkomst).

---

### User Story 3 - Omlægning til ratepension eller livrente (Priority: P2)

Borgeren kan vælge "Omlæg til ratepension over N år" eller "Omlæg til livrente". Udbetalingen
beskattes så som personlig indkomst, modregnes i pensionstillægget og følger ratepensionens
regler.

**Acceptance Scenarios**:

1. **Given** en kapitalpension omlagt til ratepension over 10 år, **Then** regnes den som en
   ratepension (§ 11 A-rater, personlig indkomst, indgår i indtægtsgrundlaget).
2. **Given** en omlægning, **Then** står der en advarsel om, at det kræver en overførsel (PBL
   § 41), som skal aftales med selskabet, før udbetalingen begynder.

---

### User Story 4 - Bufferen regnes som den virkelige opsparing (Priority: P1)

Engangsbeløb i bufferen står som opsparing uden for pension. Derfor:
- afkastet beskattes som kapitalindkomst (bund- og kommuneskat, og mellem- og topskat over
  bundfradraget, med skatteloft 42 %)
- afkastet indgår i indtægtsgrundlaget for pensionstillægget
- opsparingen pr. 1. januar tæller med i ældrechecks formuegrænse

Det erstatter den faste antagelse "27 % skat af afkastet" og advarslen
`BUFFER_YDELSE_FORENKLING`.

**Acceptance Scenarios**:

1. **Given** et stort engangsbeløb i bufferen, **Then** er der skat af kapitalindkomst i årene
   med afkast, og pensionstillægget er lavere end uden buffer.
2. **Given** en buffer over formuegrænsen 1. januar, **Then** er der ingen ældrecheck det år.
3. **Given** samme kapitalpension som engangsbeløb og i portioner, **Then** kan forskellen
   aflæses i det faste beløb hele perioden.

---

### User Story 5 - Optimeringen vælger udbetalingsform (Priority: P1)

"Find bedste plan" afprøver for hver kapitalpension (som ikke er fravalgt buffer):
- engangsbeløb
- portioner over 2 til N år
- omlægning til ratepension over 10 til 30 år
- omlægning til livrente

Omlægning afprøves kun, når afgiften ikke er betalt. Forslaget siger fx "Kapitalpension: ét beløb
→ i portioner over 8 år".

### Edge Cases

- Kapitalpension uden kendt pensionsudbetalingsalder: Fristen på 20 år regnes fra den udledte
  tidligste alder (samme som i dag).
- Negativ buffer (lån af senere udbetalinger) giver ingen kapitalindkomst. Det er en forenkling,
  som allerede advares om.
- Engangsbeløb, der udbetales direkte (ikke buffer), indgår ikke i bufferens formue og afkast.
  Borgeren har valgt at bruge dem.
- Afkast af borgerens egen "anden kapitalindkomst" behandles som hidtil (forenkling, markeret).

## Requirements *(mandatory)*

- **FR-001**: `Ordning.afgift_betalt` (kapitalpension) MUST give 0 % afgift.
- **FR-002**: `Ordning.udbetalingsform` for kapitalpension ∈ {engangs, portioner, ratepension,
  livsvarig}. Portioner og ratepension bruger `udbetaling_aar`.
- **FR-003**: Portioner: rater efter § 11 A-formlen af restværdien, afgift pr. portion, og
  sidste portion senest pensionsudbetalingsalderen + 20 år (registret).
- **FR-004**: Omlægning: Ordningen regnes som ratepension eller livsvarig. Den er ikke tilladt med
  betalt afgift. Der gives en advarsel om overførsel (PBL § 41).
- **FR-005**: Bufferens afkast før skat = afkast efter PAL / (1 − PAL-sats). Det er en antagelse:
  bufferen investeres som pensionen. Afkastet er positiv kapitalindkomst. Formuen pr. 1. januar
  er bufferen ved årets start.
- **FR-006**: Skat af kapitalindkomst efter PSL (bund og kommune, mellem og top over
  bundfradraget, skatteloft 42 %). Den opgøres som marginal skat oven i den personlige indkomst og
  betales af bufferen.
- **FR-007**: Kapitalindkomst og formue afhænger af bufferen, som afhænger af den jævne
  udbetaling. Kernen MUST løse det deterministisk ved fastpunkt-iteration (højst N gange) og
  advare, hvis den ikke konvergerer.
- **FR-008**: Alle nye satser og regler MUST stå i registret med kilde og status (Princip II).
- **FR-009**: Guide og datapanel: udbetalingsform, antal år og "afgiften er allerede betalt" på
  kapitalpension. Tidslinjen viser portioner og omlægning som bjælke med greb.
- **FR-010**: Optimeringen MUST afprøve udbetalingsformerne (US5) inden for grænserne og give
  samme forslag i CPython og browseren.
- **FR-011**: PDF-indlæsningen sætter `afgift_betalt` i stedet for at skifte type.
- **FR-012**: Princip X: axe 0 fejl, ingen vandret scroll ved 360 px, og forklaringer i klart
  sprog.

## Success Criteria *(mandatory)*

- **SC-001**: Golden cases for portioner, betalt afgift, omlægning og buffer med
  kapitalindkomst og formue er regnet i hånden fra loven.
- **SC-002**: Kernen konvergerer på 3 eller færre iterationer for golden cases og den syntetiske
  rapport.
- **SC-003**: "Find bedste plan" tager under 10 s i browseren for 4 ordninger, heraf 1
  kapitalpension.
- **SC-004**: Samme forslag i Pyodide og CPython.

## Assumptions

- Bufferen investeres med samme afkast før skat som pensionen og beskattes som kapitalindkomst
  (bank og obligationer). Aktieindkomst (27 %/42 %) er ikke modelleret. Det står som forudsætning.
- Udbetaling i portioner og omlægning kræver, at pensionsselskabet tilbyder det. Det står som
  advarsel.
- Ægtepars overførsel af uudnyttet bundfradrag for kapitalindkomst er ikke modelleret (55.000 kr.
  pr. person).
