# Feature Specification: Sådan regner vi – forklaring i tre niveauer

**Feature Branch**: `020-forklaring`

**Created**: 2026-10-26

**Status**: Implementeret 2026-10-27 (020a–d). SC-004 (brugertest) udestår, se ux-evaluering.md

**Input**: "Det er vigtigt at kunne forklare, hvordan pensionsanalytikeren regner – for newbies,
almindeligt vidende og eksperter. Alt væsentligt ift. præsentation og beregninger skal
redegøres for."

**Grundlag**:
- Princip I (AI beregner aldrig), III (lovgrundlag og forenklinger), V (sporbarhed), X (svaret
  først, progressiv afsløring, klarsprog) og XI (ingen persondata til AI)
- Kernens output: `Aarsresultat.sporing` og `flag`, `Fremskrivning.sporing_samlet`, `advarsler`,
  `antagelser`, `jaevn`, `buffer_iterationer` og `formue` (013)
- Regelregistret (`register/2026.toml`): id, værdi, enhed, kilde og status pr. post
- Brugerfladens katalog (`pensionsoverblik/katalog.py`): korttekster og advarsler
- 002 FR-022 (detaljer bag fold-ud) og 002's udskudte "AI-forklaring"

**Det, der findes i dag** (konstateret under clarify):
- Kortene har en "Hvad er …?"-knap med en kort forklaring.
- "Sådan har vi regnet" har en tabel år for år, satserne med kilde og status og
  forudsætningerne.
- Hvert år har kilderne med brutto, skat og netto, indtægtsgrundlaget og tillægsprocenten.
- Kernen markerer forenklinger som flag pr. år:
  - `forenkling:kapitalindkomst_ikke_beskattet`
  - `forenkling:partnerindkomst_naermeste_aar`
  - `skoennet_atp`
- Advarslerne har et katalog med titel, ikon og placering.

Featuren handler derfor mest om et fælles katalog og tre niveauer, ikke om ny beregning.

## Clarifications

### Session 2026-10-26

- **Niveauvalg**: Niveauet vælges én gang og huskes lokalt i browseren. Ved det enkelte tal kan
  man åbne et dybere niveau. Uden et gemt valg er niveau 1 standard. Valget kan nulstilles
  (FR-008).
- **Metodebeskrivelse som PDF**: En udskriftsvenlig side er nok. Den slås sammen med "Rapport til
  rådgiveren" fra roadmappen, så der ikke kommer en ny afhængighed til at lave PDF.
- **Eksport**: Både JSON (hele beregningen, fuld præcision) og CSV (år for år, til regneark).
- **AI-forklaringen (002)**: Den forbliver udskudt. En senere AI-chat må kun bruge kataloget med
  ord og pladsholdere, aldrig de udfyldte tekster. De indeholder borgerens tal og er persondata
  (Princip XI).

### Ændringer i forhold til udkastet (fundet under clarify)

1. **FR-003 er gjort smallere.** En generel "forklaring pr. tal" fra kernen er en stor ombygning.
   I stedet udvides det, kernen allerede leverer pr. år, med tre ting:
   - skatten pr. type: bund, mellem, top, toptop, kommune og kirke, personfradraget og
     skatteloftets nedslag (`Skatteberegning` findes allerede i `regler/skat.py`)
   - pensionstillægget før og efter modregning
   - formuen pr. 1. januar i forhold til ældrechecks grænse
2. **FR-004 (afstemning) gælder tal, der er en sum.**
   - Et år afstemmer: brutto → skat → netto.
   - Hovedtallet er det faste beløb efter udjævning (008–010). Dets regnestykke er udjævningen,
     ikke en sum af linjer, så niveau 2 forklarer udjævningen med borgerens tal.
   - Skatten pr. indkomstkilde er en fordeling, der kun bruges i visningen. Loven beskatter den
     samlede indkomst. Niveau 2 skal sige det, så fordelingen ikke ser ud som lov.
3. **FR-002 og FR-006 bygger på emner.** Tre niveauer for hver registerpost ville være ca. 165
   håndskrevne tekster.
   - Hver registerpost peger på et emne (fx "Skattetrin").
   - Niveau 1 og 2 skrives pr. emne.
   - Niveau 3 for en post laves automatisk ud fra id, værdi, satsår, kilde og status.
   - Testen kræver, at hver post har et emne, og at hvert emne har tekst på alle tre niveauer.
4. **Forenklingsregistret (FR-005) laves som en fil.** Hver forenkling har id, beskrivelse,
   begrundelse og betydning. En test kræver, at hver markering i kernen (`o.marker(...)`) findes
   i registret. I dag ligger forenklingerne spredt i kernen og i domænedokumentet.
5. **US3 forudsætter skifteren mellem nominelle beløb og dagens kroner.** Den findes ikke endnu.
   Den står på roadmappen som en lille gevinst og laves før 020b.
