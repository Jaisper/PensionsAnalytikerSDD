# Feature Specification: Kør i browseren

**Feature Branch**: `005-browser`

**Created**: 2026-10-25

**Status**: Draft

**Input**: "Kan den køre på GitHub Pages?" Afprøvningen viste, at kernen og PDF-parseren kører
uændret i browseren (Pyodide).

**Grundlag**:
- Afprøvningen 2026-10-25 (se [research.md](research.md)): PDF-aflæsningen gav samme resultat
  som CPython. Beregningerne afveg højst med en relativ afvigelse på 4·10⁻¹⁶.
- Princip I, VII, IX og XI
- Feature 002–004

## Clarifications

### Session 2026-10-25

- Q: Hvor udgives siden? → A: GitHub Pages. Repoet gøres offentligt efter en scanning af
  historikken.
- Q: Hvor hentes Pyodide fra? → A: Det lægges i den byggede side. Intet CDN ved første besøg.
- Q: Hvad sker der med FastAPI-serveren? → A: Den fjernes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hele beregningen sker på borgerens egen computer (Priority: P1)

Borgeren åbner siden og indlæser sin PensionsInfo-rapport eller udfylder guiden. Aflæsning og
beregning sker i browseren. Rapporten, CPR-nummeret og tallene sendes ikke til nogen server.

**Why this priority**: Det er grunden til featuren. Der er ingen server at drive, sikre eller
stole på, og persondata forlader aldrig borgerens computer (Princip VII).

**Independent Test**: Kør hele forløbet (upload, guide, resultat, skydere) med netværksloggen
åben. Efter den første indlæsning sendes der ingen request, og ingen request indeholder
rapportens eller formularens data.

**Acceptance Scenarios**:

1. **Given** siden er indlæst, **When** borgeren indlæser en rapport og regner, **Then** sendes
   der ingen netværksrequest med PDF-indhold eller guidedata.
2. **Given** samme rapport og guidedata, **When** der regnes i browseren og i CPython, **Then**
   er aflæsning, hovedtal, grænser og advarsler identiske, og alle øvrige tal afviger højst
   10⁻⁹ relativt.
3. **Given** en PDF, som ikke er fra PensionsInfo, **When** den indlæses, **Then** vises samme
   danske fejlbesked som i dag.
4. **Given** et input, som kernen afviser, **When** der regnes, **Then** vises kernens danske
   feltbesked ved feltet som i dag.

---

### User Story 2 - Siden udgives som statiske filer (Priority: P1)

Siden kan lægges på en statisk host uden server. Ved hver ændring på `main` bygges og udgives
den automatisk.

**Why this priority**: Det er det, der gør det muligt at bruge GitHub Pages, og det fjerner
drift.

**Independent Test**: Byg siden til en mappe, server mappen med en almindelig statisk
filserver, og kør hele forløbet i headless Chrome.

**Acceptance Scenarios**:

1. **Given** et push til `main` med grønne tests, **When** udgivelsen kører, **Then** ligger
   den nye version på den statiske host.
2. **Given** den byggede mappe, **When** den serveres statisk, **Then** virker upload, guide,
   resultat, datapanel og tidslinje som i feature 004.

---

### User Story 3 - Klar besked mens programmet indlæses (Priority: P2)

Første besøg tager nogle sekunder, fordi beregningsprogrammet skal hentes. Borgeren ser,
hvad der sker, og kan begynde at udfylde guiden imens.

**Why this priority**: Uden besked ligner ventetiden en fejl (Princip X: synlighed).

**Acceptance Scenarios**:

1. **Given** første besøg, **When** programmet indlæses, **Then** står der "Gør
   beregningen klar …" med en statuslinje, og guidens første trin kan udfyldes.
2. **Given** borgeren trykker "Beregn", før programmet er klar, **When** det bliver klar,
   **Then** regnes der automatisk, uden at borgeren skal trykke igen.
3. **Given** programmet ikke kan hentes (fx offline ved første besøg), **When** det fejler,
   **Then** vises en dansk besked med en knap til at prøve igen.
4. **Given** skyderne flyttes, **When** der regnes, **Then** fryser siden ikke, fordi
   beregningen kører uden for sidens hovedtråd.

### Edge Cases

