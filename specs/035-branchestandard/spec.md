# Feature Specification: Branchestandard – prognose som pensionsselskaberne regner

**Feature Branch**: `035-branchestandard`

**Created**: 2026-11-04

**Status**: Draft

**Input**: "Kan min pensionsanalytiker også have en prognose baseret på standardberegningen? Så
kan man selv vælge egne tal eller standard."

**Grundlag**:
- Metoden forklaret: [docs/branchestandard-metode.md](../../docs/branchestandard-metode.md).
- Forsikring & Pension, *Henstilling om pensionsprognoser – opdateret version* (LP-information 20/20,
  7.10.2020, gældende for prognoser fra 1.1.2021). Primærkilde og den nyeste version på
  fogp.dk/branchesamarbejde/pension pr. 2026-11-04. Bilag: 1 (Munk og Rangvid 2017, risikoen i
  pensionsopsparinger), 2 (taleksempel, Excel), 3 (Munk 2017, approksimativ beregning af
  usikkerheden), 4 (Hessler 2018, deterministiske afkaststier), 5–6 (passivsiden).
- Rådet for Afkastforventninger: forventet afkast, standardafvigelse, korrelation og
  investeringsomkostninger pr. aktivklasse samt inflation, for år 1–5, år 6–10 og år 11+. Udsendes
  pr. 1. oktober og 1. april (henstillingen note 1).
- Kernen i dag: `Antagelser.afkast_efter_pal` (standard 4 %) og `inflation` (2 %), ét afkast for
  alle ordninger. 023a (afkast pr. år), 018 (±-scenarier), 016 (Monte Carlo, draft).
- 003: rapporten indeholder selskabernes egne udbetalingsprognoser pr. produkt. I dag omregnes de
  straks til en nutidsværdi for at fordele saldoen (`pdfimport/pensionsinfo.py`), og
  investeringsformen aflæses ikke (FR-015).

## Idé

Borgeren vælger **beregningsgrundlag** med én skifter:

| Valg | Hvad | Hvornår godt |
|---|---|---|
| **Branchestandard** (ny, standard) | Kernen fremregner som henstillingen: Rådets forudsætninger, tre trin, 5 %/middel/95 % | Sammenlignelig med selskabernes tal. Bjælkerne kan stadig flyttes |
| **Egne antagelser** (i dag) | Ét afkast efter PAL-skat og én inflation, som borgeren vælger | "Hvad nu hvis"-regning, forsigtighed |

**Selskabernes egne prognoser** fra rapporten vises som reference. Med branchestandard og
selskabets aftalte pensionsalder skal kernens tal ligge tæt på dem (US4). Det er både en
tillidsfaktor og en test.

## Clarifications

### Session 2026-11-04

- Q: Findes der en nyere version af henstillingen? → A: Nej. fogp.dk linker pr. 2026-11-04 til
  LP-information 20/20 af 7.10.2020 (ændring i pkt. 7.2 i forhold til LP-info 35/19).
- Q: FR-009 forudsætter chatten "Spørg om pension". → A: Chatten (spec 026) og forfatning 2.0.0 er
  ikke merget. FR-009 gælder først, når 026 er merget. Indtil da dækkes kravet af kataloget
  (FR-008), som chatten senere skal bruge.
- Q: Hvordan findes porteføljen pr. ordning? Rapporten oplyser kun investeringsform
  ("Markedsrente", "Gennemsnitsrente", "Flere investeringsformer", "Ingen oplysninger"), ikke
  aktivfordelingen. → A: Kombination efter investeringsform (FR-011 til FR-015):
  - **Markedsrente med prognose**: Aktieandelen udledes af selskabets egen prognose
    (kalibrering). Vises som skøn, som borgeren kan rette.
  - **Markedsrente uden prognose, "Flere" og "Ingen oplysninger"**: Standardprofil (mellem
    risiko) med nedtrapning mod pensionsalderen.
  - **Gennemsnitsrente**: Selskabets prognose bruges direkte. Ingen aktivfordeling.
  - **Senere**: Borgeren vælger sin profil hos selskabet fra et register (uden for scope).
- Q: Hvordan regnes administrationsomkostninger, når ÅOK ikke aflæses? → A: Rådets
  investeringsomkostninger plus en fast administrationsomkostning i kr. pr. år (antagelse i
  registret), indtil ÅOK aflæses. Gælder kun standardprofilen og "angivet af dig". Ved kalibrering
  er selskabets omkostninger allerede opsuget i aktieandelen (`kalibrering_opsuger_omkostninger`).
- Q: Erstatter branchemetodens 5 %/95 %-fraktiler Monte Carlo (016)? → A: Ja. Usikkerhedsviften
  regnes analytisk og deterministisk efter henstillingen. 016 lukkes eller reduceres til en senere
  ekspertvisning.