6. **"Klik på en søjle" må ikke ramme tidslinjen.** Et klik på en bjælke vælger i dag ordningen
   til justering (006). "Dit år" åbnes fra grafens søjler og fra rækkerne i år-for-år-tabellen.
7. **SC-004 (brugertest) er et manuelt krav.** Det kan ikke automatiseres. Det registreres i
   `ux-evaluering.md` og er ikke en betingelse for merge. LIX-kravet (SC-005) testes automatisk.
8. **SC-007 (300 ms)**: Forklaringerne bygges af data, der allerede følger med beregningen. Der
   er intet ekstra kald til motoren, når en forklaring åbnes.

## Tre niveauer

| Niveau | Målgruppe | Indhold | Form |
|---|---|---|---|
| **1. Kort fortalt** | Ny i pension | Hvad tallet betyder for dig, og hvad der påvirker det. Ingen paragraffer, ingen formler | 1–3 korte sætninger i "du"-form, evt. et hverdagseksempel |
| **2. Sådan regner vi** | Almindeligt vidende | Regnestykket trin for trin med *dine egne tal*, fagudtryk forklaret | Opstillet regnestykke: brutto → skat pr. type → modregning → netto |
| **3. For eksperter** | Rådgiver, revisor, fagperson | Lovhenvisning, registerposter (id, værdi, satsår, status), formel, forenklinger, antagelser, iterationer og søgeomfang | Tabel og formel, eksport af hele regnestykket |

Hvert niveau bygger på det forrige og modsiger det aldrig. Niveau 1 er standard (Princip X).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - "Hvordan fremkommer dette tal?" (Priority: P1, 020a: hovedtallet; 020b: øvrige tal)

Ved hvert tal, borgeren ser (hovedtallet, et kort, en søjle i grafen, en celle i år for år),
er der en forklaringsknap. Den åbner forklaringen på det valgte niveau og kan skifte niveau på
stedet.

**Acceptance Scenarios**:

1. **Given** hovedtallet (det faste beløb), **When** forklaringen åbnes på niveau 1, **Then** står
   der, hvad beløbet er (efter skat, pr. måned, ens hele perioden), og de 2–3 ting, der påvirker
   det mest.
2. **Given** samme tal på niveau 2, **Then** forklares udjævningen med borgerens tal: hvad der
   kommer ind, hvad der spares op, og hvornår opsparingen er brugt (ændring 2).
3. **Given** niveau 3, **Then** vises hver registerpost med id, værdi, satsår, kilde og status,
   og uverificerede poster er markeret med fast ikon og tekst (ikke kun farve).
4. **Given** tastatur og skærmlæser, **Then** kan forklaringen åbnes, læses og lukkes (WCAG 2.2
   AA).

---

### User Story 2 - Forklaring af et år (Priority: P1, 020a)

Klik på en søjle i grafen eller en række i år-for-år-tabellen åbner "Dit år [kalenderår] (du er
[alder])":

- **Niveau 1**: Hvor pengene kommer fra, og hvorfor beløbet er anderledes end året før (fx
  "Ratepensionen stopper, så pensionstillægget stiger").
- **Niveau 2**: Hver indkomstkilde brutto → skat → netto, indtægtsgrundlag, tillægsprocent,
  pensionstillæg før og efter modregning, ældrecheck ja/nej med formue mod grænse, træk fra eller
  indskud i bufferen.
- **Niveau 3**: Skattegrundlag pr. skattetype (bund, mellem, top, toptop, kommune, kirke),
  personfradrag og skatteloft, kapitalindkomst og bundfradrag, realfaktor, ægtefælleoverførsler
  (012) og den fulde sporing for året.

**Acceptance Scenarios**:

1. **Given** et år, hvor tallet ændrer sig mere end en tærskel i forhold til året før, **Then**
   nævner niveau 1 årsagen (den største ændring først).
2. **Given** et år med modregning, **Then** viser niveau 2 både tillæg før og efter modregning.
3. **Given** et år, **Then** summerer niveau 2 til årets netto inden for visningens afrunding
   (FR-004).

---

### User Story 3 - Forklaring af præsentationen (Priority: P1, 020b)

Hver visning har en forklaring af, *hvordan den skal læses*:

- **Hovedtal**: efter skat, pr. måned, nominelt eller i dagens kroner, hvilken periode.
- **Graf**: hvad søjler, farver, linjen "Fast beløb, hvis du udjævner" og stiplede forslag betyder.
- **Tidslinje**: bjælkernes start, længde og greb, og hvad det betyder at flytte dem.
- **Opsparingsgrafen** (bufferen): hvad den er, og hvorfor den aldrig går i minus (010).
- **Faner** Dig, Partner og Samlet: hvad der er summeret, og hvad der er koblet.
- **Statusikoner**: verificeret, forenkling, antagelse og advarsel.
- **Usikkerhed og levetid** (018, 019): hvad scenarierne ændrer, og hvad de ikke ændrer.