- Gamle browsere uden WebAssembly får en dansk besked om at bruge en nyere browser.
- Meget store PDF'er: samme grænse på 25 MB som i dag, tjekket før aflæsningen.
- To hurtige skyderændringer: kun den nyeste beregning vises (som i dag).
- Rigtige rapporter må stadig aldrig ligge i repoet eller i den byggede side.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Beregning, oversættelse, visning, grænser, kommuneliste og PDF-aflæsning MUST
  køre i browseren med samme Python-kode som i dag (Princip I: én implementering af reglerne).
  Ingen regel eller sats må genimplementeres i JavaScript.
- **FR-002**: Der MUST være ét Python-indgangspunkt (fx `pensionsoverblik.app`) med de samme
  operationer og fejlformater som de nuværende endpoints (`kommuner`, `beregn`, `pdf`).
  Brugerfladen kalder kun dette.
- **FR-003**: Persondata MUST NOT forlade browseren. Siden må kun hente sine egne
  programfiler (Princip VII og XI). `tests/kontrakt/test_ingen_ai.py` gælder fortsat.
- **FR-004**: Alle filer, siden kører, MUST være låst til præcise versioner. Python-pakker
  (fx pdfminer.six og pdfplumber) MUST ligge i den byggede side og ikke hentes fra PyPI, når
  siden kører. Det samme gælder Pyodide selv: kun de nødvendige filer lægges i den byggede
  side. Der må ikke være noget CDN ved første besøg, bortset fra Chart.js, som allerede bruges.
- **FR-005**: Beregningen MUST køre i en Web Worker, så brugerfladen ikke fryser.
- **FR-006**: Indlæsningen MUST vises som i US3, og en fejl MUST give en dansk besked med
  "Prøv igen".
- **FR-007**: Testsuiten MUST køre kernen i Pyodide og sammenligne med CPython (aflæsning,
  hovedtal, grænser og advarsler identiske, øvrige tal højst 10⁻⁹ relativt). Testen skal
  køre på mindst en golden case, guide-eksemplet og den syntetiske rapport.
- **FR-008**: En GitHub Action MUST køre testsuiten, bygge siden og udgive den på GitHub Pages
  ved push til `main`. Repoet gøres offentligt. Først skal hele git-historikken scannes for
  persondata og hemmeligheder (CPR, navne, aftale- og depotnumre fra rigtige rapporter, nøgler),
  og fund skal fjernes.
- **FR-009**: FastAPI-serveren MUST fjernes (Princip IX: én måde at køre på). Lokal udvikling
  bruger en statisk filserver på den byggede mappe. API-testene flyttes til at teste
  indgangspunktet direkte, og privatlivstestene (ingen cookies, ingen logs) erstattes af FR-003.
- **FR-010**: Princip X gælder fortsat: ingen vandret scroll ved 360 px og axe uden fejl, også
  for indlæsningsbeskeden.

### Key Entities

- **Indgangspunkt**: Python-funktioner, som tager guidedata eller PDF-bytes og returnerer det
  samme JSON som de nuværende endpoints, inklusive fejl (`felt`, `besked`, `kode`).
- **Bygget side**: statiske filer, som består af HTML/CSS/JS, en worker, projektets wheel,
  låste afhængigheder og eventuelt Pyodide.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Efter den første indlæsning sender et helt forløb 0 requests med persondata.
- **SC-002**: Første besøg er klar til at regne på under 8 sekunder (afprøvning: cirka 5 s).
  Senere besøg er klar på under 3 sekunder.
- **SC-003**: En skyderændring viser et nyt hovedtal på under 1 sekund (som i 004).
- **SC-004**: Sammenligningen med CPython består for alle testcases.
- **SC-005**: axe-core: 0 overtrædelser. Ingen vandret scroll ved 360 px.

## Assumptions

- Brugerne har en moderne browser med WebAssembly (Chrome, Edge, Firefox, Safari fra 2022).
- Der skal ikke være offline-tilstand ud over browserens almindelige cache.
- Python-versionen i Pyodide (3.12 eller nyere) er kompatibel med kernen, som kræver 3.11 eller
  nyere.
- De ubetydelige afvigelser i sidste decimal skyldes platformens matematikbibliotek. De ville
  også opstå på en Linux-server og er ikke en regelafvigelse.
