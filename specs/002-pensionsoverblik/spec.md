# Feature Specification: Pensionsoverblik

**Feature Branch**: `002-pensionsoverblik`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "Pensionsoverblik: brugerflade, der viser kernens fremskrivning for
en borger. Svaret først og progressiv afsløring, inspireret af velliv.dk-layout."

**Grundlag**:
- Forfatningens Princip X
- [docs/ux/designretning.md](../../docs/ux/designretning.md)
- Beregningskernen fra feature 001 ([kontrakt](../001-beregningskerne/contracts/kerne-api.md))

## Overblik

Første version af en brugerflade. Borgeren indtaster sine oplysninger i en kort guide og får
et overblik over sin forventede pension efter skat. Alle tal kommer fra beregningskernen
(Princip I). Indlæsning af PensionsInfo-PDF og AI-forklaring er senere features. Denne
feature gør det muligt at indtaste ordninger manuelt, så brugerfladen kan bruges og testes
uafhængigt af dem.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Se svaret: hvad får jeg om måneden? (Priority: P1)

Borgeren har indtastet sine oplysninger. Det første, hun ser, er ét tal: hvad hun kan
forvente at få udbetalt om måneden efter skat, i dagens kroner. Tallet har en kort sætning
om, hvad det dækker, og ét tydeligt næste skridt.

**Why this priority**: Det er det spørgsmål, borgeren kommer med. Legacy viste korrekte tal,
men begravede svaret i tabeller.

**Independent Test**: Med en kendt profil vises hovedtallet øverst på resultatsiden, og det
svarer til kernens jævne udbetaling (realværdi / 12), afrundet til hele hundrede kroner.

**Acceptance Scenarios**:

1. **Given** en beregnet profil, **When** resultatsiden vises, **Then** ses øverst ét
   hovedtal "ca. X kr. om måneden efter skat (i dagens kroner)" sammen med en sætning, der
   siger, fra hvilken alder beløbet gælder.
2. **Given** resultatsiden, **When** den vises på en 360 px bred skærm, **Then** er
   hovedtallet synligt uden at scrolle, og der er ingen vandret scroll.
3. **Given** resultatsiden, **When** den vises, **Then** står forbeholdet "information,
   ikke rådgivning" synligt på siden.

---

### User Story 2 - Hvad består beløbet af, og hvordan ændrer det sig over tid? (Priority: P1)

Under hovedtallet ser borgeren en graf over nettoudbetalingen pr. år, fordelt på kilder
(folkepension, ATP, ratepension, livsvarig, checks), og et kort pr. kilde med beløb og
periode.

**Why this priority**: Borgeren skal forstå, hvorfor beløbet ændrer sig, fx når en
ratepension stopper, eller folkepensionen begynder.

**Independent Test**: Graf og kort viser de samme beløb som kernens år-for-år-resultat. Hver
kilde har samme farve i graf og kort.

**Acceptance Scenarios**:

1. **Given** en profil med ratepension og folkepension, **When** grafen vises, **Then**
   ses et tydeligt skift i det år, ratepensionen stopper, og i det år, folkepensionen
   begynder.
2. **Given** kortene for kilderne, **When** borgeren aktiverer "Se detaljer →" på et kort,
   **Then** udfoldes brutto, skat og netto pr. år for den kilde.
3. **Given** grafen, **When** den bruges med tastatur eller skærmlæser, **Then** findes de
   samme tal som tabel (tilgængeligt alternativ).

---

### User Story 3 - Indtast mine oplysninger i en kort guide (Priority: P1)

Borgeren besvarer en kort guide i trin med ét emne pr. trin:
1. Om dig: fødselsdato, kommune, civilstand og folkekirke
2. Dine ordninger: type, saldo, indbetaling og start
3. Dine forventninger: afkast, inflation og pensionsalder (med forslag)

Hvert felt forklarer, hvorfor der spørges.

**Why this priority**: Uden input er der intet resultat. Til PDF-import findes (feature 003)
er manuel indtastning den eneste vej.

**Independent Test**: En ny bruger kan gennemføre guiden med en enkel profil (én
ratepension) på under 3 minutter. Ugyldigt input giver en dansk fejlbesked ved feltet.

**Acceptance Scenarios**:

1. **Given** guiden, **When** borgeren skriver en fødselsdato før 1.7.1955, **Then** vises
   en dansk forklaring ved feltet (kernens valideringsbesked) og intet resultat.
2. **Given** trinet med ordninger, **When** borgeren tilføjer en ratepension, **Then** ses
   kun de felter, der er relevante for ratepension.