- Q: Hvilken levetid bruges til livsvarige ydelser? (Henstillingen giver metodefrihed.) → A:
  Finanstilsynets levetidsbenchmark. NB (rettet samme dag): 019 bruger ikke benchmarket. Kernen
  regner i dag livrenten over en fast horisont (`livsvarig_horisont_alder` = 90), og registret har
  kun middellevetiderne for opsat folkepension. Benchmarket skal derfor ind i registret som ny
  post med kilde. Det gælder kun branchestandardens livsvarige forløb. Med `egne` er
  horisonten uændret (SC-001).

### Session 2026-11-05

- Q: Skal borgeren vælge beregningsgrundlag i guiden? → A: Nej (produktejer, 035b). Der regnes altid som
  pensionsselskaberne. Afkast og inflation i guiden er valgfrie egne estimater, og ved resultatet skiftes
  der mellem branchestandarden og de egne estimater. Gemte input åbnes også med branchestandarden; deres
  afkast og inflation er egne estimater. Kernens standard er fortsat `egne` (SC-001), så indgangslaget
  får altid grundlaget fra brugerfladen.

- Q: Hvilket afkast får bufferen (engangsbeløb og opsparing uden for pension) med branchestandarden?
  → A: (produktejer, 035c) Uden eget afkast: Rådets langsigtede afkast for obligationer efter
  investeringsomkostninger og PAL-skat, det samme i alle tre forløb, og borgeren oplyses om det ved beløbet,
  når der er noget i bufferen. Har borgeren selv angivet et afkast, følger bufferen det både med
  branchestandarden og med egne estimater.

## Porteføljen: kalibrering mod selskabets prognose

Selskabets prognose i rapporten er beregnet efter henstillingen med selskabets faktiske
portefølje. Kernen kan derfor finde den aktieandel, der med Rådets forudsætninger og
tretrinsmetoden giver selskabets forventede udbetaling:

1. Input pr. ordning: saldo, årlig indbetaling, udbetalingsform, alder og selskabets forventede
   udbetaling (før skat, nutidskroner).
2. Aktieandelen *a* (0–100 %) i en blandingsportefølje af globale aktier og stats- og
   realkreditobligationer findes ved bisektion, så kernens forventede udbetaling rammer
   selskabets. Forventet afkast er monotont i *a*, så løsningen er entydig.
3. Ligger løsningen uden for 0–100 %, bruges grænsen, og afvigelsen vises.

Kendte svagheder (forenklinger i registret):
- `kalibrering_opsuger_omkostninger`: Selskabets omkostninger og forsikringspriser trækkes med
  ind i aktieandelen.
- `kalibrering_opsuger_levetid`: For livsvarige ordninger trækkes selskabets levetidsantagelse
  med ind. Ratepension og aldersopsparing giver det reneste skøn. En livsvarig ordning hos
  samme selskab og med samme investeringsform arver derfor skønnet fra en ratepension, hvis den
  findes.
- `kalibrering_ingen_nedtrapning`: Livscyklus-nedtrapning bliver til ét gennemsnit.

## Lovgrundlag og kilder (Princip III)

| Element | Kilde | Status |
|---|---|---|
| Tre ydelser: 95 %-fraktil, middelværdi, 5 %-fraktil; benævnelser "Udbetaling ved højt / forventet / lavt afkast" | Henstillingen pkt. 6.1 og 7.1 | verificeret (branchestandard, ikke lov) |
| Tretrinsmetoden og Munks approksimative formler for middelværdi, varians og fraktiler | Henstillingen pkt. 7.1 og appendiks 1, bilag 3 (Munk) og bilag 4 (Hessler) | verificeret |
| Rådets forudsætninger for år 1–5, år 6–10 og år 11+. Investeringsomkostninger for år 1–10 | Henstillingen pkt. 7.2 | verificeret |
| Nutidskroner, ydelse før indkomstskat | Henstillingen pkt. 5 og 5.1 | verificeret |
| Indbetalinger og omkostninger prisindekseres (uændrede i nutidskroner) | Henstillingen pkt. 7.2 | verificeret |
| PAL-skat 15,3 % | PAL § 2 (i registret) | verificeret |
| Rådets forudsætninger for 1. halvår 2027 (offentliggjort 2.11.2026): 10 aktivklasser for år 1–5, 6–10 og 1–10, tre aktivklasser (obligationer, illikvide, aktier) for år 11+, standardafvigelser, korrelationer, investeringsomkostninger og inflation | afkastforventninger.dk, regneark "afkastforventninger-1-halvar-2027.xlsx" | skal ind i registret |
| Finanstilsynets levetidsbenchmark (livsvarige ydelser) | finanstilsynet.dk | skal ind i registret |