**Acceptance Scenarios**:

1. **Given** grafen, **When** "Sådan læser du grafen" åbnes, **Then** forklares hver serie og
   farve, der faktisk vises, og ingen andre.
2. **Given** skifteren nominel/dagens kroner, **Then** forklares forskellen med et eksempel fra
   borgerens egne tal. Kræver skifteren (ændring 5).

---

### User Story 4 - Metodebeskrivelse: "Sådan regner PensionsAnalytikeren" (Priority: P2, 020d)

En selvstændig side (også uden indtastede data) med hele metoden, opdelt i de tre niveauer. Den
dækker alle punkter i **Forklaringsinventaret** nedenfor og genereres fra samme katalog og
regelregister som forklaringerne i US1–US3, så de aldrig kan være uenige. Siden kan udskrives
(erstatter PDF).

**Acceptance Scenarios**:

1. **Given** et nyt satsår i registret, **When** siden bygges, **Then** viser den de nye satser
   uden ændring af tekst.
2. **Given** en registerpost uden emne i kataloget, **Then** fejler bygget (FR-006).

---

### User Story 5 - Forklaring af optimeringen og forbehold (Priority: P2, 020c)

"Find bedste plan" (007) forklarer:
- **Niveau 1**: hvad forslaget ændrer, og hvad du får ud af det i kr. pr. måned (findes delvis).
- **Niveau 2**: hvilket mål der optimeres (højeste faste beløb uden nye indkomsthuller), og
  hvilke valg der er afprøvet.
- **Niveau 3**: søgerum, antal evaluerede ud af mulige kombinationer (findes), begrænsninger og
  stopkriterium (Princip V).

Alle forklaringer, der indeholder en anbefaling, har forbeholdet "information, ikke
rådgivning" med henvisning til en certificeret pensionsrådgiver (Princip V).

---

### User Story 6 - Eksport af regnestykket (Priority: P3, 020d)

En ekspert kan eksportere hele beregningen som JSON og år for år som CSV: input (uden CPR, navne
og policenumre), satsår, registerposter med status, antagelser, år-for-år-resultater og sporing.
Eksporten laves lokalt i browseren (Princip VII).

### Edge Cases

- **Uverificeret sats** indgår i et tal: alle tre niveauer siger det (niveau 1 med én sætning).
- **Forenkling** påvirker tallet: forenklingen nævnes ved tallet med betydning for resultatet
  (Princip III og V).
- **Fastpunktet konvergerede ikke**: forklaringen siger det og viser advarslen.
- **Tal = 0** (fx ingen ældrecheck): forklaringen siger hvorfor (fx formue over grænsen eller
  indkomst for høj).
- **Partner**: det fremgår altid, hvem tallet gælder, og hvilke koblinger der påvirker det.

## Forklaringsinventar (skal dækkes på alle tre niveauer)

**Beregninger**
- Folkepensionsalder og opsat folkepension
- Folkepension: grundbeløb, pensionstillæg, indtægtsgrundlag, modregning, tillægsprocent
- Ældrecheck og mediecheck, likvid formue og formuegrænse
- ATP
- Ratepension (stigende udbetaling), livsvarig pension, aldersopsparing, kapitalpension
  (afgift, portioner efter PBL § 26, omlægning efter § 41)
- Indkomstskat: bund, mellem, top, toptop, kommune, kirke, personfradrag, skatteloft
- AM-bidrag (og hvorfor det ikke betales af pension)
- Kapitalindkomst og bundfradrag (bufferens og opsparingens afkast)
- Udjævning, fast beløb og buffer uden lån (008–010)
- Opsparing uden for pension: i planen eller urørt, restformue (013)
- Usikkerhed om afkast og inflation (018) og levetid som scenarie (019)
- Optimering (007)
- Husstand og partner: koblinger og ægtefælleoverførsler (012)
- Afkast, inflation, satsregulering og realfaktor (antagelser)
- Fastpunkt-iterationer
- Afrunding og præcision i visningen
- PDF-aflæsning: hvad der læses fra PensionsInfo, hvad der ikke læses, og hvad brugeren selv
  skal tjekke (003)

**Præsentation**
- Hovedtal, kort, graf, tidslinje, opsparingsgraf, faner, statusikoner og farver
- Nominelle beløb og dagens kroner, måned og år, alder og kalenderår

**Forbehold**
- Information, ikke rådgivning
- Liste over forenklinger (fra forenklingsregistret)
- Liste over antagelser og deres standardværdier med kilde
- Satsår og verifikationsstatus

Nye features (fx 013b og 017) SKAL tilføje deres punkter til inventaret.

## Requirements *(mandatory)*

