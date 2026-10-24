# Feature Specification: PensionsAnalytikerSDD — Baseline (eksisterende funktionalitet)

**Feature Branch**: `speckit-setup`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "Lav en baseline-specifikation baseret på den eksisterende kode i
PensionsAnalytikerSDD, så fremtidige features kan specificeres op imod den."

> Dette er en **as-is**-specifikation (brownfield). Den beskriver den adfærd, løsningen har i dag,
> udledt af koden, testene og README.md — ikke ny funktionalitet. Kravene herunder er dermed
> allerede implementeret, medmindre andet er angivet.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload PensionsInfo-rapport og få overblik (Priority: P1)

En borger på vej mod pension henter sin rapport fra pensionsinfo.dk som PDF og uploader den.
Værktøjet udtrækker personoplysninger (alder/fødselsår), alle pensionsordninger (selskab,
produkttype, opsparing, skattetype, forventet udbetaling) og forsikringsdækninger, og viser en
oversigtstabel over ordningerne, så brugeren kan se, hvad værktøjet har forstået.

**Why this priority**: Uden en korrekt indlæst profil har ingen af de øvrige funktioner noget at
regne på. Det er indgangen til hele værktøjet.

**Independent Test**: Upload en kendt test-rapport og kontrollér, at oversigten viser de ordninger
og beløb, der står i PDF'en.

**Acceptance Scenarios**:

1. **Given** en ny session, **When** brugeren uploader en tekstbaseret PensionsInfo-PDF,
   **Then** vises en oversigt over alle ordninger med selskab, type og opsparing.
2. **Given** en scannet PDF uden tekstlag, **When** den uploades, **Then** får brugeren en dansk
   fejlbesked, der forklarer, at rapporten skal eksporteres direkte fra pensionsinfo.dk.
3. **Given** en PDF over 25 MB, **When** den uploades, **Then** afvises den med en forståelig besked.
4. **Given** at udtrækket tager for lang tid, **When** tidsgrænsen nås, **Then** får brugeren en
   dansk fejlbesked frem for en hængende side.

---

### User Story 2 - Besvar interview og se beregnet udbetalingsplan (Priority: P1)

Efter upload stiller værktøjet en række spørgsmål (bl.a. forventet pensionsalder, udbetalingsperiode,
afkast, inflation, kommune, civilstand, løbende indbetaling, fri formue og dens beskatning, og evt.
bruttoindtægt når topskat kan være relevant). Ud fra svarene beregner værktøjet en år-for-år-
fremskrivning efter dansk skatte- og pensionslovgivning og viser den som tabeller og et diagram:
fremtidsværdi og månedlig udbetaling pr. ordning, netto pr. måned/år med skattenoter, og
folkepension med pensionstillæg.

**Why this priority**: Det er værktøjets kerneværdi — et pålideligt, deterministisk beregnet svar
på "hvad får jeg udbetalt, efter skat, år for år?".

**Independent Test**: Brug en fast testprofil og faste parametre; kontrollér at tabeller og
diagram matcher regressionstestenes facit-tal.

**Acceptance Scenarios**:

1. **Given** en indlæst profil, **When** brugeren indsender interviewsvar, **Then** beregnes og vises
   Tabel 1 (pr. ordning) og Tabel 2 (år for år, inkl. noter om topskat) samt et udbetalingsdiagram.
2. **Given** en eksisterende beregning, **When** brugeren ændrer en parameter (f.eks. pensionsalder
   eller kommune) og vælger "Opdater analyse", **Then** genberegnes alle tal, og forældede tabeller
   markeres som sådan, indtil de er opdateret.
3. **Given** samme profil og parametre, **When** beregningen køres igen, **Then** er resultatet
   identisk (deterministisk).
4. **Given** en profil, hvor en opsparingssaldo ikke fremgår af rapporten, **When** beregningen
   køres, **Then** udledes saldoen konservativt fra det oplyste udbetalingsbeløb, og brugeren kan
   overskrive saldoen manuelt.

---

### User Story 3 - Få resultatet forklaret af en AI-assistent (Priority: P2)

Brugeren vælger et forklaringsniveau (1: ny i pension, 2: kender det grundlæggende, 3: godt
kendskab) og kan i en chat få resultatet præsenteret og stille opfølgende spørgsmål. Assistenten
gengiver og forklarer kun de beregnede tal og henviser til en certificeret pensionsrådgiver ved
konkrete anbefalinger.