Henstillingen er en branchestandard, ikke lov. Det SKAL fremgå af forklaringerne.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Vælg beregningsgrundlag (Priority: P1)

Over hovedtallet står "Beregnet som pensionsselskaberne (branchestandard)" med skifteren
"Brug mine egne antagelser". Alle tal (hovedtal, graf, år for år, optimering) følger valget.

**Acceptance Scenarios**:

1. **Given** standardvalget, **Then** er hovedtallet beregnet med Rådets forudsætninger og står i
   nutidskroner efter skat.
2. **Given** skift til egne antagelser, **Then** er resultatet identisk med i dag (SC-001).
3. **Given** et gemt input fra før featuren, **Then** åbnes det med branchestandarden, og de gemte
   tal for afkast og inflation er egne estimater, som skifteren bruger (035b).

---

### User Story 2 - Udbetaling ved højt, forventet og lavt afkast (Priority: P1)

Med branchestandard viser hovedtallet og grafen tre niveauer med branchens benævnelser. Spændet
dækker 90 % af udfaldene for afkastet. Forklaringen bruger henstillingens standardtekst om
usikkerhed (pkt. 6.2, tilpasset til efter skat).

**Acceptance Scenarios**:

1. **Given** en ordning med kendt saldo og indbetaling, **Then** svarer kernens 5 %-, middel- og
   95 %-formue til henstillingens taleksempel (bilag 2) inden for afrunding.
2. **Given** tre niveauer, **Then** beregnes skat, pensionstillæg og ældrecheck for hvert niveau
   for sig. Spændet efter skat er ikke bare spændet før skat skaleret.

---

### User Story 3 - Skønnet portefølje, som du kan rette (Priority: P1)

Pr. ordning står fx "Skønnet ud fra dit selskabs prognose: ca. 55 % aktier". Borgeren kan rette
skønnet, vælge standardprofilen eller angive sin profil hos selskabet som aktieandel.

**Acceptance Scenarios**:

1. **Given** en markedsrenteordning med prognose, **Then** vises den kalibrerede aktieandel med
   status "skøn".
2. **Given** at borgeren retter aktieandelen, **Then** genberegnes alle tre forløb, og status
   bliver "angivet af dig".
3. **Given** en gennemsnitsrenteordning, **Then** vises "Bruger dit selskabs egen prognose", og
   der er ingen aktieandel at rette.
4. **Given** "Ingen oplysninger" eller ingen prognose, **Then** bruges standardprofilen, og det
   fremgår.

---

### User Story 4 - Sammenlign med selskabernes egne prognoser (Priority: P2)

En fold-ud viser pr. ordning selskabets prognose fra rapporten ved siden af kernens
branchestandard ved samme alder og udbetalingsform, før skat.

**Acceptance Scenarios**:

1. **Given** en kalibreret ordning, **Then** sammenlignes ved en anden alder eller udbetalingsform
   end den, der er kalibreret på. Afvigelsen skal være under en tolerance (fastsættes i plan, fx
   5 %). Sammenligningen på kalibreringsalderen er pr. definition 0 og bruges ikke som test.
2. **Given** en større afvigelse, **Then** vises den med mulige årsager (anden portefølje,
   omkostninger, udjævning, garanti), og der vises ingen fejl.

### Edge Cases

- **Gennemsnitsrente- og garanterede produkter**: Selskabets prognose bruges direkte (US3). Ved
  ændret alder eller udbetalingsform skaleres den med kernens annuitetsfaktor (forenkling,
  markeret).
- **Kalibreringen rammer 0 % eller 100 % aktier**: Grænsen bruges og vises med mulige årsager
  (høje omkostninger, garanti, særlig udjævning).
- **Flere ordninger hos samme selskab**: Kalibreres hver for sig. Afviger skønnene meget, vises
  det.
- **Ordning under udbetaling**: Fremregnes fra nuværende depot. Ingen 1. års-krav (pkt. 5.1).
- **Depotet løber tør i et lavt-afkast-forløb**: Henstillingens regel: brug seneste beregnelige
  afkast for resten af perioden.
- **Livsvarig pension**: Tilføj henstillingens tekst om levetidsrisiko.
- **Rådet udsender nye forudsætninger** (1. oktober eller 1. april): nyt registersæt med dato.
  Satsåret vises.
- **Manuelt indtastet ordning (uden rapport)**: Ingen investeringsform og ingen prognose, så
  standardprofilen bruges.

## Requirements *(mandatory)*

- **FR-001**: `Antagelser` MUST have et beregningsgrundlag: `branchestandard` eller `egne`. Med
  `egne` er alt som i dag.
