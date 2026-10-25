# Feature Specification: Indlæsning af PensionsInfo-rapport

**Feature Branch**: `003-pdf-import`

**Created**: 2026-10-24

**Status**: Revideret 2026-10-25 efter NFR "ingen persondata til AI/LLM" (forfatningens Princip XI).
AI-aflæsningen er fjernet. Infrastrukturen (upload, lokalt tekstudtræk, omsætning, brugerflade) er
bevaret. **Den lokale parser er bygget 2026-10-25** og funktionen er slået til.

**Input**: "Indlæs PensionsInfo-PDF, så guiden udfyldes automatisk."

## Overblik

Borgeren kan uploade sin PDF-rapport fra pensionsinfo.dk. Løsningen aflæser **lokalt på
serveren** fødselsdato,
ordninger (type, saldo, indbetaling, startalder og periode) og ATP og udfylder guiden fra
feature 002 med det. Borgeren tjekker og retter tallene, før der regnes. Aflæsningen
**udfylder kun formularen**. Alle tal i resultatet kommer stadig fra kernen (Princip I).

Legacy-erfaringer, der skal undgås:
- **PDF-cache:** Udtræk blev gemt permanent på disk (`.pdf_cache/`).
- **CPR-nummer:** Det blev sendt til AI-tjenesten.
- **Samtykke:** Oplysningen om AI-tjenesten stod kun i sidefoden.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload rapporten og få guiden udfyldt (Priority: P1)

Borgeren vælger sin PDF og trykker "Aflæs rapport". Rapporten læses lokalt og slettes med det
samme. Guidens felter og ordninger bliver udfyldt.

**Independent Test**: Med en aflæsning, der giver kendte ordninger, bliver guidens felter og
ordningskort udfyldt med de samme værdier.

**Acceptance Scenarios**:

1. **Given** en tekstbaseret rapport, **When** den aflæses, **Then** er
   fødselsdato og ordninger udfyldt, og der står "Aflæst fra rapporten – tjek tallene".
2. **Given** en aflæsning, **When** den foregår, **Then** sendes intet fra rapporten til en
   AI/LLM-tjeneste (Princip XI).
3. **Given** en scannet PDF uden tekst, **When** den uploades, **Then** vises en dansk
   besked om at hente rapporten som PDF direkte fra pensionsinfo.dk.
4. **Given** en fil, der ikke er en PDF, eller som er over 25 MB, **When** den uploades,
   **Then** afvises den med en forståelig besked.
5. **Given** at parseren ikke kan genkende rapporten, **When** den aflæses, **Then** vises en
   dansk fejlbesked med henvisning til manuel indtastning.

### User Story 2 - Usikre værdier er markeret (Priority: P1)

Hvor aflæsningen er usikker eller ufuldstændig, ser borgeren det ved den pågældende ordning
og kan rette det. Det gælder fx manglende saldo, ukendt type, startalder, der ikke er
fundet, eller en udledt oprettelsesperiode.

**Acceptance Scenarios**:

1. **Given** en ordning uden aflæst saldo, **When** guiden vises, **Then** er saldoen tom,
   og der står "Saldo blev ikke fundet i rapporten".
2. **Given** en tidligste udbetalingsalder 5 år før folkepensionsalderen, **When** ordningen
   udfyldes, **Then** er oprettelsesperioden "Maj 2007 – 2017", og der står, at den er udledt.
3. **Given** en kapitalpension med betalt afgift, **When** den udfyldes, **Then** regnes
   den som skattefri, og det står ved ordningen.

### User Story 3 - Privatliv (Priority: P1)

**Acceptance Scenarios**:

1. **Given** en rapport med CPR-nummer, **When** den aflæses, **Then** udledes fødselsdatoen
   lokalt, og parseren får teksten uden CPR-numre (dataminimering).
2. **Given** en aflæsning, **When** den er færdig eller fejler, **Then** findes hverken PDF
   eller tekst på serverens disk eller i logs.