3. **Given** et felt med et fagudtryk (fx "livsvarig pension"), **When** borgeren aktiverer
   (i), **Then** ses en forklaring på én til to linjer.
4. **Given** et trin, **When** borgeren går tilbage, **Then** er de indtastede værdier
   bevaret.

---

### User Story 4 - Advarsler og usikkerhed, hvor de hører til (Priority: P2)

Kernens advarsler (fx mellemskat i bestemte år, skønnet ATP, jævn udbetaling forudsætter
senere udbetalinger) vises som korte kort ved den del af resultatet, de vedrører, ikke som
en lang liste.

**Why this priority**: Princip V og X. Det er vigtigt for tilliden, men det sekundære lag.

**Independent Test**: Hver advarselskode fra kernen har en dansk tekst, et ikon og en
placering. Profiler, der udløser hver kode, viser den det rigtige sted.

**Acceptance Scenarios**:

1. **Given** en profil med `ATP_SKOENNET`, **When** resultatet vises, **Then** står
   advarslen på ATP-kortet med ikon og tekst, ikke kun med farve.
2. **Given** en profil med `MELLEMSKAT_INTERVAL`, **When** grafen vises, **Then** er de
   berørte år markeret, og markeringen forklares.

---

### User Story 5 - Prøv andre antagelser (Priority: P2)

Borgeren ændrer afkast, inflation eller pensionsstart med skydeknapper ved resultatet og ser
hovedtallet og grafen opdatere sig med det samme.

**Why this priority**: Viser følsomheden uden en separat scenarie-tabel (legacy havde
4 scenarier i en tabel).

**Independent Test**: En ændring af afkastet giver en ny beregning i kernen og et opdateret
hovedtal inden for 1 sekund.

**Acceptance Scenarios**:

1. **Given** resultatsiden, **When** borgeren flytter afkast fra 4 % til 2 %, **Then**
   falder hovedtallet, og det vises kort, hvor meget det ændrede sig.
2. **Given** en ændret antagelse, **When** borgeren vælger "Nulstil", **Then** vender
   værdierne tilbage til forslaget.

---

### User Story 6 - Se hvordan vi har regnet (Priority: P3)

Bag "Se hvordan vi har regnet →" kan borgeren (eller en revisor) se år for år: brutto, skat og
netto pr. kilde, indtægtsgrundlag og tillægsprocent, samt de satser fra regelregistret, der
er brugt, med kilde og status.

**Why this priority**: Gennemsigtighed (Princip V). Det er et tredje lag, som de fleste
ikke åbner.

**Independent Test**: For et vilkårligt år svarer de viste tal til kernens `Aarsresultat`,
og hver nævnt sats har kilde og status fra registret.

**Acceptance Scenarios**:

1. **Given** sektionen "Sådan har vi regnet", **When** den åbnes, **Then** vises en tabel pr.
   år, som er lukket som standard.
2. **Given** en sats i listen, **When** den vises, **Then** står kilden og status-ikonet ved
   den (✓ verificeret / ≈ sekundær kilde).

### Edge Cases

- **Kun folkepension og ATP**: Ingen private ordninger. Hovedtallet og kortene fungerer
  stadig.
- **Allerede pensionist**: Grafen starter i år.
- **Ugyldig kombination**, fx start før lovlig udbetalingsalder: Kernens fejl vises ved
  feltet.
- **Langsom eller fejlende beregning**: Der vises en dansk fejlbesked med et næste skridt,
  aldrig en tom side.
- **Meget store tal**, fx 20 mio. kr.: Tusindtalsseparatorer og ingen ombrydning midt i et
  beløb.

## Requirements *(mandatory)*

### Functional Requirements

**Beregning og data**

- **FR-001**: Alle viste beløb, procenter og aldre MUST komme fra beregningskernen
  (`beregn`). Brugerfladen MUST NOT regne skat, ydelser eller fremskrivninger selv (Princip
  I). Den må kun formatere, summere kernens kilder til visning og dividere årsbeløb med 12.
- **FR-002**: Satser, der vises (fx i forklaringer), MUST læses fra regelregistret, ikke
  skrives i brugerfladen (Princip II).
- **FR-003**: Brugerens oplysninger MUST kun leve i den aktive session (browser/hukommelse).
  De må ikke gemmes på serveren eller i logs (Princip VII).

**Svaret først (US1)**

- **FR-010**: Resultatsiden MUST starte med et hovedtal: den jævne udbetaling i dagens
  kroner pr. måned, afrundet til nærmeste 100 kr. og med "ca.". Til hovedtallet hører en
  sætning med startalder og en henvisning til forbeholdet.