**Why this priority**: Gør tallene forståelige for brugere uden pensionsfaglig viden, men værdien
afhænger af User Story 1 og 2.

**Independent Test**: Med en beregnet profil, stil et spørgsmål om netto-udbetalingen i et givent
år og kontrollér, at svaret bruger præcis det tal, beregningen viser.

**Acceptance Scenarios**:

1. **Given** en beregnet plan, **When** brugeren stiller et spørgsmål, **Then** streames svaret løbende,
   og alle tal i svaret stammer fra beregningen.
2. **Given** forklaringsniveau 1, **When** assistenten forklarer, **Then** undgås fagord eller de
   forklares med det samme; på niveau 3 springes grundforklaringer over.
3. **Given** en konkret anbefaling i svaret, **When** den vises, **Then** indeholder den et forbehold
   om, at det ikke er reguleret rådgivning.
4. **Given** en afbrudt eller hængende stream, **When** den fejler, **Then** låses knapper og chat
   ikke permanent.
5. **Given** en lang samtale, **When** historikken bliver stor, **Then** beskæres den, så kun de
   seneste beskeder (højst 40) sendes med.

---

### User Story 4 - Optimer udbetalingsrækkefølgen (Priority: P2)

Brugeren kan bede værktøjet finde den rækkefølge af udbetalinger — start-alder pr. ordning,
ratepensioners udbetalingsperiode, engangsbeløbs udbetalingsår og evt. udskudt folkepension — der
giver det højeste faste, inflationskorrigerede månedsbeløb gennem hele perioden, uden at skabe et
dybere indkomsthul end brugerens nuværende plan. Brugeren kan angive en hård bundgrænse pr. måned.

**Why this priority**: Den største konkrete værdi ud over selve fremskrivningen — men en avanceret
funktion, der bygger på User Story 2.

**Independent Test**: Kør optimering på en fast testprofil og kontrollér, at den foreslåede plan
mindst er lige så god som udgangsplanen og overholder lovlige grænser.

**Acceptance Scenarios**:

1. **Given** en beregnet plan, **When** brugeren kører optimering, **Then** vises den bedste plan,
   en top-liste af alternativer og hvor følsomt resultatet er for de enkelte valg.
2. **Given** at søgerummet er større end antallet af evaluerede kombinationer, **When** resultatet
   vises, **Then** oplyses brugeren om, at søgningen ikke var udtømmende.
3. **Given** en plan med udskudt folkepension uden for den kildehenviste tabel, **When** den vises,
   **Then** markeres ventetillægget som usikkert.
4. **Given** en hård bundgrænse, der ikke kan overholdes, **When** optimeringen kører, **Then**
   oplyses det, at ingen gennemførlig plan findes.

---

### User Story 5 - Planlæg som par (Priority: P3)

En gift/samlevende bruger kan angive partnerens alder og indkomst eller uploade partnerens egen
PensionsInfo-rapport. Værktøjet kobler de to beregninger, så pensionstillæg og tillægsprocent
bygger på husstandens fælles indtægtsgrundlag, og viser partnerens egen analyse side om side.

**Why this priority**: Vigtig for korrekte offentlige ydelser for par, men kun relevant for en
del af brugerne.

**Independent Test**: Brug to faste testprofiler og kontrollér, at pensionstillægget ændres i
forhold til enlig-beregningen som forventet.

**Acceptance Scenarios**:

1. **Given** civilstand "gift/samlevende" og et overslag over partnerens indkomst, **When**
   beregningen køres, **Then** indgår partnerens indkomst i pensionstillæg og tillægsprocent.
2. **Given** en uploadet partnerrapport, **When** brugeren beregner partnerens analyse, **Then**
   vises partnerens egen plan med partnerens egne antagelser.
3. **Given** en partnerplan, **When** optimeringen køres for partneren, **Then** optimeres
   partnerens ordninger, mens brugerens indkomst bidrager til husstandskoblingen.

---

### User Story 6 - Supplerende analyser og eksport (Priority: P3)

