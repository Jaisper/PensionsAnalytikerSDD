# Sådan fungerer PensionsAnalytikeren – metodebeskrivelse

**Formål**: En samlet redegørelse for, hvordan løsningen fungerer: fra en PensionsInfo-rapport lægges
ind, over beregningsmotoren, til tallene på skærmen. Dokumentet er skrevet til revision og anden
uafhængig gennemgang.

**Gælder for**: `main` pr. 2026-11-24 (commit `9e54f6e`), satsår 2026. Dokumentet beskriver koden, som
den er. Ændres koden, skal dokumentet følge med.

**Satser og kilder** står ikke her. De ligger ét sted, i regelregistret, med kilde og status pr. sats
(afsnit 5). Borgeren og revisor kan se dem i løsningen under "Sådan regner PensionsAnalytikeren"
(nederst på siden) og i filerne [`src/pensionskerne/register/2026.toml`](../src/pensionskerne/register/2026.toml),
[`kommuner_2026.toml`](../src/pensionskerne/register/kommuner_2026.toml) og
[`forenklinger.toml`](../src/pensionskerne/register/forenklinger.toml).

**Andre dokumenter**, som dette bygger på og henviser til:

| Dokument | Indhold |
|---|---|
| [`.specify/memory/constitution.md`](../.specify/memory/constitution.md) | Forfatningen: de principper, al kode skal følge (fx Princip I, III og XI nedenfor) |
| [`docs/domaene/beregningskerne.md`](domaene/beregningskerne.md) | Lovgrundlaget pr. regel, afvigelser fra den tidligere løsning (A1–A14) og noter pr. feature |
| [`docs/branchestandard-metode.md`](branchestandard-metode.md) | Prognosemetoden "som pensionsselskaberne" (F&P's henstilling) i detaljer |
| [`specs/NNN-*/spec.md`](../specs/) | Krav, afklaringer og beslutninger pr. feature (001–038) |

Henvisninger som `fremskrivning.py:223` peger på en fil og en linje i koden.

---

## Indhold

1. [Overblik](#1-overblik)
2. [Data, privatliv og sikkerhed](#2-data-privatliv-og-sikkerhed)
3. [Indlæsning af PensionsInfo-rapporten](#3-indlæsning-af-pensionsinfo-rapporten)
4. [Borgerens input og oversættelsen til kernen](#4-borgerens-input-og-oversættelsen-til-kernen)
5. [Regelregistret og sporbarhed](#5-regelregistret-og-sporbarhed)
6. [Beregningsmotoren år for år](#6-beregningsmotoren-år-for-år)
7. [Par og husstand](#7-par-og-husstand)
8. [Prognose som pensionsselskaberne (branchestandard)](#8-prognose-som-pensionsselskaberne-branchestandard)
9. ["Find bedste plan" (optimering)](#9-find-bedste-plan-optimering)
10. [Øvrige beregninger](#10-øvrige-beregninger)
11. [Fra resultat til skærm](#11-fra-resultat-til-skærm)
12. [Kvalitetssikring](#12-kvalitetssikring)
13. [Forenklinger, begrænsninger og kendte afvigelser](#13-forenklinger-begrænsninger-og-kendte-afvigelser)

---

## 1. Overblik

PensionsAnalytikeren svarer på ét spørgsmål: *Hvad kan jeg regne med at få udbetalt om måneden efter
skat?* Den regner borgerens private pensioner, ATP, folkepension og tillæg, løn, opsparing uden for
pension og skat ud år for år efter gældende regler og viser et fast månedligt beløb i dagens kroner.

Løsningen er **information, ikke rådgivning**. Den bygger på borgerens oplysninger, gældende regler for
satsåret og antagelser om fremtiden (afkast, inflation, levetid), som ingen kender.

### Arkitektur

Der er ingen server, der regner eller gemmer noget. Hele løsningen kører i borgerens browser:

```
 Browser (borgerens computer)
 ┌──────────────────────────────────────────────────────────────────────────────────┐
 │  Siden (index.html, app.js)            Worker (Pyodide = Python i WebAssembly)   │
 │  ─────────────────────────             ──────────────────────────────────────    │
 │  guide, resultat, grafer   ── kald ──▶  pensionsoverblik/app.py   (indgangspunkt) │
 │  (omformaterer kun tal)    ◀── svar ──    ├─ pdfimport/   PDF → guidedata        │
 │                                           ├─ oversaet.py  guidedata → kernens     │
 │                                           │               datamodel + validering  │
 │                                           ├─ pensionskerne/  BEREGNINGEN          │
 │                                           │    fremskrivning, regler, register,   │
 │                                           │    jaevn, husstand, prognose,         │
 │                                           │    optimering, forsikring             │
 │                                           └─ visning.py   resultat → visning      │
 └──────────────────────────────────────────────────────────────────────────────────┘
        ▲ henter kun sidens egne, statiske filer (GitHub Pages). Sender intet.
```

- **Beregningskernen** (`src/pensionskerne/`) er ren Python uden netværk, filer eller tilfældighed. Én
  offentlig funktion, `beregn(profil, antagelser, satsaar, beregningsdato)`, giver en fuld
  fremskrivning år for år.
- **Regelmodulerne** (`src/pensionskerne/regler/`) har ét modul pr. lovområde (skat, folkepension,
  ydelser, ordninger, løn, aktier, opsat pension, udbetalingsalder). De indeholder ingen tal. Alle
  satser hentes fra registret (afsnit 5).
- **Brugerfladen** (`src/pensionsoverblik/`) indlæser rapporten, samler borgerens svar, kalder kernen og
  omformaterer resultatet. Den beregner ikke selv skat, ydelser eller satser (Princip X, FR-001 i 002).

### Principper, der styrer metoden

Forfatningen ([`constitution.md`](../.specify/memory/constitution.md)) har forrang for al kode. De
vigtigste for denne redegørelse:

| Princip | Betydning i praksis |
|---|---|
| I. Deterministisk beregning | Samme input giver altid samme tal. Ingen AI beregner eller præsenterer tal |
| II. Regelregister | Alle satser står ét sted med kilde og status. Ingen tal i regelmodulerne (testet) |
| III. Lovgivningen er facit | En regel eller sats kræver en kilde. Afvigelser fra loven er eksplicitte forenklinger |
| IV. Test først | Hver regel har test med facit-tal (golden cases) |
| V. Sporbarhed | Hvert tal kan føres tilbage til de satser og antagelser, der blev brugt |
| XI. Ingen persondata til AI (NON-NEGOTIABLE) | Ingen AI-klienter, -afhængigheder eller -endpoints i koden (testet) |

---

## 2. Data, privatliv og sikkerhed

Kort fortalt: **Al behandling sker i borgerens egen browser. Der er ingen server, der modtager, regner på
eller gemmer borgerens data, og løsningen sender intet ud.** Afsnittet redegør for, hvorfor det holder,
hvordan det er kontrolleret, og hvor grænserne går.

### 2.1 Hvilke persondata indgår

| Data | Kilde | Bruges til | Hvor længe |
|---|---|---|---|
| PensionsInfo-rapporten (PDF) med navn, CPR, aftalenumre, saldi, forsikringer | Borgeren vælger filen | Kun aflæsning (afsnit 3) | I hukommelsen, mens aflæsningen kører. Rapporten gemmes ikke |
| Fødselsdato | Udledt af CPR på forsiden eller indtastet | Alder og folkepensionsalder | Mens siden er åben |
| Ordninger (selskab, aftalenummer, type, saldo, indbetaling, alder) | Rapporten eller indtastet | Beregningen | Mens siden er åben |
| Løn, opsparing, kommune, civilstand, folkekirke, partner | Indtastet | Beregningen | Mens siden er åben |
| Forsikringer (selskab, aftale, modtager, beløb) | Rapporten | Visning efter skat | Mens siden er åben |
| Resultater (beløb år for år) | Beregnet | Visning | Mens siden er åben |

**Navnet læses ikke. CPR-nummeret bruges kun til at udlede fødselsdatoen og gemmes ikke**
(`foedselsdato_fra_rapport`, afsnit 3.1). Der er ingen brugerkonti, ingen login og ingen identifikation
af borgeren.

### 2.2 Hvor data behandles: kun i browseren

```
  Borgerens computer                                        Internettet
  ┌───────────────────────────────────────────────┐
  │  Browserfanen                                 │        GitHub Pages
  │  ┌──────────────┐  postMessage  ┌──────────┐  │  GET   (statiske filer:
  │  │ Siden        │◀────────────▶│ Worker   │  │◀────── HTML, JS, Pyodide,
  │  │ (app.js)     │  kun i samme │ (Pyodide)│  │        Python-pakker)
  │  └──────────────┘  fane        └──────────┘  │
  │        │                                      │  ✗ Ingen POST, ingen data ud
  │        ▼ kun hvis borgeren selv vælger det    │  ✗ Ingen tredjeparter
  │   gemt fil (krypteret) / udskrift / eksport   │  ✗ Ingen AI-tjenester
  └───────────────────────────────────────────────┘
```

- **Beregningen** kører i en Web Worker med Pyodide (Python kompileret til WebAssembly). Pyodide og alle
  Python-pakker hentes fra sidens egen adresse (`./pyodide/`, `./py/`). Der er ingen CDN eller anden
  server ved kørsel.
- **Kommunikationen** mellem siden og workeren er `postMessage` i samme browserfane. Den forlader ikke
  computeren.
- **PDF-filen** læses af browseren som bytes (`ArrayBuffer`) og gives direkte til workeren. Den uploades
  ingen steder, selv om guiden kalder det "upload".
- **Intet skrives til disk**: PDF-aflæsningen arbejder i hukommelsen (`io.BytesIO`). Python-koden har
  ingen filskrivning, ingen logning af data og ingen `print` (kontrolleret ved gennemgangen).
- **Når fanen lukkes**, er alt væk. Afbrydes en beregning ("Afbryd"), genstartes workeren, og dens
  hukommelse frigives.

### 2.3 Hvad der sendes over netværket

Kun det, enhver hjemmeside henter: **`GET`-forespørgsler efter sidens egne, statiske filer**, uden
indhold fra borgeren.

| Gennemgået | Resultat |
|---|---|
| JavaScript (`app.js`, `worker.js`) | Eneste netværkskald er `fetch` af sidens egen `py/manifest.json`. Ingen `XMLHttpRequest`, `sendBeacon`, WebSocket, `EventSource` eller dynamisk import fra andre adresser |
| Python (`src/`) | Ingen import af `urllib`, `http`, `socket`, `ssl`, `requests`, `pyodide.http` eller `js`. Kun standardbiblioteket, egne pakker og PDF-læseren er tilladt (`tests/kontrakt/test_browserpakker.py`) |
| HTML (`index.html`) | Kun lokale scripts (`app.js`, `chart.umd.min.js`) og et indlejret ikon. Ingen skrifttyper, billeder, analyse- eller sporingsværktøjer fra andre domæner. Ingen cookies |
| AI | Ingen AI-klienter, -afhængigheder eller -værter (`tests/kontrakt/test_ingen_ai.py`) |
| Content-Security-Policy | Siden har en CSP (`<meta>` i `index.html`): `default-src 'self'`, `connect-src 'self'`, `img-src 'self' data: blob:`, `font-src 'self'`, `object-src 'none'`, `form-action 'none'`, `base-uri 'none'`. Browseren blokerer selv enhver forbindelse fra siden til andre domæner. Inline style er tilladt (style-attributter), men CSS kan ikke hente noget udefra |

**Kontrolleret i browseren**: Browsertesten `test_pyodide.py` kører et helt forløb i Chromium: rapporten
lægges ind, guiden udfyldes, resultatet vises, og en ordning flyttes. Testen registrerer alle
forespørgsler, også fra workeren, og kræver,

- at alle er `GET` til sidens egen adresse uden indhold,
- at der ikke sker en eneste forespørgsel, efter rapporten er læst.

Testen kører før hver udgivelse (afsnit 12.3).

**CSP i browseren**: `tests/browser/test_csp.py` kræver, at politikken findes med de nævnte direktiver, at
et forsøg på at sende data til et andet domæne (`fetch` og billede) blokeres af browseren, og at et helt
forløb (rapport, guide, resultat, bedste plan og metodesiden) ikke giver en eneste overtrædelse.

### 2.4 Hvad andre kan se

- **GitHub** (hosting) ser det samme som ved ethvert besøg på en hjemmeside: IP-adresse, browser og
  hvilke statiske filer der hentes, hvornår. GitHub ser ingen rapport, ingen indtastninger og ingen
  resultater, fordi de aldrig sendes.
- **Pensionsselskaber, PensionsInfo, myndigheder og AI-tjenester** modtager intet fra løsningen.
- **Udvikleren** modtager intet. Der er ingen fejlrapportering, telemetri eller logning til en server.
  Fejl vises kun på borgerens skærm.

### 2.5 Det, borgeren selv kan vælge at gemme

| Funktion | Hvad sker der | Beskyttelse |
|---|---|---|
| **Gem til senere** | En fil hentes ned på borgerens computer | Krypteret i browseren: nøgle med PBKDF2-SHA-256 af borgerens adgangskode (mindst 8 tegn), 600.000 iterationer og tilfældigt salt på 16 byte. AES-GCM med tilfældig IV på 12 byte. Indhold: guidens felter, ordninger, forsikringer, fordelingen over tid og partnerens antagelser (`gemData()`). Uden adgangskoden kan filen ikke læses |
| **Åbn gemt fil** | Filen læses og dekrypteres i browseren | Sendes ingen steder |
| **Udskriv** og **eksport** (JSON/CSV) | Browserens udskrift eller en fil hentet ned lokalt | Ukrypteret. Borgeren vælger selv |
| **Præferencer** | `localStorage`: forklaringsniveau og dagens/årets kroner | Ingen persondata |

### 2.6 Leverancekæden

- **Låste versioner**: Pyodide og alle Python-pakker er låst til version og SHA-256 i
  [`scripts/pyodide_laas.toml`](../scripts/pyodide_laas.toml). `scripts/byg_side.py` henter dem ved
  build og fejler ved enhver afvigelse. Der hentes kun ved build, aldrig når borgeren bruger siden.
- **Afhængigheder**: Koden i `src/` må kun bruge standardbiblioteket, egne pakker og PDF-læseren
  (pdfplumber, pdfminer og dens krav, cryptography). En ny afhængighed kræver en ændring i låsefilen
  med SHA-256.
- **Udgivelse**: GitHub Actions bygger og udgiver først, når alle tests, også browsertestene, er
  grønne.

### 2.7 Persondata i kildekoden

- Rigtige rapporter må aldrig committes. Testene bruger syntetiske rapporter.
- En lokal test mod en rigtig rapport (`PENSIONSINFO_RAPPORT=<sti> uv run pytest -k rigtig`) læser
  filen fra disk uden at gemme noget.
- `scripts/scan_historik.py` gennemsøger hele git-historikken for CPR-numre og hemmeligheder og, med
  `--rapport`, for netop de værdier, en given rapport indeholder (navn, CPR, aftale- og depotnumre). Den
  viser kun, hvor fund er, aldrig værdierne, og køres før push til det offentlige repository.
- Den tidligere løsning (`legacy/`) sendte rapporttekst med navn og CPR til en AI-tjeneste og gemte
  udtræk på disk. Begge dele er fjernet (domænegrundlaget afsnit 7, A13).

### 2.8 Grænser og anbefalinger

- **Borgerens egen computer** er uden for løsningens kontrol: browserudvidelser, delt computer,
  skærmdeling og browserens egen hukommelse. En gemt, ukrypteret eksport ligger, hvor borgeren lægger
  den.
- **CSP dækker siden, ikke workeren**: GitHub Pages kan ikke sætte HTTP-headere, så politikken står i et
  `<meta>`-tag. Det gælder siden. En worker, der hentes fra en fil, får sin politik fra filens egne headere
  og er derfor ikke omfattet. Workerens kode (Python og `worker.js`) er dækket af kodegennemgangen i 2.3 og
  af netværkstesten. Fuld dækning kræver en hosting, der kan sætte headere.
- **Hosting**: GitHub Pages' egne adgangslogs er GitHubs (afsnit 2.4).

---

## 3. Indlæsning af PensionsInfo-rapporten

Borgeren henter sin rapport som PDF fra pensionsinfo.dk og lægger den ind i guiden. Indlæsningen er en
**lokal, deterministisk parser** uden AI. Den læser tekst og placering på siderne med pdfplumber
(`src/pensionsoverblik/pdfimport/`).

**Alt, der læses, vises i guiden, før der regnes.** Borgeren kan se, rette og slette hver ordning. Hvert
felt, parseren har skønnet eller ikke fundet, har en synlig bemærkning ("usikkerhed") ved ordningen.

### 3.1 Modtagelse og forside (`app.pdf`, `tekst.py`)

1. **Størrelse**: højst 25 MB (`MAKS_PDF_BYTES`).
2. **Format**: filen skal begynde med `%PDF-`. Ellers afvises den.
3. **Tekstlag**: forsiden skal have tekst. En scannet PDF uden tekst afvises med en forklaring.
4. **Fødselsdato** (`foedselsdato_fra_rapport`): kun fra forsiden.
   - Er der et fuldt CPR-nummer med bindestreg (DDMMÅÅ-NNNN), bruges det. Århundredet afgøres af 7.
     ciffer efter CPR-kontorets regel (`cpr_foedselsdato`).
   - Ellers bruges PensionsInfos maskerede form (DDMMÅÅ-xxxx) og udskriftsåret ("Udskrevet: …"). Der
     vælges det århundrede, der giver en alder mellem 0 og 110 år i udskriftsåret.
   - Kun formen med bindestreg og kun forsiden bruges, fordi rapporten indeholder 10-cifrede aftale- og
     depotnumre, der ellers kunne forveksles med et CPR-nummer.
   - **Kun fødselsdatoen bruges videre.** CPR-nummeret og navnet gemmes ikke og sendes ingen steder.
     Navnet læses ikke.

### 3.2 Find sektionerne (`pensionsinfo.py`, `_relevante_sider`)

Parseren bruger tre sektioner til pensionerne og fire til forsikringerne. Siderne findes i
indholdsfortegnelsen (side 2–3). Er den der ikke, eller passer sidetallene ikke, gennemløbes siderne,
til sektionerne er fundet.

| Sektion i rapporten | Bruges til |
|---|---|
| "Dine aftaler" | Saldo og årlig indbetaling pr. aftale, og om aftalen kun er forsikring |
| "Hvis du går på pension som X-årig får du" (tabellen) | Ordningerne: produkt, skat, udbetalingsform og -periode |
| "Pension - flere oplysninger" | Tidligste og aftalte udbetalingsalder, saldo og indbetaling pr. produkt |
| Død, tab af arbejdsevne, kritisk sygdom, sundhed | Forsikringerne (afsnit 3.7) |

### 3.3 "Dine aftaler" (`_dine_aftaler`)

Pr. aftale (en række pr. aftalenummer):

| Felt | Hvordan |
|---|---|
| Aftalenummer | Tekst i kolonnen "Aftalenr." (cifre, evt. med mellemrum). ATP har ikke et nummer og springes over |
| Årlig indbetaling | Beløbet nærmest kolonnen "Årlig indbetaling" (højrestillet) |
| Opsparing (saldo) | Beløbet nærmest kolonnen "Opsparing" |
| Kun forsikring | "Kun forsikring" et sted i rækken (under "Opsparing" eller i "Bemærkninger") |

Rapportens indbetaling er **før** arbejdsmarkedsbidrag (AM-bidrag).

### 3.4 Udbetalingstabellen (`_udbetalingstabel`)

Rapporten viser et eller flere scenarier ("Hvis du går på pension som 60-årig …"). **Kun det første
(laveste) scenarie bruges.** Rækkerne står i grupper: Folkepension, "På én gang", "Om året i en årrække"
og "Om året, så længe du lever". Pr. produkt læses:

| Felt | Hvordan |
|---|---|
| Skattekode | S (skattepligtig), A (afgiftspligtig) eller F (skatte- og afgiftsfri) foran selskabet |
| Selskab | Teksten efter skattekoden |
| Beløb pr. aldersperiode | Fx "60 år", "61-69 år", "Fra 70 år" (selskabets egen prognose, før skat) |
| Aftalenummer | Linjen under selskabet |
| Produkttype | Fx "Ratepension", "Livsvarig pension", "Kapitalpension", "Aldersopsparing" |
| Udbetalingsperiode | "Udbetales i N år" |

Produktets **kategori** (ratepension, livsvarig, aldersopsparing, kapitalpension) afgøres af
produkttypen og ellers af gruppen (`_kategori`).

**ATP** er det første beløb over 0 i ATP's række. **Folkepensionen** læses ikke. Den beregnes af
kernen efter loven (afsnit 6).

### 3.5 "Pension - flere oplysninger" (`_flere_oplysninger`)

Pr. produkt (selskab, aftalenummer og type i venstre kolonne):

| Felt | Tekst i rapporten |
|---|---|
| Tidligste udbetalingsalder | "Pensionen kan tidligst udbetales fra/ved N år" |
| Aftalt udbetalingsalder | "Det er aftalt, at pensionen kommer til udbetaling fra/ved N år" |
| Saldo pr. produkt | "… udgør opsparingen X kr." (ikke alle selskaber oplyser den) |
| Indbetaling pr. produkt | "… årlig indbetaling til pensionen på X kr." eller "Der indbetales ikke" (= 0) |

Sektionen beriger kun. Kan den ikke læses, fortsætter importen med en bemærkning.

### 3.6 Sammenstilling (`PensionsInfoAflaeser.aflaes`, `_fordel`)

1. Produkterne fra tabellen kobles til "flere oplysninger" på aftalenummer og type.
2. **Saldo og indbetaling pr. produkt** under samme aftale:
   - Oplyser rapporten både saldo og indbetaling for alle produkter, bruges de.
   - Oplyser den kun saldoen for alle, bruges den. Indbetalingen fordeles efter reglen i punkt 4.
   - Ellers fordeles aftalens saldo **skønsmæssigt** efter nutidsværdien af hvert produkts
     udbetalingsprognose: engangsbeløb med beløbet, rater som annuitet over perioden og livsvarige over
     25 år, alle med en fast rente på 4 % (`FORDELING_RENTE`, `FORDELING_LIVSVARIG_AAR`). Det er et
     fordelingsskøn fra den tidligere løsning, uafhængigt af borgerens egne antagelser. Produktet får
     bemærkningen "Aftalens saldo er fordelt skønsmæssigt … tjek beløbet hos selskabet".
   - Med kun ét produkt får det aftalens saldo og indbetaling direkte.
3. **Indbetalingen omregnes til beløbet efter AM-bidrag** (× (1 − `skat.am_bidrag`)), fordi kernen
   regner med indbetalingen efter AM-bidrag. Produktet får en bemærkning om omregningen.
4. **Skønnet fordeling af indbetalingen** (når den ikke er oplyst pr. produkt): først ratepension op til
   ratepensionens indbetalingsloft (`ordning.ratepension.indbetalingsloft`), resten til livsvarig.
   Aldersopsparing og kapitalpension får 0.
5. **En aftale med saldo, men uden prognose** i tabellen, bliver en ordning af ukendt type med
   bemærkningen "Aftalen har en opsparing, men ingen udbetalingsprognose i rapporten". En aftale, der kun
   er forsikring, springes over.
6. Kapitalpension med skattekoden F (afgiften er betalt, fx ved omlægning 2013–2014) markeres som
   afgiftsberigtiget.

**Fejltolerance** (rettet i PR #39, 2026-11-23): Kun udbetalingstabellen er uundværlig. Kan "Dine
aftaler", "flere oplysninger" eller forsikringerne ikke læses, fortsætter importen med en bemærkning, og
borgeren udfylder det manglende. En uventet fejl giver beskeden "Rapporten kunne ikke læses", og
borgeren kan indtaste selv. Afvigende layout giver aldrig forkerte tal uden bemærkning: parseren læser
kun tekst, den genkender.

### 3.7 Forsikringer (`daekninger.py`)

Fra sektionerne om død, tab af arbejdsevne, visse kritiske sygdomme og sundhed (også børnedækninger)
læses pr. dækning: type, selskab, aftalenummer, skattekode (A/F/S), modtager (ved død), form (på én
gang, om året i en årrække, livsvarigt), beløb, ophørsalder og præmiefritagelse. Et afsnit, der ikke kan
læses, giver en bemærkning og ingen dækninger.

**Forsikringerne indgår ikke i beregningen af det faste beløb.** De vises for sig med beløb efter skat
(afsnit 10.4).

### 3.8 Fra aflæsning til guiden (`omsaet.py`, `til_guide`)

Pr. ordning udfyldes guidens felter, med en usikkerhed, hver gang noget er skønnet:

| Guidens felt | Fra rapporten |
|---|---|
| Type | Kategorien. Ukendt type bliver livsvarig med bemærkningen "Vi har gættet på livsvarig pension – tjek det" |
| Saldo | Afsnit 3.6. Mangler den: bemærkning |
| Årlig indbetaling | Afsnit 3.6, efter AM-bidrag |
| Startalder | Den aftalte udbetalingsalder, ellers den tidligste (med bemærkning) |
| Udbetalingsperiode (ratepension) | Summen af årene i prognosens perioder. Kan den ikke aflæses, eller er den uden for lovens grænser, bruges registrets minimum (med bemærkning) |
| Oprettelsesperiode | Udledt af den tidligste udbetalingsalder efter registrets regler (før 2007, 2007–2017, fra 2018) |
| Tidligste udbetalingsalder | Selskabets oplysning. Den har forrang for lovens regel (afsnit 4.3) |
| Afgift betalt | Kapitalpension med skattekode F |
| Fra lønnen | Ordninger med indbetaling (ikke kapitalpension) får pension fra lønsedlen (017c) |

Desuden: fødselsdatoen, ATP pr. år og rapportens samlede indbetaling pr. måned **før** AM-bidrag (et tjek
af lønsedlens procenter i guiden).

### 3.9 Det, der ikke læses

Navn, CPR-nummer (kun fødselsdatoen udledes), folkepensionens rækker, investeringsform,
garantier, omkostninger og selskabets prognoser ud over brugen i afsnit 3.6. Selskabets egne
udbetalingsbeløb bruges kun til at fordele saldoen og som udbetalingsperiode. Selve udbetalingerne
beregner kernen.

---

## 4. Borgerens input og oversættelsen til kernen

### 4.1 Guidens felter

Guiden har fem trin. Alt kan også rettes i datapanelet ved resultatet.

| Trin | Felter |
|---|---|
| 1. Om dig | Fødselsdato, civilstand (enlig, gift, samlevende), kommune, medlem af folkekirken, løn (bruttoløn pr. måned, egen og firmaets pension i procent), stopalder, evt. deltidsløn |
| 2. Dine ordninger | Pr. ordning: type, saldo, årlig indbetaling, startalder, periode (ratepension), oprettelsesperiode, udbetalingsform (kapitalpension), afgift betalt, i buffer eller direkte (engangsbeløb). ATP pr. år |
| 3. Din partner | Fuld profil (samme felter) eller et overslag (fødselsdato og anden indkomst) |
| 4. Opsparing | Bank, frit depot (med gevinst), aktiesparekonto, løbende indskud, om opsparingen bruges i planen |
| 5. Forventninger | Valgfrit: egne forventninger til afkast efter PAL-skat og inflation (ellers branchestandarden, afsnit 8). Opsættelse af folkepension |

### 4.2 Oversættelse (`oversaet.py`)

`til_kerne` laver guidens JSON om til kernens datamodel (`Pensionsprofil`, `Ordning`, `Aktiv`, `Loen`,
`Partner`, `Antagelser` i `model.py`). `til_husstand` gør det samme for en partner med fuld profil:
partneren får sin egen profil og sine egne antagelser for afkast, grundlag og fordeling over tid (037).
Kommune og inflation er husstandens.

### 4.3 Validering (`validering.py`)

Kernen afviser ugyldigt input med feltets navn og en dansk besked, som vises ved feltet. Blandt andet:

- satsåret skal findes i registret,
- fødselsdatoen skal ligge før beregningsdatoen og ikke før den første årgang, registret har en
  folkepensionsalder for (personer født før 1.7.1955 afvises, domænegrundlaget A10),
- civilstand og partner skal passe sammen, og kommunen skal findes i registret,
- beløb må ikke være negative, og ordnings-id'er skal være unikke,
- **startalderen må ikke være før den tidligste lovlige udbetalingsalder**. Den afhænger af
  oprettelsesdatoen (PBL § 1 A; aftaler fra 2018: folkepensionsalderen − 3; 2007–2017: − 5; før 2007:
  60 år). Er datoen ukendt, bruges den mest restriktive regel, og der gives en advarsel i stedet for en
  afvisning. Oplyser selskabet alderen (PensionsInfo), har den forrang,
- ratepension: mindst registrets minimum af år, og sidste rate senest det tilladte år efter
  udbetalingsalderen,
- kapitalpension: udbetalingsform, portioner (mindst 2, senest registrets frist) og ingen omlægning, når
  afgiften er betalt,
- fordelingen over tid: hvert bånd 0–150 %, mindst ét over 0.

---

## 5. Regelregistret og sporbarhed

### 5.1 Indhold

Registret (`src/pensionskerne/register/`) er **det eneste sted, satser findes**:

| Fil | Indhold |
|---|---|
| `2026.toml` | 85 poster: skat (25), folkepension (14), personlig tillægsprocent (5), ældre- og mediecheck (4), ordninger (11), opsat pension (3), ATP, PAL, aktiesparekonto, forsikringsafgift, Rådet for Afkastforventninger (15) og branchestandarden (3) |
| `kommuner_2026.toml` | Kommune- og kirkeskat for 98 kommuner (Skatteministeriet, kommuneskattesatser_2026.xlsx) |
| `forenklinger.toml` | 19 forenklinger med titel, beskrivelse, begrundelse, betydning og kilde (afsnit 13) |

Hver post har `id`, `vaerdi`, `enhed`, `kilde` (lov og paragraf eller officiel kilde), `status` og
`reguleres`:

- **status** `verificeret` (80 poster): værdien er holdt op mod primærkilden.
  `sekundaer` (5 poster): kilden er sekundær eller en antagelse. Det gælder
  `forsikring.afgift`, `ordning.udbetalingsalder.foer_2007`, `raadet.lang.tilknytning`,
  `branchestandard.standardprofil` og `branchestandard.blanding`. Ingen poster er `uverificeret`.
- **reguleres = true**: beløbet satsreguleres i fremtidige år (afsnit 6.1).

Domænegrundlaget ([`beregningskerne.md`](domaene/beregningskerne.md) afsnit 2) gennemgår reglerne og
2026-værdierne mod lovgivningen.

### 5.2 Opslag og sporing (`register/opslag.py`)

Al adgang går gennem `Regelopslag`, den eneste vej fra beregningen ind i registret:

- `o.v(id)` giver værdien for kalenderåret. Er posten et beløb, der reguleres, ganges med
  reguleringsfaktoren (1 + satsregulering)^(kalenderår − satsår).
- Hvert opslag noteres i årets **sporing** (`Aarsresultat.sporing`), og hver antagelse, der bruges
  (`o.antagelse`), noteres også. Resultatet har den samlede sporing (`Fremskrivning.sporing_samlet`).
- Poster, der ikke er verificerede, sætter automatisk et **flag** på året. I streng tilstand
  (`streng=True`) afvises de.
- Hver forenkling, beregningen gør brug af i et år, markeres (`o.marker("forenkling:<id>")`) og vises
  ved resultatet.

### 5.3 Test af registret

- `tests/register/test_ingen_litteraler.py`: ingen tal i `regler/`.
- `tests/register/test_forenklinger.py`: hver markering i kernen står i forenklingsregistret, og hver
  markeret forenkling bruges.
- `tests/register/test_opslag.py`, `test_indlaesning.py`, `test_kommunenavne.py`, `test_raadet.py`:
  registrets format, regulering, kommunenavne og Rådets forudsætninger.

---

## 6. Beregningsmotoren år for år

Hovedfunktionen er `beregn` i [`fremskrivning.py`](../src/pensionskerne/fremskrivning.py). Den regner
én person. Et par regnes som to personer, der påvirker hinanden (afsnit 7).

### 6.1 Grundlag

- **Tid**: Beregningen går **kalenderår for kalenderår** fra første relevante år til planens slutning.
  Alderen i et år er kalenderåret minus fødselsåret.
- **Beløb** regnes **nominelt** i årets kroner og omregnes til **dagens kroner** med årets realfaktor
  1 / (1 + inflation)^(kalenderår − beregningsår).
- **Satsregulering**: Beløbsgrænser og satser, der reguleres (fx personfradrag, skattegrænser,
  folkepension), fremskrives med satsreguleringen. Den er som standard lig inflationen
  (`Antagelser.satsregulering = None`).
- **Afkast** er borgerens antagelse **efter PAL-skat** (eller branchestandardens, afsnit 8). PAL indgår
  derfor ikke selv i pensionernes afkast.
- **Folkepensionsalder** efter fødselsdato fra registret (`fp.folkepensionsalder`, lov om social pension
  § 1 a).
- **Stopalder** (feature 017 og 030): med løn den valgte stopalder (ellers folkepensionsalderen). Uden
  valgt stopalder følger den første udbetaling.
- **Tabellen** begynder i dag med løn, ellers ved første udbetaling eller folkepensionsalderen, og slutter
  ved det seneste af planens slutning (standard 90 år, `livsvarig_horisont_alder`), folkepensionens start
  og sidste rate.

### 6.2 Opsparingsfasen (frem til hver ordnings start)

Pr. år og ordning (`fremskrivning.py`, afsnit 1):

1. **Indbetaling** = den oplyste årlige indbetaling (efter AM-bidrag) × reguleringsfaktor ×
   (1 + realvækst)^år. Den er i dagens kroner og følger lønnen (017b). Med løn stopper indbetalingerne ved
   stopalderen.
2. **Lønsedlen** (017c): oplyser borgeren bruttoløn og pensionsprocenter, bliver indbetalingen
   brutto × (eget + firma) × (1 − AM-sats). Den fordeles på ordningerne med pension fra lønnen efter deres
   egne beløb (ligeligt, hvis de er 0).
3. **Lofter** (PBL § 16): aldersopsparing højst `ordning.aldersopsparing.indbetalingsloft` (det forhøjede
   loft de sidste år før folkepensionsalderen). Ratepension højst `ordning.ratepension.indbetalingsloft`.
   Det overskydende regnes som indbetaling til en livsvarig pension med advarslen `RATEPENSION_LOFT`.
4. **Saldo** ved årets slutning = saldo × (1 + afkast) + indbetaling − gebyr. Saldoen bliver ikke
   negativ. Kernen kan trække et fast gebyr pr. år, men det sættes aldrig og er 0 (se M4 i afsnit 13.3).

### 6.3 Udbetalingsplaner (pr. ordning)

| Ordning | Udbetaling | Hjemmel / note |
|---|---|---|
| Ratepension | Årsrate = værdien primo / resterende år. Raten betales primo, restværdien forrentes resten af året (`rateplan`). Periode: den valgte, ellers registrets minimum | PBL § 11 A, stk. 2, nr. 1 (domænegrundlaget A9) |
| Livsvarig pension | Konstant årlig ydelse, der netop opbruger saldoen over horisonten max(`livsvarig_min_aar`, 90 − startalder) med afkastet (forudbetalt annuitet, `livsvarig_ydelse`) | Antagelse, ikke lov. Selskabet fastsætter den faktiske ydelse |
| Aldersopsparing | Engangsbeløb, skattefrit | PBL |
| Kapitalpension, engangsbeløb | Saldo × (1 − afgift), skattefri, hvis afgiften er betalt | PBL § 25, stk. 1, nr. 1 (`ordning.kapitalpension.afgift`) |
| Kapitalpension i portioner | Som ratepensionens rater af restværdien, hver portion efter afgift. Advarsel `PORTIONER_KRAEVER_AFTALE` | PBL § 26 |
| Kapitalpension omlagt | Regnes som ratepension eller livsvarig. Advarsel `OMLAEGNING_KRAEVER_OVERFOERSEL` | PBL § 41 |

Engangsbeløb kan sættes "i buffer" (standard) eller "direkte". I bufferen bruges de til den faste
udbetaling (afsnit 6.6).

### 6.4 Rækkefølgen i et år

Pr. kalenderår i `aar_for_aar` (`fremskrivning.py:478`):

**1. Private udbetalinger**: årets rater, livsvarige ydelser og engangsbeløb (netto).

**2. ATP** fra folkepensionsalderen: oplyst beløb × reguleringsfaktor, ellers registrets gennemsnit
(`atp.fallback`, advarsel `ATP_SKOENNET`). ATP påvirkes ikke af opsat folkepension. I det år,
folkepensionsalderen nås, udbetales den fra måneden efter fødselsdagen (andel (12 − fødselsmåned) / 12).

**3. Løn** (017): AM-bidrag af hele lønnen (`skat.am_bidrag`, AMBL § 1). Indbetaling til rate- og livsvarig
pension fradrages i den personlige indkomst (regnet som arbejdsgiverordning, forenkling).
Beskæftigelses-, job- og seniorfradrag (LL §§ 9 J og 9 K) er ligningsmæssige fradrag og nedsætter kun
grundlaget for kommune- og kirkeskat.

**4. Indtægtsgrundlaget** (lov om social pension § 29, `indtaegtsgrundlag`):
skattepligtige private pensionsudbetalinger + ATP + kapitalindkomst (bufferens og opsparingens afkast og
anden kapitalindkomst) + aktieindkomst + partnerens øvrige indkomst. Partnerens indkomst tæller fuldt, hvis
partneren er pensionist, ellers med registrets andel (`fp.partner_ikke_pensionist.medregnet_andel`, § 29,
stk. 5). Egen løn og aldersopsparing indgår ikke. Grundlaget afrundes nedad til hele hundreder (§ 29,
stk. 6).

**5. Folkepension** fra folkepensionsalderen plus en evt. opsættelse:
- **Grundbeløb** (`fp.grundbeloeb`), uafhængigt af indkomst.
- **Pensionstillæg** = ydelse − aftrapningssats × max(0, grundlag − fradrag), dog mindst 0. Der er tre
  regler: enlig, gift/samlevende med pensionist-partner og gift/samlevende med partner, der ikke er
  pensionist. Den vælges år for år efter partnerens status.
- **Midlertidig forhøjelse af fradraget** (§ 49 c): aftrappes lineært til 0 i registrets nul-år
  (domænegrundlaget A12).
- **Ventetillæg** ved opsættelse: begge ganges med 1 + venteprocent, hvor venteprocent = opsatte måneder
  / middellevetid i måneder ved ophøret (registrets officielle tabel), afrundet (§ 15 a ff.; BEK 930/2018
  § 8). Advarslerne `750_TIMER` og `OPSAT_ANDRE_FORMER` gives.
- Første år udbetales fra måneden efter fødselsdagen, som ATP.

**6. Personlig tillægsprocent** (§ 14 a): 100 op til bundgrænsen (+ forhøjelsen), derefter 1 point mindre
pr. fuldt trin (`tillaegsprocent`). Grundlaget er indtægtsgrundlaget plus egen løn over bundfradraget
(`tp.arbejdsindkomst.bundfradrag`). Den er en selvstændig regel og afledes ikke af pensionstillægget
(golden case G-42).

**7. Ældrecheck og mediecheck** fra året efter folkepensionens start (kræver folkepension pr. 1. januar):
- ældrecheck = sats × tillægsprocent / 100. Den bortfalder helt, hvis husstandens likvide formue pr.
  1. januar er over formuegrænsen (§ 72 d), og udbetales ikke under registrets minimum,
- mediecheck kræver tillægsprocent 100 og er uafhængig af formue,
- begge er skattepligtige (domænegrundlaget A3).

**8. Skat** (personskatteloven, `regler/skat.py`):
- Personlig indkomst (PI) = summen af alle skattepligtige kilder. **Pensionsudbetalinger og offentlige
  ydelser har intet AM-bidrag** (domænegrundlaget A1).
- Bundskat af PI + kapitalindkomst. Kommune- og kirkeskat (kommunens satser) af samme grundlag minus de
  ligningsmæssige fradrag. Personfradraget regnes for hvert grundlag for sig.
- Mellem-, top- og top-topskat: hvert trin rammer alt grundlag over sin grænse. Kapitalindkomst indgår her
  kun over bundfradraget (§ 7, stk. 1) og lægges øverst.
- **Skrå skatteloft** (§ 19): overstiger bundskat + kommuneskat + samlet trinsats loftet, nedsættes
  trinsatsen med det overskydende, for kapitalindkomst med dens eget loft (§ 19, stk. 2). Kirkeskat indgår
  ikke i loftet.
- **Ægtefæller** (kun gifte): den andens uudnyttede personfradrag nedsætter skatten (§ 10, stk. 3), og et
  uudnyttet bundfradrag for kapitalindkomst lægges til (§ 7, stk. 5).
- **Aktieindkomst** (gevinst ved salg fra frit depot): 27 %/42 % efter progressionsgrænsen (§ 8 a), for
  gifte med ægtefællens uudnyttede grænse (stk. 4). Personfradraget bruges ikke.
- **Aktiesparekonto**: lagerbeskatning af afkastet med registrets sats.
- Skatten af kapitalindkomsten er **merskatten** ved at lægge den oven på PI. Den betales af bufferen.
- Den samlede skat af PI **fordeles forholdsmæssigt** på kilderne, så hver kilde kan vises med netto. Det
  er en præsentationskonvention. Loven beskatter den samlede indkomst (forenkling
  `skat_fordelt_paa_kilder`).

**9. Årets resultat** (`Aarsresultat`): kilder brutto, skat og netto, PI, indtægtsgrundlag,
tillægsprocent, netto i alt (nominelt og i dagens kroner), skat pr. type, AM-bidrag, fradrag, formue pr.
1. januar, sporing og flag. **Disponibel** = netto i alt − skat af opsparing (kapital-, aktie- og
ASK-skat) − indskud på opsparing. Det er det, udjævningen fordeler.

### 6.5 Opsparing uden for pension (013 og 013b)

Borgerens bank, frie depot og aktiesparekonto forrentes med pensionens afkast **før** PAL-skat:
rente = afkast efter PAL / (1 − PAL-sats). Opsparingen er delt i tre skattekasser:

| Lag | Skat | Før første udbetaling |
|---|---|---|
| Bank | Afkastet er kapitalindkomst | Vokser brutto. Skatten betales af lønnen (forenkling `opsparing_skat_foer_udbetaling`) |
| Frit depot | Gevinsten ved salg er aktieindkomst, forholdsmæssigt af anskaffelsessummen | Vokser uden skat (der sælges ikke). Gevinst i dag: oplyst, ellers halvdelen af værdien (`depot_urealiseret_andel`) |
| Aktiesparekonto | Lagerbeskatning | Vokser efter lagerskat |

Opsparing **i planen** indsættes i bufferen ved første udbetalingsår (med løn: ved stopalderen) og bruges
af udjævningen. **Urørt** opsparing vokser videre, og skatten af dens afkast betales af den løbende
udbetaling. Løbende indskud gælder kun med løn, frem til stopalderen. Indskud på aktiesparekontoen over
loftet står i frit depot (advarsel `ASK_OVER_LOFT`). Al opsparing tæller i husstandens likvide formue
(§ 72 d, stk. 2).

### 6.6 Den faste udbetaling og bufferen (udjævning, `jaevn.py`)

Rå nettoudbetalinger svinger fra år til år (engangsbeløb, rater, der stopper, folkepension, der begynder).
Løsningen viser i stedet det **højeste forløb, der er konstant i dagens købekraft, aldrig låner af senere
år og kun stiger, når der kommer flere penge** (feature 010). Det er en præsentationsmodel, ikke en
lovregel.

**Bufferen** er opsparing uden for pension: engangsbeløb, opsparing i planen og det, der spares op i år med
høje udbetalinger. Den forrentes med renten før skat, og skatten af afkastet regnes i årets skat (6.4).

**Algoritmen** (forbrugsudjævning med likviditetsbegrænsning, segment for segment). Fra år *i* med buffer
*B* er niveauet

```
c = min over k ≥ i af  ( B + Σ_{t=i..k} I_t / (1+r)^(t−i) )  /  ( Σ_{t=i..k} w_t · g^(t−i) / (1+r)^(t−i) )
```

hvor *I_t* er årets indbetaling til bufferen (disponibel + engangsbeløb i bufferen), *g* = 1 + inflation,
*r* årets rente og *w_t* fordelingens vægt (1 uden fordeling). Niveauet i år *t* er *c · w_t · g^(t−i)*.
Segmentet varer til og med det sidste *k*, der giver minimum. Her er bufferen netop brugt op, og næste
segment begynder. Det sikrer, at

- **bufferen aldrig er negativ** (der lånes aldrig af senere år),
- niveauet ikke falder i dagens kroner (i forhold til fordelingen),
- bufferen ender i 0.

Betalinger sker primo året. Med løn udjævnes kun årene fra stopalderen. Arbejdsårene vises med årets
nettoindkomst, og engangsbeløb før stopalderen samles i bufferen og forrentes til stopalderen.

**Fordelingen over tid** (equalizer, 033/033b/037): borgeren kan sætte hvert bånd på fem år fra sin
stopalder (et sidste bånd fra 85 år, korte bånd lægges sammen) fra 0 % til 150 % af det faste beløb.
Vægten *w_t* er båndets procent. Hver partner har sin egen fordeling fra sin egen stopalder (037).

**Fastpunkt** (009): bufferens afkast er kapitalindkomst. Den påvirker skat, pensionstillæg og ældrecheck
(formue), som igen påvirker den disponible indkomst og dermed bufferen. Det løses ved iteration:
beregn årene, udjævn, beregn bufferens kapitalindkomst, aktieindkomst, ASK-afkast og formue pr. år, og
gentag. Der stoppes, når ingen års udbetaling ændrer sig mere end **1 kr. om måneden**
(`BUFFER_TOLERANCE_KR`), eller når intet år skifter side af ældrechecks formuegrænse. Efter højst 12
iterationer (`BUFFER_MAKS_ITERATIONER`) stoppes med advarslen `BUFFER_IKKE_KONVERGERET`. Beregningen er
deterministisk. Golden cases kræver højst 6 iterationer.

Træk fra bufferen tages i rækkefølgen bank → depot → aktiesparekonto (`traekraekkefoelge`). Et træk fra
depotet realiserer gevinsten forholdsmæssigt.

### 6.7 Hovedtallet (`visning.py`, `_hovedtal`)

**Hovedtallet** er det faste beløb om måneden efter skat i dagens kroner: det **laveste** udjævnede
niveau fra stopalderen (uden løn fra første udbetaling), målt i forhold til fordelingen (beløbet ved
100 %). År på 0 % tæller ikke. Det rundes til nærmeste 100 kr. Stiger niveauet senere (fordi der først
kommer flere penge da), oplyses det som "Fra X år stiger det til ca. Y kr.". Uden udjævning (ingen
udbetalinger) er hovedtallet nettoindkomsten i første hele folkepensionsår.

Med løn vises også lønnen efter skat og pensionsindbetaling pr. måned (gennemsnit før stopalderen) og hvor
mange procent det faste beløb er af den.

### 6.8 Advarsler

Kernen giver advarsler som en del af resultatet (`Advarsel` med kode, besked, aldre og registerposter).
De vises ved hovedtallet ("forudsætninger bag tallet") eller i graf og tidslinje. Eksempler:
`MELLEMSKAT_INTERVAL`, `ATP_SKOENNET`, `UDBETALING_FOER_LOVLIG_ALDER`, `RATEPENSION_LOFT`,
`ALDERSOPSPARING_OVER_LOFT`, `BUFFER_SOM_OPSPARING`, `AKTIEINDKOMST_OVER_GRAENSE`, `INDKOMSTHUL`,
`OPSPARING_FOER_UDBETALING`, `FORBRUGSPROFIL`, `750_TIMER`, `BUFFER_IKKE_KONVERGERET`,
`HUSSTAND_IKKE_KONVERGERET`. Den fulde liste med titler står i `src/pensionsoverblik/katalog.py`.

---

## 7. Par og husstand

Med en partner som fuld profil regner `beregn_husstand` ([`husstand.py`](../src/pensionskerne/husstand.py))
begge personer. De påvirker hinanden efter loven:

| Kobling | Hjemmel |
|---|---|
| Pensionstillæg og tillægsprocent af parrets samlede indtægtsgrundlag. Partnerens AM-pligtige arbejdsindkomst indgår ikke | Lov om social pension § 29 |
| Ældrechecken ser på husstandens samlede likvide formue, også begges buffer og opsparing | § 72 d, stk. 2 |
| Gifte: uudnyttet personfradrag og bundfradrag for kapitalindkomst overføres | PSL § 10, stk. 3, og § 7, stk. 5 |
| Gifte: uudnyttet progressionsgrænse for aktieindkomst | PSL § 8 a, stk. 4 |

Gifte og samlevende behandles ens af ydelserne. Kun gifte får skatteoverførslerne.

**Fastpunkt**: Partneren regnes først uden kendskab til borgeren. Derefter regnes skiftevis borgeren med
partnerens tal og partneren med borgerens, til begges resultater er uændrede, højst 6 runder
(`HUSSTAND_MAKS_ITERATIONER`, ellers advarslen `HUSSTAND_IKKE_KONVERGERET`).

**Hver for sig** (037): hver person har sin egen fordeling over tid, sit eget afkast og sit eget grundlag
(branchestandard eller egne forventninger). Inflationen er husstandens, så dagens kroner betyder det samme
for begge, og beløbene kan lægges sammen. Har de forskellige grundlag, er inflationen ikke helt den samme,
fordi branchestandarden har sin egen (afsnit 8). Det står ved hovedtallet.

**Fanen Samlet** viser summen af begges faste beløb pr. kalenderår. Der lægges kun sammen, intet regnes
om.

**Partneren som overslag** (uden fuld profil): partnerens fødselsdato og øvrige indkomst bruges kun i
indtægtsgrundlaget og til tillægsreglen, og partnerens opsparing kun i husstandens formue
(ældrechecken).

---

## 8. Prognose som pensionsselskaberne (branchestandard)

Som udgangspunkt regner løsningen **som pensionsselskaberne**: efter Forsikring & Pensions *Henstilling om
pensionsprognoser* (LP-information 20/20) med Rådet for Afkastforventningers forudsætninger. Borgeren kan
i stedet vælge egne forventninger i guiden eller skifte ved hovedtallet. Henstillingen er en
branchestandard, ikke lov.

Metoden er beskrevet i detaljer i [`docs/branchestandard-metode.md`](branchestandard-metode.md). Kort:

1. **Portefølje pr. ordning**: en blanding af globale aktier og obligationer. Aktieandelen følger
   registrets standardprofil efter år til pension (`branchestandard.standardprofil`, nedtrapning mod
   pensionsalderen). Der skønnes ikke ud fra selskabets prognose (forenkling
   `branchestandard_standardprofil`, M1).
2. **μ og σ** for porteføljen af Rådets forventede afkast, investeringsomkostninger, standardafvigelser og
   korrelationer for år 1–5, 6–10 og 11+. Investeringsomkostningerne trækkes fra afkastet. En fast
   administrationsomkostning i kroner trækkes ikke (forenkling
   `branchestandard_uden_administrationsomkostning`, M4).
3. **Trin 1–2** (`prognose.py`): middelværdi og varians af depotet fremregnes rekursivt (henstillingens
   appendix 1), og 5 %- og 95 %-fraktilerne findes med en log-normal approksimation. Det giver tre
   afkaststier pr. ordning: højt, forventet og lavt. Implementeringen genskaber henstillingens
   taleksempel (bilag 2) med en nøjagtighed på 10⁻⁹ (`tests/golden/test_branchestandard_bilag2.py`).
4. **Trin 3**: stierne omregnes til afkast efter PAL-skat, og den almindelige fremskrivning (afsnit 6) køres
   tre gange med ordningens forløb. Skat, ydelser og udjævning er de samme.
5. **Inflation og regulering**: Rådets langsigtede inflation for hele forløbet (forenkling
   `branchestandard_en_inflation`). Bufferen og opsparing uden for pension følger det forventede afkast
   (forenkling `branchestandard_opsparing_fast_afkast`).

Hovedtallet er udbetalingen ved forventet afkast. Højt og lavt afkast vises som et spænd ved hovedtallet.
Udbetalingen ved lavt afkast er beløbet efter skat, når 5 %-**forløbet** regnes igennem. Det er ikke
5 %-fraktilen af beløbet efter skat, fordi skat og modregning ikke er lineære.

---

## 9. "Find bedste plan" (optimering)

[`optimering.py`](../src/pensionskerne/optimering.py) søger den plan, der giver det **højeste faste
beløb hele perioden**. Det er en søgning over kernens egne, fulde beregninger med skat og modregning
(Princip I). Der er ingen tilfældighed. Samme input giver altid samme forslag.

- **Mål**: det laveste udjævnede beløb fra pensionsalderen (stopalderen med løn, ellers
  folkepensionsalderen) i dagens kroner. Ved lige mål vinder det fladeste forløb.
- **Søgerum**: startalder pr. ordning (fra pensionsalderen, dog tidligst den lovlige alder, til
  folkepensionsalderen plus den maksimale opsættelse), ratepensionens varighed, folkepensionens opsættelse
  og kapitalpensionens form (engangsbeløb, portioner over 2–20 år, omlægning til ratepension over 10–30 år
  eller livrente, ikke når afgiften er betalt). Alle grænser fra registret. En ordning, der allerede
  udbetaler, flyttes ikke. Engangsbeløb udbetalt direkte flyttes ikke.
- **Værn** mod forslag, der ser bedre ud, men er værre at leve af (fra den tidligere løsning): det faste
  beløb mindst 70 % af udgangspunktets, laveste rå udbetaling mindst 97 % af udgangspunktets, ikke flere
  år med lav rå udbetaling (under 85 % af det faste beløb) og regler for bufferen.
- **Søgning**: udtømmende, hvis søgerummet er lille nok, ellers koordinatsøgning fra flere startpunkter,
  højst 1.500 beregninger.
- **I brugerfladen** (036) søges der automatisk efter første beregning, og den bedste plan vises som
  hovedtallet. Borgeren kan skifte til sin egen plan. En statuslinje siger altid, om det viste er den
  bedste plan. Ændres planen, regnes tallene med det samme, men der søges først igen, når borgeren beder om
  det.

---

## 10. Øvrige beregninger

Alle er almindelige kald af kernen med ændret input. Ingen har egne regler.

### 10.1 Usikkerhed (018 og 019)

Tabellen "Hvis afkast, inflation eller levetid bliver anderledes" regner hovedtallet med afkast ±1
procentpoint, inflation ±0,5 procentpoint (hver for sig og sammen, ingen sats under 0) og planens slutning
ved 85 og 95 år i stedet for 90. Livrentens ydelse ændres ikke af levetidsscenarierne, fordi selskabet
fastsætter den. Med branchestandarden vises kun levetiden, fordi branchestandarden har sit eget spænd
(afsnit 8). For et par flyttes partnerens afkast med samme forskel (037).

(Rækkerne "Dårlige år først" og "Gode år først" er fjernet 2026-11-23. De viste kun niveauet de første år,
som gode år ikke kan hæve, fordi udjævningen ikke låner. Afkast pr. år, feature 023a, er bevaret i kernen.)

### 10.2 "Hvornår kan jeg stoppe?" (017)

Kræver løn. Afprøver hver stopalder fra i dag til folkepensionsalderen med den nuværende plan og viser
den tidligste, hvor hovedtallet når det ønskede beløb, ellers den bedste. Alle aldre afprøves.

### 10.3 "Hvor skal næste krone hen?" (021)

Kræver løn. Sammenligner et ekstra årligt beløb fra lønnen til ratepension, aldersopsparing,
aktiesparekonto og opsparing i banken, hver med en fuld beregning. Ratepensionen får beløbet før skat,
de andre det, ratepensionen koster efter skat, så lønnen efter skat falder lige meget. Målet er det faste
beløb **i gennemsnit** fra stopalderen (for et par summen af begges), fordi hovedtallet (minimum) ville
favorisere likvid opsparing.

### 10.4 Forsikringer efter skat (034, `forsikring.py`)

Beløbene er rapportens udbetaling i dag. Skatten afhænger af skattekoden:

| Kode | Behandling |
|---|---|
| F | Skatte- og afgiftsfri. Beløbet vises uændret |
| A | Afgift efter registret (`forsikring.afgift`, status sekundær) |
| S, til borgeren (tab af arbejdsevne) | Regnes som årets eneste personlige indkomst, uden AM-bidrag, med borgerens kommune |
| S, til efterladte | Regnes ikke. Skatten afhænger af modtagerens indkomst, som er ukendt |

Forsikringerne indgår ikke i det faste beløb.

---

## 11. Fra resultat til skærm

[`visning.py`](../src/pensionsoverblik/visning.py) laver kernens resultat om til visningen. Det er **ren
omformatering**: kilder grupperes i kort, årsbeløb divideres med 12, og der ganges med kernens
realfaktor. Der beregnes ingen skat, ydelser eller satser.

- **Afrunding**: hovedtal og månedsbeløb til nærmeste 100 kr. Tabeller viser hele kroner.
- **Dagens eller årets kroner**: grafen kan vise begge. Hovedtallet er altid i dagens kroner.
- **Forklaringer på tre niveauer** (020): hvert tal har en forklaring fra kataloget
  [`forklaringer.toml`](../src/pensionsoverblik/forklaringer.toml), fra kort (niveau 1) til fuld
  metode med paragraffer (niveau 3). Kataloget indeholder kun ord og pladsholdere, aldrig borgerens tal.
  Tallene sættes ind fra beregningen.
- **"Sådan har vi regnet"**: år for år og de satser, der er brugt, med kilde og status.
- **Metodesiden** ("Sådan regner PensionsAnalytikeren"): hele kataloget, alle forenklinger og hele
  registret for satsåret.
- **Eksport** (020d): hele beregningen som JSON og år for år som CSV.

---

## 12. Kvalitetssikring

### 12.1 Udviklingsproces

Hver ændring følger Spec Kit: spec med afklaringer, test først, implementering. Krav, beslutninger og
fund står pr. feature i `specs/NNN-*/`. Afvigelser fra loven og fra den tidligere løsning står i
domænegrundlaget. En ændring af en golden case kræver en begrundelse (Princip IV).

### 12.2 Test

Ca. 1.000 almindelige tests og 187 browsertests (`uv run pytest` og `uv run pytest -m browser`):

| Type | Mappe | Indhold |
|---|---|---|
| Golden cases | `tests/golden/` | Facit-tal pr. regel og forløb (skat, folkepension, ydelser, opsat pension, ordninger, udjævning, buffer, husstand, løn, opsparing, branchestandard, forsikring m.fl.). Fx G-02/G-03 (mellem- og topskat), G-40–G-43 (tillægsprocent og ældrecheck), FP-1 (folkepensionsalder), VT-1 (ventetillæg) |
| Regler | `tests/regler/` | Hver regelfunktion for sig |
| Egenskaber | `tests/egenskaber/` | Invarianter for vilkårligt input: skat mellem 0 og indkomsten, monoton skat og marginalskat under loftet, pensionstillæg aftagende, tillægsprocent heltal 0–100 |
| Differentialtest | `tests/differential/` | Mod den tidligere løsning (`legacy/engine.py`): samme tal, hvor reglen er uændret, og kun de kendte afvigelser (A1) ellers |
| Register | `tests/register/` | Ingen tal i reglerne, forenklingerne, format og regulering |
| Kontrakt | `tests/kontrakt/` | Ingen AI, kun tilladte pakker, inputvalidering |
| App og PDF | `tests/app/` | Oversættelse, visning, PDF-parser på syntetiske rapporter (også med layoutvarianter og fejl) |
| Browser | `tests/browser/` | Den byggede side i Chromium: hele forløb, Pyodide giver samme tal som CPython, intet netværk, tilgængelighed (axe-core, WCAG 2.2 AA) og 360 px bredde |

### 12.3 Udgivelse

GitHub Actions (`.github/workflows/pages.yml`) kører ved hver ændring på `main`: alle almindelige tests,
build af siden, alle browsertests og først derefter udgivelse. Fejler en test, udgives intet.

---

## 13. Forenklinger, begrænsninger og kendte afvigelser

### 13.1 Forenklinger

Forenklingsregistret ([`forenklinger.toml`](../src/pensionskerne/register/forenklinger.toml)) har 19
forenklinger med begrundelse og betydning for resultatet. Seks gælder altid, de øvrige kun i de år,
kernen markerer dem, og de vises ved resultatet. Blandt de vigtigste:

- `skat_fordelt_paa_kilder`: skatten fordeles forholdsmæssigt på kilderne (kun visning, summen er rigtig),
- `afkast_som_kapitalindkomst`: bufferen beskattes som kapitalindkomst (bank og obligationer),
- `ingen_renteudgifter`: negativ kapitalindkomst giver intet fradrag,
- `samme_afkast_hvert_aar`: ét afkast for alle år (med egne forventninger),
- `pensionsindbetaling_som_arbejdsgiverordning` og `pensionsprocent_af_bruttoloen` (løn),
- `partnerens_loen_ukendt` og `partnerindkomst_naermeste_aar` (husstand),
- `kapitalpension_foer_1980`: lavere afgift for kapitalpension oprettet før 1980 er ikke modelleret,
- `aktieafkast_som_kursgevinst` og `ask_indskud_lig_saldo` (opsparing),
- `livsvarig_uden_aarets_afkast`, `branchestandard_en_inflation`,
  `branchestandard_opsparing_fast_afkast`, `branchestandard_standardprofil` og
  `branchestandard_uden_administrationsomkostning` (prognose, de to sidste fra M1 og M4).

### 13.2 Ikke modelleret

- Personer født før 1.7.1955 (afvises).
- Livsvarig pension påbegyndt før folkepensionsalderen (reduceret ydelse). Rapportens tal antages at
  afspejle det.
- Opsat folkepension som forhøjet tillæg i 10 år eller engangsbeløb (kun livsvarigt tillæg).
  750-timers-kravet kontrolleres ikke (der gives en advarsel).
- Aktieudbytte, tab og negativt afkast fremføres ikke.
- Arbejdsindkomst efter folkepensionsalderen ud over en evt. deltidsløn.
- Engangsydelser som engangschecken i 2026.
- Den præcise kontoteknik hos selskaberne (gennemsnitsrente, garantier, bonus). Livrentens ydelse er
  kernens annuitet over horisonten, ikke selskabets.

### 13.3 Kendte afvigelser og fund ved denne gennemgang

| # | Fund | Betydning | Status |
|---|---|---|---|
| M1 | **Aktieandelen kalibreres ikke.** Spec 035 og forklaringen på niveau 3 sagde, at aktieandelen er "et skøn kalibreret mod selskabets prognose". Kernen kan modtage en aktieandel pr. ordning (`Ordning.aktieandel`), men brugerfladen sætter den aldrig. Alle ordninger regnes med registrets standardprofil | Branchestandardens tal kan afvige fra selskabets prognose, hvis ordningen har en anden aktieandel | **Teksten rettet** (PR #47): forklaringen siger nu standardprofil, og forenklingen `branchestandard_standardprofil` vises ved resultatet. Kalibreringen er en senere feature |
| M4 | **Ingen fast administrationsomkostning.** Spec 035 og [`branchestandard-metode.md`](branchestandard-metode.md) beskrev, at et fast gebyr i kroner pr. år trækkes fra opsparingen. Kernen kan det (`Ordning.gebyr_pr_aar`), men feltet sættes aldrig og er 0. Rådets investeringsomkostninger er med | Branchestandardens tal er en anelse for høje i forhold til selskabernes, mest for små opsparinger | **Teksten rettet** (PR #47): forenklingen `branchestandard_uden_administrationsomkostning` vises ved resultatet. Et gebyr kræver en sats med kilde i registret (Princip III) og er en senere feature |
| M5 | **Ingen Content-Security-Policy.** Siden satte ingen CSP | Et ekstra forsvarslag manglede | **Lukket** (PR #46): CSP i `<meta>` og `tests/browser/test_csp.py`. Den dækker siden, ikke workeren (afsnit 2.8) |
| M2 | `tekst.py` har funktionerne `relevante_sider` og `fjern_cpr` fra den tidligere løsning (kommentaren nævner "tokens"). De bruges kun af tests, ikke af importen | Ingen. Koden sender intet nogen steder (afsnit 2) | Kan fjernes |
| M3 | PDF-parseren er udledt af rigtige rapporter og PensionsInfos demorapport (2026). Et nyt layout hos PensionsInfo kan give manglende felter | Manglende felter giver bemærkninger og tomme felter i guiden, ikke forkerte tal uden bemærkning (afsnit 3.6) | Overvåges. Fejlrettet senest i PR #39 |

---

*Spørgsmål til metoden: se koden og testene, som dette dokument henviser til, eller spec'en for den
feature, der indførte reglen (`specs/`).*