- **FR-001**: Alle forklaringer MUST være deterministiske tekstskabeloner udfyldt med tal fra
  kernen og regelregistret. Ingen AI genererer eller beregner forklaringstekst (Princip I og XI).
- **FR-002**: Et forklaringskatalog MUST indeholde tekst på niveau 1, 2 og 3 for hvert emne:
  hvert punkt i inventaret, hver advarselskode, hver korttype og hver visning. Registerposter
  peger på et emne. Niveau 3 for den enkelte post laves ud fra registret. Kataloget indeholder ord
  og pladsholdere, aldrig tal (Princip II).
- **FR-003**: Kernen MUST pr. år levere skatten pr. type (inkl. personfradrag og skatteloftets
  nedslag), pensionstillægget før og efter modregning og formuen pr. 1. januar i forhold til
  ældrechecks grænse. Brugerfladen regner ikke selv (Princip VI).
- **FR-004**: Regnestykket på niveau 2 MUST afstemme for tal, der er en sum (et år): linjerne
  summerer til det viste tal inden for visningens afrunding. Hovedtallet forklares med
  udjævningen.
- **FR-005**: Forenklinger MUST ligge i et register (id, beskrivelse, begrundelse, betydning for
  resultatet), som forklaringerne og metodesiden læser fra (Princip III). Hver markering i kernen
  MUST findes i registret.
- **FR-006**: En automatisk test MUST fejle, hvis et inventarpunkt, en advarselskode, en
  forenkling eller et emne mangler tekst på et af de tre niveauer, eller hvis en registerpost
  mangler et emne.
- **FR-007**: Niveau 1 MUST følge klarsprog: korte sætninger, aktiv form, ingen paragraffer,
  fagudtryk forklaret i teksten (Princip X).
- **FR-008**: Niveauvalget huskes kun lokalt i browseren og kan nulstilles (Princip VII).
- **FR-009**: Fagudtryk i forklaringerne MUST følge myndighedernes terminologi og have en
  ordliste med de samme tre niveauer (Princip VIII). (020b)
- **FR-010**: Princip X: axe 0 fejl, ingen vandret scroll ved 360 px, forklaringen må ikke dække
  det tal, den forklarer, på mobil.

### Key Entities

- **Forklaringskatalog**: tekstskabeloner pr. emne og niveau.
- **Emne**: et begreb (fx "Skattetrin", "Pensionstillæg"), som registerposter og visninger peger på.
- **Årets detaljer (kernen)**: skat pr. type, tillæg før og efter modregning, formue mod grænse.
- **Forenklingsregister**: forenklinger med begrundelse og betydning.
- **Ordliste**: fagudtryk med forklaring på tre niveauer.

## Success Criteria *(mandatory)*

- **SC-001**: 100 % dækning: hvert inventarpunkt, hver advarsel, hver forenkling og hvert emne har
  tekst på alle tre niveauer, og hver registerpost har et emne (FR-006).
- **SC-002**: Afstemning: for alle golden cases summerer niveau 2 for hvert år til årets netto.
- **SC-003**: Niveau 3 for et tal kan genberegnes i hånden af en fagperson ud fra forklaringen
  alene (verificeres i 3 golden cases).
- **SC-004** (manuel, ikke betingelse for merge): Brugertest med mindst 3 personer pr. målgruppe
  (ny, almindeligt vidende, ekspert). Mindst 4 ud af 5 opgaver af typen "hvorfor er dette tal
  sådan?" løses uden hjælp. Resultatet står i `ux-evaluering.md`.
- **SC-005**: Niveau 1-tekster har en LIX under 35 (automatisk test).
- **SC-006**: Samme forklaringer i Pyodide og CPython.
- **SC-007**: En forklaring åbner på under 300 ms i browseren, uden kald til motoren.

## Foreslået opdeling

| Feature | Indhold | Forudsætter |
|---|---|---|
| **020a (P1)** | Forenklingsregistret, kataloget med emner og testen af dækning, niveauvalget, kernens årsdetaljer (FR-003), forklaringen af hovedtallet (US1) og "Dit år" (US2) | – |
| **020b** | Forklaring af præsentationen (US3), de øvrige tal (US1) og ordlisten | Skifteren mellem nominelle beløb og dagens kroner |
| **020c** | Forklaring af optimeringen (US5) | 020a |
| **020d** | Metodesiden, eksport og udskrift (US4, US6), slået sammen med "Rapport til rådgiveren" | 020a |

**Besluttet 2026-10-26** (projektejeren): Opdelingen er godkendt. Forenklingsregistret (fra 020a)
laves først, fordi det er lille og gør de eksisterende forenklinger synlige. Resten af 020 kommer
efter 017.

## Uden for scope

- AI-genererede forklaringer og AI-chat (se Clarifications).
- Forklaringer på andre sprog end dansk.
