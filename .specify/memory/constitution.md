<!--
Sync Impact Report
Version change: [TEMPLATE/UNRATIFIED] → 1.0.0
Rationale: Første ratificering. Forfatningen er udledt af den eksisterende kodebase
(brownfield) og README.md — den kodificerer principper projektet allerede følger,
frem for at indføre nye.

Added principles:
  - I. Deterministisk Beregning — AI'en Beregner Aldrig (NON-NEGOTIABLE)
  - II. Ét Kildested for Satser med Kildehenvisning
  - III. Regressionstest for Alle Beregninger
  - IV. Gennemsigtighed og Forbehold
  - V. Klar Ansvarsfordeling mellem Moduler
  - VI. Persondata og Privatliv (GDPR)
  - VII. Dansk Brugerflade
  - VIII. Simpelhed og Minimale Afhængigheder

Added sections:
  - Teknologibegrænsninger
  - Kvalitetsgates
  - Governance

Removed sections: none

Observerede afvigelser i den eksisterende kode (skal håndteres som features, ikke
rettet af denne kommando):
  - Princip VI: pdf_parser.py gemmer udtrukne profiler (inkl. persondata) permanent
    i .pdf_cache/ på disk, nøglet på PDF'ens SHA-256 — uden udløb eller sletning.
    Det modsiger sidefodens løfte "Ingen data gemmes permanent".
  - Princip VI: debug-endpoints GET /api/session/{id}/raw, GET /api/session/{id}/text
    og POST /api/session/{id}/inject er eksponeret uden adgangsbegrænsning ud over
    kendskab til session-id'et.
  - Princip VI: Oplysningen om, at data sendes til Anthropic, står kun i sidefoden —
    ikke i forbindelse med selve upload-handlingen.
  - Princip III: tests er print-baserede scripts; test_api/test_deploy/test_final
    kræver en kørende server og kører derfor ikke i én samlet kommando.

Deferred / TODO items: none

Templates requiring follow-up review (not modified by this command):
  - .claude/skills/speckit-plan — Constitution Check bør eksplicit tjekke
    Princip I (ingen tal fra LLM) og Princip II (ingen litterale satser uden for
    satser_2026.py).
-->

# PensionsAnalytikerSDD Constitution

## Core Principles

### I. Deterministisk Beregning — AI'en Beregner Aldrig (NON-NEGOTIABLE)
Alle tal, brugeren får præsenteret (skat, udbetalinger, fremskrivninger, scenarier,
optimeringsresultater), SKAL være beregnet af den deterministiske beregningskerne
(`engine.py` og moduler der kalder den). Beregningen SKAL være kørt færdig, før
AI-modellen genererer et svar, og AI'en SKAL instrueres i kun at gengive og
forklare engine-tal. Nye undtagelser fra denne regel SKAL være snævert afgrænsede,
bruge en fast, dokumenteret formel og være beskrevet eksplicit i `prompts.py`.
Beregningsfunktioner SKAL være rene funktioner uden delt tilstand.

Rationale: Værktøjets troværdighed hviler på, at tallene kan verificeres ved at
læse og teste koden — ikke ved at stole på en sprogmodels regnefærdigheder.

### II. Ét Kildested for Satser med Kildehenvisning
Alle satser og beløbsgrænser fra lovgivningen SKAL ligge i `satser_2026.py` (eller
efterfølgende års-modul) som `Sats`-objekter med `kilde` og `verificeret`-flag.
Ingen anden fil — Python, prompt-tekst eller frontend — må indeholde en litteral
kopi af en sats; de SKAL læses fra kildestedet (frontend via API). En sats SKAL
markeres `verificeret=False`, indtil den er bekræftet mod en primær, officiel kilde
(skat.dk, Skatteministeriet, borger.dk, ATP.dk o.l.) — sekundære opsummeringer
tæller ikke. Kommuneskat er den ene dokumenterede undtagelse fra `Sats`-formatet,
men SKAL stadig kun findes ét sted.

Rationale: Dublerede satser har tidligere ført til indbyrdes modstridende og
forældede tal i det brugeren så. Ét kildested gør den årlige opdatering og en
revisionsgennemgang mulig.

### III. Regressionstest for Alle Beregninger
Enhver ændring af beregningslogik, satser eller optimering SKAL ledsages af
regressionstests i `tests/`, og hele suiten SKAL bestå før merge. Nye funktioner
SKAL have deres egen testfil eller tilføjelser til en eksisterende. Ændrede satser
SKAL give nye, eksplicit forventede tal i de tests, der bruger dem — "stadig grønt"
er ikke nok. Håndverificerede facit-tal (golden cases) SKAL bevares og må kun
ændres med en begrundelse. For fejlrettelser SKAL der skrives en test, der fejler
før rettelsen.

Rationale: Testene er det offentlige bevis for beregningernes korrekthed og
erstatter manuel QA i et enmandsprojekt.

### IV. Gennemsigtighed og Forbehold
Værktøjet er information, ikke reguleret rådgivning, og det SKAL fremgå for
brugeren ved enhver konkret anbefaling, med henvisning til en certificeret
pensionsrådgiver. Når en beregning bygger på en uverificeret sats, en forenklet
tilnærmelse eller en ikke-udtømmende søgning, SKAL det rapporteres eksplicit i
resultatet (som f.eks. `usikker_venteprocent` og antal evaluerede vs. mulige
kombinationer). Kendte forenklinger SKAL dokumenteres i README.md.

Rationale: Brugeren træffer beslutninger med store økonomiske konsekvenser og
skal kunne se, hvor sikre tallene er.

