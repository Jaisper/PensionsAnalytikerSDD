# Feature Specification: Indlæsning af PensionsInfo-rapport

**Feature Branch**: `003-pdf-import`

**Created**: 2026-10-24

**Status**: Draft

**Input**: "Indlæs PensionsInfo-PDF, så guiden udfyldes automatisk."

## Overblik

Borgeren kan uploade sin PDF-rapport fra pensionsinfo.dk. Løsningen aflæser fødselsdato,
ordninger (type, saldo, indbetaling, startalder og periode) og ATP og udfylder guiden fra
feature 002 med det. Borgeren tjekker og retter tallene, før der regnes. Aflæsningen
**udfylder kun formularen**. Alle tal i resultatet kommer stadig fra kernen (Princip I).

Legacy-erfaringer, der skal undgås:
- **PDF-cache:** Udtræk blev gemt permanent på disk (`.pdf_cache/`).
- **CPR-nummer:** Det blev sendt til AI-tjenesten.
- **Samtykke:** Oplysningen om AI-tjenesten stod kun i sidefoden.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload rapporten og få guiden udfyldt (Priority: P1)

Borgeren vælger sin PDF, giver samtykke til, at teksten sendes til en AI-tjeneste, og trykker
"Aflæs rapport". Guidens felter og ordninger bliver udfyldt.

**Independent Test**: Med en aflæsning, der giver kendte ordninger, bliver guidens felter og
ordningskort udfyldt med de samme værdier.

**Acceptance Scenarios**:

1. **Given** en tekstbaseret rapport og samtykke, **When** den aflæses, **Then** er
   fødselsdato og ordninger udfyldt, og der står "Aflæst fra rapporten – tjek tallene".
2. **Given** at samtykke ikke er givet, **When** borgeren trykker "Aflæs", **Then** sendes
   intet, og der vises en dansk besked ved samtykkefeltet.
3. **Given** en scannet PDF uden tekst, **When** den uploades, **Then** vises en dansk
   besked om at hente rapporten som PDF direkte fra pensionsinfo.dk.
4. **Given** en fil, der ikke er en PDF, eller som er over 25 MB, **When** den uploades,
   **Then** afvises den med en forståelig besked.
5. **Given** at AI-tjenesten ikke svarer, inden der er gået 90 sekunder, **When** borgeren
   venter, **Then** vises en dansk fejlbesked med henvisning til manuel indtastning.

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

1. **Given** en rapport med CPR-nummer, **When** teksten sendes til AI-tjenesten, **Then**
   er CPR-numre erstattet med "[CPR fjernet]". Fødselsdatoen udledes lokalt.
2. **Given** en aflæsning, **When** den er færdig eller fejler, **Then** findes hverken PDF
   eller tekst på serverens disk eller i logs.
3. **Given** at der ikke er adgang til AI-tjenesten, **When** guiden vises, **Then** vises
   upload-muligheden ikke. Manuel indtastning virker som før.

### Edge Cases

- **Folkepension og forsikringer i rapporten:** Ignoreres. Folkepensionen beregner kernen
  selv.
- **ATP:** Står som linje → udfylder feltet "ATP pr. år".
- **AI-tjenesten afviser** at aflæse (refusal): Der vises en dansk fejlbesked.

## Requirements *(mandatory)*

- **FR-001**: Tekst udtrækkes lokalt fra PDF'en. Kun teksten (ikke PDF-filen) sendes videre.
- **FR-002**: CPR-numre MUST fjernes lokalt, før teksten sendes. Fødselsdato MUST udledes
  lokalt af CPR-nummeret efter 7.-ciffer-reglen for århundrede.
- **FR-003**: Upload MUST kræve eksplicit samtykke. Samtykketeksten MUST nævne modtageren
  (Anthropic) og at intet gemmes.
- **FR-004**: AI-tjenesten MUST returnere data efter et fast skema (structured output). Svar,
  der ikke passer til skemaet, afvises.
- **FR-005**: Omsætningen fra aflæsning til guidedata MUST være deterministisk og testet. Den
  bruger kernens regelregister til folkepensionsalder (udledning af oprettelsesperiode).
- **FR-006**: Hver aflæst ordning MUST have en kildeangivelse (selskab og aftalenummer) og en
  liste over usikkerheder.
- **FR-007**: Filer > 25 MB eller uden PDF-signatur MUST afvises. Aflæsning MUST have
  timeout.
- **FR-008**: Ingen persistens. Hverken fil, tekst eller resultat må skrives til disk eller
  logs (Princip VII).
- **FR-009**: Funktionen MUST kunne slås fra. Uden adgang til AI-tjenesten skjules den.
- **FR-010**: UX følger Princip X:
  - samtykke ved selve handlingen
  - fremdrift under aflæsning
  - klar dansk besked ved fejl med et næste skridt
  - usikkerheder ved de felter, de gælder

## Success Criteria

- **SC-001**: For en rapport med 3 ordninger er guiden udfyldt på under 60 sekunder.
- **SC-002**: 0 CPR-numre i den tekst, der sendes (testet med syntetiske rapporter).
- **SC-003**: 0 filer skrevet under aflæsning (testet).
- **SC-004**: Omsætningen er dækket af tests for alle ordningskategorier og alle usikkerheder.

## Assumptions

- Der findes ingen rigtige PensionsInfo-rapporter i repoet. Feltvejledningen til AI-tjenesten
  bygger på legacy-prompten, som er udviklet mod rigtige rapporter.
- Model: Claude Opus 5.5 med structured outputs og refusal-fallback.
- Der laves ingen live-test mod AI-tjenesten i denne feature (ingen nøgle i miljøet). Den
  verificeres manuelt med en rigtig rapport, før funktionen tages i brug.