- **FR-011**: Hvis der ikke er nogen jævn udbetaling, MUST hovedtallet være nettoudbetalingen
  i det første fulde år med folkepension, med en tydelig tekst om det.

**Indhold og progressiv afsløring (US2, US6)**

- **FR-020**: En graf MUST vise netto pr. år, stablet pr. kildetype, med faste farver for
  hver kildetype i hele løsningen.
- **FR-021**: Der MUST være et kort pr. kilde med samlet netto pr. måned i første år,
  periode og "Se detaljer →".
- **FR-022**: Detaljer (år for år, skat, indtægtsgrundlag, tillægsprocent, sporing) MUST
  være skjult som standard og kunne foldes ud.
- **FR-023**: Grafen MUST have et tilgængeligt tabelalternativ.

**Guide (US3)**

- **FR-030**: Guiden MUST have tre trin (om dig, ordninger, forventninger) med en
  fremdriftsindikator og mulighed for at gå tilbage uden datatab.
- **FR-031**: Kommune MUST vælges fra registrets kommuneliste (søgbar).
- **FR-032**: Ordningsfelterne MUST afhænge af ordningstypen. Felter, der ikke er relevante,
  vises ikke.
- **FR-033**: Kernens valideringsfejl (`UgyldigtInput.felt`) MUST vises ved det felt, den
  vedrører, med kernens danske besked.
- **FR-034**: Antagelser MUST have forslag (kernens defaults) og forklaringen "dette er et
  gæt, ikke et løfte".

**Advarsler og antagelser (US4, US5)**

- **FR-040**: Hver advarselskode fra kernen MUST have en placering i resultatet (kort, graf
  eller sektion), et ikon og en dansk tekst. En ukendt kode vises i en generel sektion
  (fejlsikker).
- **FR-041**: Afkast, inflation og pensionsalder MUST kunne ændres på resultatsiden med
  genberegning på under 1 sekund og en "Nulstil".

**UX-krav (Princip X)**

- **FR-050**: Layoutet MUST følge docs/ux/designretning.md:
  - topbjælke
  - todelt resultat-hero
  - sektioner med luft
  - kort med "→"-links
  - ingen karruseller

  Det MUST NOT ligne Velliv i navn, logo, farver eller billeder.
- **FR-051**: WCAG 2.2 AA: kontrast, tastaturbetjening, synligt fokus, labels og
  skærmlæsertekst for grafen.
- **FR-052**: Ingen vandret scroll ved 360 px.
- **FR-053**: Alt indhold på dansk med dansk talformat (1.234.567 kr. og 4,5 %), klarsprog
  og du-form.
- **FR-054**: Før merge MUST der foreligge en heuristisk evaluering (Nielsens 10) i
  `specs/002-pensionsoverblik/ux-evaluering.md` eller en brugertest med mindst 3 personer.

### Key Entities

- **Guidedata**: Brugerens indtastning, som kan oversættes til kernens
  `Pensionsprofil` og `Antagelser`.
- **Visningsmodel**: Afledt af `Fremskrivning`. Indeholder hovedtal, kort pr. kilde,
  grafserier, placerede advarsler og sporingstabel. Den indeholder ingen beregnede satser,
  kun omformatering.
- **Advarselskatalog**: Kode → titel, tekst, ikon og placering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: I en test med mindst 3 personer fra målgruppen kan mindst 2 af 3 svare
  korrekt på "Hvad får du om måneden, og fra hvornår?" inden for 10 sekunder efter at have
  set resultatsiden.
- **SC-002**: En ny bruger gennemfører guiden med én ratepension på under 3 minutter.
- **SC-003**: 0 kritiske fejl i en automatisk tilgængelighedstest (axe eller tilsvarende)
  og 0 fund af alvorlighed 3–4 i den heuristiske evaluering.
- **SC-004**: Hvert tal på resultatsiden kan spores til et felt i kernens `Fremskrivning`.
  Det testes ved at sammenligne visningsmodellen med kernens output for mindst 5 profiler.
- **SC-005**: Genberegning ved ændret antagelse viser det nye hovedtal inden for 1 sekund.

## Assumptions

- Én bruger ad gangen. Der er ingen login, og intet gemmes (tilsvarende legacy uden
  PDF-cache).
- Gift/samlevende indtastes med partnerens fødselsdato og et samlet årligt beløb for
  partnerens øvrige indkomst. Den fulde husstandsmodel er en senere feature.
- Desktop og mobil i moderne browsere. Ingen app.
- Uden for scope:
  - PDF-import (003)
  - AI-forklaring og chat (004)
  - Optimering af udbetalingsrækkefølge
  - Forsikringsanalyse
  - Eksport og print