- **FR-002**: Med `branchestandard` MUST kernen fremregne hver ordning efter tretrinsmetoden:
  1. Middelværdi og varians rekursivt uden omkostninger og PAL-skat. Fraktiler ved log-normal
     approksimation (Munk).
  2. Tre afkaststier ud fra fraktilerne.
  3. Fremregning med investeringsomkostninger, PAL-skat og omkostninger på hver sti.
- **FR-003**: Rådets forudsætninger (forventet afkast, standardafvigelse, korrelation,
  investeringsomkostninger pr. aktivklasse og inflation pr. periode) MUST ligge i
  regelregistret med kilde, udgivelsesdato og status (Princip II).
- **FR-004**: Standardprofilen og nedtrapningen MUST ligge i registret som antagelser med
  begrundelse og vises for borgeren (Princip III).
- **FR-005**: Indbetalinger og omkostninger MUST være uændrede i nutidskroner. Folkepension og
  satser reguleres med Rådets inflation.
- **FR-006**: Skat, pensionstillæg, ældrecheck, udjævning og optimering MUST køre uændret på hvert
  af de tre forløb (Princip VI). Optimeringen bruger det forventede forløb.
- **FR-007**: Benævnelserne "Udbetaling ved højt afkast", "… forventet afkast" og "… lavt afkast"
  MUST bruges, med tilføjelsen "efter skat" (Princip VIII).
- **FR-008**: Forklaringskataloget MUST have tekst på tre niveauer for skifteren, de tre niveauer,
  metoden, Rådets forudsætninger, porteføljerne og sammenligningen med selskabernes tal (Sådan
  regner vi, FR-006).
- **FR-009**: Når chatten "Spørg om pension" (026) er merget, MUST den kunne forklare
  branchestandarden generelt ud fra kataloget. Ingen persondata (Princip XI).
- **FR-010**: Princip X: skifteren er ét valg med forklaring i konteksten. Tre niveauer i grafen
  skelnes med mønster og tekst, ikke kun farve.
- **FR-011**: Porteføljen pr. ordning MUST vælges efter investeringsform som besluttet i
  Clarifications. Kilden (skøn, standard, angivet af dig, selskabets prognose) MUST følge
  ordningen og vises.
- **FR-012**: Kalibreringen MUST være deterministisk (bisektion med fast tolerance og maksimalt
  antal iterationer) og MUST foretrække ratepension og aldersopsparing frem for livsvarige
  ordninger (se Porteføljen).
- **FR-013**: De tre kalibreringsforenklinger MUST ligge i forenklingsregistret og nævnes ved
  skønnet (Princip III og V).
- **FR-014**: For gennemsnitsrente MUST selskabets prognose bruges som forventet forløb. Høj og
  lav vises kun, hvis rapporten oplyser dem. Ellers vises kun forventet med forklaring.
- **FR-015**: PDF-importen (003) MUST pr. produkt bevare selskabets forventede udbetaling (beløb,
  form, startalder) og aflæse investeringsformen. Begge er input til kalibreringen. Lokalt og
  deterministisk som i dag, og intet skrives til disk.

### Key Entities

- **Beregningsgrundlag**: branchestandard eller egne.
- **Forudsætningssæt (Rådet)**: udgivelsesdato, aktivklasser, perioder, inflation.
- **Standardportefølje**: profil, vægte pr. aktivklasse, nedtrapning.
- **Porteføljeskøn**: ordning, aktieandel, kilde (skøn/standard/angivet/selskabets prognose),
  kalibreringsafvigelse.
- **Selskabsprognose**: ordning, investeringsform, forventet udbetaling, form, startalder.
- **Prognoseforløb**: højt, forventet og lavt, pr. ordning og samlet.

## Success Criteria *(mandatory)*

- **SC-001**: Med `egne` er alle eksisterende tests og golden cases grønne uden ændringer.
- **SC-002**: Kernens trin 1–2 genskaber henstillingens taleksempel (bilag 2) inden for afrunding.
- **SC-003**: Golden cases for tre ordningstyper (rate, livsvarig, aldersopsparing) med
  kildehenvisning.
- **SC-004**: Afvigelse mod selskabernes prognose ved en anden alder end kalibreringsalderen
  under tolerancen (US4).
- **SC-005**: Ny beregning på under 2 s i browseren (tre forløb og to personer).
- **SC-006**: Samme resultat i Pyodide og CPython.
- **SC-007**: Kalibreringen genfinder en kendt aktieandel inden for 2 procentpoint, når selskabets
  prognose er beregnet med kernen selv (rundturstest).

## Uden for scope

- Garanterede og gennemsnitsrente-produkter efter henstillingens tjekliste (appendiks 3)
- Aflæsning af ÅOK fra rapporten
- Register over selskabernes profiler med offentliggjort aktivfordeling (forbedring af
  "angivet af dig")
- Bankernes pensionsprodukter, hvis de følger en anden standard