3. **Given** at der ikke er en lokal parser, **When** guiden vises, **Then** vises
   upload-muligheden ikke. Manuel indtastning virker som før.
4. **Given** kodebasen, **When** testsuiten kører, **Then** fejler den, hvis kode i `src/`
   importerer en AI/LLM-klient, har en AI-afhængighed eller indeholder et AI-endpoint.

### Edge Cases

- **Folkepension og forsikringer i rapporten:** Ignoreres. Folkepensionen beregner kernen
  selv.
- **ATP:** Står som linje → udfylder feltet "ATP pr. år".
- **Ukendt rapportformat**: Der vises en dansk fejlbesked, og brugeren indtaster selv.

## Requirements *(mandatory)*

- **FR-001**: Tekst udtrækkes og aflæses lokalt. Intet fra rapporten forlader serveren (Princip XI).
- **FR-002**: Fødselsdato MUST udledes lokalt af CPR-nummeret efter 7.-ciffer-reglen for
  århundrede. CPR-numre fjernes, før parseren får teksten (dataminimering).
- **FR-003**: Brugeren MUST ved upload få at vide, at rapporten læses på serveren, slettes
  med det samme, og at intet sendes til AI.
- **FR-004**: Den lokale parser MUST levere data i den faste struktur `Aflaesning`
  (pdfimport/aflaeser.py) og være deterministisk.
- **FR-005**: Omsætningen fra aflæsning til guidedata MUST være deterministisk og testet. Den
  bruger kernens regelregister til folkepensionsalder (udledning af oprettelsesperiode).
- **FR-006**: Hver aflæst ordning MUST have en kildeangivelse (selskab og aftalenummer) og en
  liste over usikkerheder.
- **FR-007**: Filer > 25 MB eller uden PDF-signatur MUST afvises. Aflæsning MUST have
  timeout.
- **FR-008**: Ingen persistens. Hverken fil, tekst eller resultat må skrives til disk eller
  logs (Princip VII).
- **FR-009**: Funktionen er slået fra, så længe der ikke er en lokal parser. Upload-kortet
  skjules da.
- **FR-011**: Ingen kode i `src/` må importere AI/LLM-klienter, have AI-afhængigheder eller
  indeholde AI-endpoints. Det håndhæves af `tests/kontrakt/test_ingen_ai.py` (Princip XI).
- **FR-010**: UX følger Princip X:
  - privatlivsinformation ved selve handlingen
  - fremdrift under aflæsning
  - klar dansk besked ved fejl med et næste skridt
  - usikkerheder ved de felter, de gælder

## Success Criteria

- **SC-001**: For en rapport med 3 ordninger er guiden udfyldt på under 5 sekunder.
- **SC-002**: 0 AI/LLM-kald og 0 AI-afhængigheder (testet). 0 CPR-numre i parserens input
  (testet).
- **SC-003**: 0 filer skrevet under aflæsning (testet).
- **SC-004**: Omsætningen er dækket af tests for alle ordningskategorier og alle usikkerheder.

## Assumptions

- Der findes ingen rigtige PensionsInfo-rapporter i repoet.

## Lokal parser (gennemført 2026-10-25 — se tasks.md R005–R008). Oprindelig plan:

1. Skaf mindst én rigtig PensionsInfo-rapport, gerne flere med forskellige selskaber og
   produkter. Anonymisér den, før den lægges i `tests/` (navn, CPR, adresse, aftalenumre).
2. Byg `LokalAflaeser` (regex og layout på pdfplumber-tekst/tabeller) ud fra rapportens
   sektioner: "Nuværende pensionsopsparinger", "Dine aftaler", "Pension – flere oplysninger"
   og udbetalingsscenarier ("Hvis du går på pension som X-årig"). Legacy-promptens
   feltvejledning (`legacy/prompts.py` → `EXTRACTION_PROMPT`) beskriver, hvor felterne står.
3. Golden tests pr. rapport. Slå funktionen til i `vaelg_aflaeser()`.