### V. Klar Ansvarsfordeling mellem Moduler
Hvert modul har ét ansvar og SKAL holde sig til det:
- `engine.py` — al beregning; ingen AI, ingen I/O.
- `satser_2026.py` — alle satser.
- `prompts.py` — al tekst AI'en ser eller siger; ingen litterale satser.
- `app.py` — routing, sessioner, streaming, caching; ingen beregning, ingen prompt-tekst.
- `pdf_parser.py` — udtræk fra PensionsInfo-PDF til engine-format.
- `sekventering.py` / `husstand.py` — orkestrering af engine-kørsler.
Ny funktionalitet SKAL placeres i det modul, der ejer ansvaret, eller i et nyt
modul med ét tydeligt ansvar.

Rationale: En revisor skal kunne verificere tal ved at læse `engine.py` og
`satser_2026.py` alene, og AI-adfærd ved at læse `prompts.py` alene.

### VI. Persondata og Privatliv (GDPR)
PensionsInfo-rapporter indeholder følsomme personoplysninger (CPR-afledte data,
opsparing, forsikringer). Derfor:
- Dataminimering: der SKAL kun gemmes det, der er nødvendigt for den aktive session.
- Uploadede PDF'er SKAL slettes fra disk, så snart de er parset.
- Persondata MÅ IKKE gemmes permanent på disk eller i logs uden et dokumenteret
  formål og en sletteregel.
- Brugeren SKAL oplyses om, at indhold sendes til en ekstern AI-tjeneste
  (Anthropic), før upload.
- Endpoints, der eksponerer rå udtræk eller tillader manipulation af samtalen,
  MÅ IKKE være tilgængelige i en offentlig udrulning.
- Hemmeligheder (API-nøgler) SKAL læses fra miljø/`.env` og aldrig committes.

Rationale: Juridisk forpligtelse og tillid — uden den vil ingen uploade deres
pensionsrapport.

### VII. Dansk Brugerflade
Alt brugervendt indhold — UI-tekst, fejlmeddelelser, AI-svar og eksporterede
analyser — SKAL være på dansk, med dansk talformatering (punktum som
tusindtalsseparator, komma som decimaltegn). Siden SKAL have `lang="da"`.
Kode, kommentarer og commits må være på dansk eller engelsk.

Rationale: Målgruppen er danske borgere, der planlægger pension under dansk lov.

### VIII. Simpelhed og Minimale Afhængigheder
Løsningen SKAL forblive en simpel FastAPI-backend med én statisk frontend-fil uden
build-trin. Nye afhængigheder (Python-pakker, frontend-biblioteker) SKAL begrundes
i PR'en: hvilket problem løses, og hvorfor kan det ikke løses simpelt uden. Frontend-
biblioteker fra CDN SKAL pinnes til en eksakt version.

Rationale: Færre dele betyder mindre at vedligeholde, færre sikkerhedsopdateringer
og en kodebase én udvikler kan overskue.

## Teknologibegrænsninger

- Backend: Python, FastAPI og uvicorn. Frontend: `static/index.html` (HTML/CSS/JS)
  med Chart.js som eneste frontend-bibliotek.
- AI: Anthropic Claude via den officielle `anthropic`-pakke, til PDF-udtræk og
  chat. Den statiske del af systemprompten SKAL caches (prompt caching).
- PDF-tekstudtræk: `pdfplumber`.
- Sessioner ligger i hukommelsen. En udrulning med flere processer eller
  vedvarende sessioner kræver en eksplicit begrundet ændring (jf. Princip VI og VIII).
- Offentligt tilgængelige endpoints SKAL have rate limiting og upload-størrelsesloft.
- Langvarige eksterne kald (PDF-udtræk, LLM) SKAL have timeouts, så brugeren altid
  får en forståelig dansk fejlbesked frem for en hængende side.

## Kvalitetsgates

- Hele testsuiten i `tests/` SKAL bestå før merge (Princip III), inklusive de
  server-afhængige tests mod en lokalt kørende app.
- En ændring, der introducerer et tal uden for `satser_2026.py`, SKAL afvises i
  review (Princip II).
- En ændring af prompts SKAL reviewes for, at AI'en ikke får mulighed for selv at
  beregne tal (Princip I).
- Ved årlig satsopdatering SKAL README.md's tjekliste "Årlig satsopdatering" følges,
  inklusive verifikation i browseren.
- Ændringer, der rører persondata, SKAL vurderes mod Princip VI og beskrive
  opbevaring og sletning i plan-dokumentet.
- Nye afhængigheder SKAL fremgå af PR-beskrivelsen med begrundelse (Princip VIII).

## Governance

Denne forfatning har forrang over øvrige praksisser, skabeloner og retningslinjer i
projektet. Ved konflikt mellem forfatningen og andre dokumenter gælder forfatningen.

Ændringer af forfatningen SKAL dokumenteres med en Sync Impact Report og en opdateret
version efter semantisk versionering:
- MAJOR: Fjernelse eller bagudkompatibel omdefinering af et princip.
- MINOR: Nyt princip eller væsentlig udvidelse af en eksisterende regel.
- PATCH: Sproglige præciseringer og andre ikke-semantiske justeringer.

Alle designs, planer og implementeringer (herunder `/speckit-plan`'s Constitution
Check) SKAL vurderes mod principperne ovenfor. Afvigelser SKAL begrundes skriftligt i
plan-dokumentet, før arbejdet fortsætter.

**Version**: 1.0.0 | **Ratified**: 2026-10-24 | **Last Amended**: 2026-10-24