Brugeren kan se følsomhedsscenarier (afkast ±1 og ±2 procentpoint fra egen antagelse), en analyse
af fri formue med kapitalbeskatning, en vurdering af forsikringsdækninger mod
brancheanbefalinger, og gemme hele analysen som en tekstfil.

**Why this priority**: Nyttige tilføjelser, men ikke nødvendige for kernebeslutningen.

**Independent Test**: Med en beregnet plan, åbn scenarietabellen og kontrollér, at den har fire
scenarier omkring brugerens afkast; gem analysen og kontrollér, at filen indeholder assistentens svar.

**Acceptance Scenarios**:

1. **Given** en beregnet plan, **When** scenarier vises, **Then** er der fire scenarier med
   uændret inflation.
2. **Given** en fri formue over 0, **When** brugeren har valgt beskatningsform, **Then** vises en
   separat fri formue-tabel.
3. **Given** forsikringsdækninger under anbefalingerne, **When** analysen vises, **Then** fremgår
   en advarsel.
4. **Given** en samtale med svar, **When** brugeren vælger "Gem analyse", **Then** downloades en
   tekstfil med alle assistentens svar.

### Edge Cases

- PDF med ukendt layout (ingen forventede overskrifter): hele dokumentet bruges i stedet for
  udvalgte sider.
- Profil uden ordninger, eller kun med folkepension: beregningen skal stadig give et resultat.
- Fødselsår udledes under antagelse af 1900-tallet (alle reelle brugere er 55-85 år).
- Kommunenavne med varierende stavemåde normaliseres til en af de 98 kommuner.
- Engangsbeløb, som brugeren har fravalgt fra bufferen, flyttes ikke af optimeringen.
- Mange forespørgsler fra samme IP: over 40 pr. minut til upload/chat/parametre afvises med 429.
- Session-id, der ikke findes: endpoints svarer 404 med dansk besked.

## Requirements *(mandatory)*

### Functional Requirements

**Indlæsning**
- **FR-001**: Systemet SKAL kunne indlæse en PensionsInfo-rapport som PDF (højst 25 MB) og udtrække
  person, ordninger og forsikringer til en struktureret profil.
- **FR-002**: Systemet SKAL afvise PDF'er uden tekstlag med en forklarende dansk fejlbesked.
- **FR-003**: Systemet SKAL afbryde indlæsningen efter en fast tidsgrænse og give en dansk fejlbesked.
- **FR-004**: Brugeren SKAL kunne overskrive udtrukne saldi manuelt.

**Beregning**
- **FR-005**: Systemet SKAL beregne en år-for-år-fremskrivning af udbetalinger efter skat ud fra
  profil og brugerens parametre, deterministisk og uden brug af AI.
- **FR-006**: Beregningen SKAL omfatte progressiv skat (bundskat, mellemskat, topskat, top-topskat,
  AM-bidrag), personfradrag, kommune- og kirkeskat, folkepension med pensionstillæg og
  tillægsprocent, ældrecheck og de produkttyper rapporten kan indeholde (bl.a. ratepension,
  livsvarig pension, aldersopsparing, kapitalpension, ATP).
- **FR-007**: Fremtidige års skattegrænser SKAL satsreguleres i stedet for at bruge faste 2026-tal.
- **FR-008**: Brugeren SKAL kunne vælge start-alder pr. ordning, udbetalingsperiode, folkepensions-
  opsættelse, og om engangsbeløb skal indgå i en buffer, der udjævnes over perioden.
- **FR-009**: Systemet SKAL vise et fast, inflationskorrigeret månedsbeløb, brugeren kan leve af
  gennem hele perioden.
- **FR-010**: Alle satser SKAL komme fra ét kildested med kildehenvisning, og uverificerede satser
  SKAL markeres over for brugeren.

**Optimering**
- **FR-011**: Systemet SKAL kunne søge efter den udbetalingsrækkefølge, der maksimerer det faste
  realmånedsbeløb, uden at skabe et dybere eller længere indkomsthul end brugerens nuværende plan.
- **FR-012**: Optimeringen SKAL overholde lovlige grænser (bl.a. mindst 10 års udbetalingsperiode
  for ratepension) og en evt. brugerdefineret bundgrænse.
- **FR-013**: Optimeringsresultatet SKAL oplyse antal evaluerede vs. mulige kombinationer og
  markere, når ventetillægget for folkepension er usikkert.

**Husstand**
- **FR-014**: Systemet SKAL kunne koble beregningen for to personer i samme husstand, så
  pensionstillæg og tillægsprocent bygger på fælles indtægtsgrundlag.
- **FR-015**: Brugeren SKAL kunne uploade partnerens rapport og angive partnerens egne antagelser.

**AI-assistent**
- **FR-016**: Systemet SKAL tilbyde en chat, hvor svar streames, og hvor assistenten kun gengiver
  og forklarer beregnede tal.
- **FR-017**: Brugeren SKAL kunne vælge forklaringsniveau 1-3, som styrer formuleringen, men ikke
  beregningen.
- **FR-018**: Assistenten SKAL tage forbehold om, at værktøjet ikke er reguleret rådgivning, ved
  konkrete anbefalinger.
- **FR-019**: Brugeren SKAL kunne rydde samtalen.

**Supplerende**
- **FR-020**: Systemet SKAL vise fire afkastscenarier (±1 og ±2 procentpoint).
- **FR-021**: Systemet SKAL analysere fri formue med valgt kapitalbeskatning.
- **FR-022**: Systemet SKAL vurdere forsikringsdækninger og advare ved mangler.
- **FR-023**: Brugeren SKAL kunne gemme analysen som en tekstfil.

**Drift, sikkerhed og privatliv**
- **FR-024**: Sessioner SKAL ligge i hukommelsen; uploadede PDF'er SKAL slettes efter parsing.
- **FR-025**: Systemet SKAL begrænse antal forespørgsler pr. IP på upload, chat og parametre.
- **FR-026**: Brugeren SKAL oplyses om, at data sendes til Anthropic, og at værktøjet ikke er
  reguleret rådgivning.
- **FR-027**: Al brugervendt tekst SKAL være på dansk med dansk talformatering.

### Key Entities

- **Session**: én brugers arbejdsforløb — samtale, profil(er), parametre og seneste beregning.
  Lever kun i hukommelsen.
- **Profil**: udtræk fra en PensionsInfo-rapport — person, liste af pensionsordninger, forsikringer.
- **Pensionsordning**: selskab, produkttype, opsparing, skattetype, start-alder og udbetalingsperiode.
- **Beregningsparametre**: brugerens antagelser (pensionsalder, afkast, inflation, kommune,
  civilstand, fri formue m.fl.), evt. med en tilsvarende sæt for partneren.
- **Sats**: en lovbestemt sats eller grænse med værdi, kilde og verifikationsstatus.
- **Udbetalingstabel**: resultatet af en beregning — pr. ordning og pr. år, brutto, skat og netto.
- **Optimeringsresultat**: bedste plan, top-alternativer, følsomhed, antal evaluerede kombinationer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % af tallene i assistentens svar kan spores direkte til beregningens output.
- **SC-002**: Alle regressionstests (ca. 190) består, og facit-tallene for golden cases er uændrede.
- **SC-003**: En tekstbaseret PensionsInfo-rapport indlæses og vises som oversigt på under 100 sekunder.
- **SC-004**: Samme profil og parametre giver identiske tal ved gentagen beregning.
- **SC-005**: Ingen sats findes som litteral værdi uden for kildestedet (kontrollerbart ved søgning).
- **SC-006**: Den optimerede plan giver et fast realmånedsbeløb, der er mindst lige så højt som
  brugerens udgangsplan.

## Assumptions

- Brugerne er danske borgere ca. 55-85 år, der kan hente deres egen rapport fra pensionsinfo.dk.
- Satserne gælder for 2026; den årlige opdatering følger README.md's tjekliste.
- Løsningen kører som én proces (lokalt via `start.bat` eller på én server); sessioner tabes ved
  genstart.
- Kendte forenklinger, som denne baseline accepterer (se README.md): flad tilnærmelse af
  ventetillæg uden for tabellen, forenklet husstandskobling, fast 4 % / 25 år ved udledning af
  manglende saldi, aldersopsparingens strafafgifter modelleres ikke, og optimeringen er ikke
  udtømmende.
- Kendte afvigelser fra forfatningen (Princip VI), som skal løses i separate features:
  `.pdf_cache/` gemmer udtrukne profiler permanent, og debug-endpoints (`/raw`, `/text`, `/inject`)
  er ikke beskyttet.
