# Sådan udvikles løsningen – udviklingsmetode

Denne beskrivelse redegør for, hvordan PensionsAnalytikeren udvikles, testes og udgives: processen fra et
ønske til en ændring i drift, de regler, der styrer arbejdet, og hvilke og hvor omfattende test der køres.
Den er skrevet til den tekniske revision og supplerer metodebeskrivelsen, som forklarer, hvad løsningen
regner, og hvordan data beskyttes<!-- teknisk --> ([metode.md](metode.md))<!-- /teknisk -->.

Tal i beskrivelsen (antal test, features og registerposter) er opgjort 26. november 2026 og ændrer sig, efterhånden
som løsningen udvikles. De kan altid tælles op igen i repositoriet<!-- teknisk --> (afsnit 12.3)<!-- /teknisk -->.

<!-- teknisk -->

## Indhold

1. [Overblik](#1-overblik)
2. [Roller og ansvar](#2-roller-og-ansvar)
3. [Styrende dokumenter](#3-styrende-dokumenter)
4. [Processen pr. feature (specifikationsdrevet udvikling)](#4-processen-pr-feature-specifikationsdrevet-udvikling)
5. [Test først](#5-test-først)
6. [Testsuiten: hvad der testes, og hvor meget](#6-testsuiten-hvad-der-testes-og-hvor-meget)
7. [Testdata og persondata](#7-testdata-og-persondata)
8. [Byg og leverancekæde](#8-byg-og-leverancekæde)
9. [Kontinuerlig integration og udgivelse](#9-kontinuerlig-integration-og-udgivelse)
10. [Ændringer, review og godkendelse](#10-ændringer-review-og-godkendelse)
11. [Brug af AI i udviklingen](#11-brug-af-ai-i-udviklingen)
12. [Dokumentation og sporbarhed](#12-dokumentation-og-sporbarhed)
13. [Årlig satsopdatering](#13-årlig-satsopdatering)
14. [Begrænsninger og anbefalinger](#14-begrænsninger-og-anbefalinger)

<!-- /teknisk -->

## 1. Overblik

PensionsAnalytikeren er genopbygget fra bunden fra 24. oktober 2026 med **specifikationsdrevet udvikling**
(Spec Driven Development, SDD). Hver ændring begynder som en skriftlig specifikation af *hvad* og *hvorfor*.
Først når spørgsmålene er afklaret, planlægges *hvordan*, og der skrives test, før koden skrives.

Arbejdet er bundet af en **forfatning** med 11 principper. Tre af dem kan ikke fraviges: beregningen er
deterministisk (AI'en beregner aldrig), test skrives først med facit-tal, og persondata må aldrig sendes
til en AI- eller LLM-tjeneste.

Kort fortalt:

| | |
|---|---|
| Proces | Én feature ad gangen: specifikation → afklaring → plan → opgaver → test → kode |
| Facit | Lovgivningen. Alle satser står ét sted med kilde og status |
| Test | Over 1.250 automatiske test: håndregnede facit-tal, regelgrænser, egenskaber, sammenligning med den tidligere løsning, kontrakter, brugerflade i en rigtig browser |
| Udgivelse | Kun fra hovedgrenen og kun, når hele testsuiten er bestået i et rent miljø |
| Godkendelse | Produktejeren træffer beslutningerne og godkender hver udgivelse udtrykkeligt |
| Persondata | Kun syntetiske testdata i repositoriet og i udviklingen. Rigtige rapporter testes kun lokalt af produktejeren |

<!-- teknisk -->
Repositoriet: kernen i `src/pensionskerne/`, brugerfladen i `src/pensionsoverblik/`, specifikationer i
`specs/NNN-*/`, test i `tests/`, byggescripts i `scripts/` og den tidligere løsning (kun orakel) i `legacy/`.
<!-- /teknisk -->

## 2. Roller og ansvar

| Rolle | Ansvar |
|---|---|
| **Produktejer** | Beslutter, hvad der skal laves, og svarer på alle afklaringsspørgsmål. Godkender hver udgivelse. Kører test mod sine egne, rigtige PensionsInfo-rapporter lokalt. Ejer forfatningen |
| **Udvikler (AI-kodeassistent)** | Skriver specifikation, plan, opgaver, test, kode og dokumentation efter forfatningen og produktejerens beslutninger. Kører testsuiten. Har ingen adgang til persondata (afsnit 7 og 11) |
| **Automatisk kontrol** | Testsuiten og byggeprocessen i et rent miljø. Uden bestået suite udgives intet |
| **Revision** | Læser forfatning, specifikationer, test, metodebeskrivelse og denne beskrivelse. Alt er offentligt i repositoriet |

Beslutninger, produktejeren har truffet, står i specifikationernes afklaringsafsnit med dato og
markeringen "(produktejer)". Det er altså sporbart, hvilke valg der er produktejerens, og hvilke der er
foreslået af udvikleren.

## 3. Styrende dokumenter

**Forfatningen**<!-- teknisk --> (`.specify/memory/constitution.md`, version 1.2.0)<!-- /teknisk --> har forrang for alt andet.
Den er versioneret semantisk: et fjernet eller omdefineret princip er en MAJOR-ændring, et nyt princip
MINOR og en sproglig præcisering PATCH. Hver ændring har en ændringsrapport øverst i dokumentet. Principperne:

| Princip | Indhold |
|---|---|
| I (kan ikke fraviges) | Deterministisk beregning. AI'en beregner aldrig |
| II | Regelregister: ét kildested for alle satser, med kildehenvisning |
| III | Lovgivningen er facit. Forenklinger skal dokumenteres |
| IV (kan ikke fraviges) | Test først med facit-tal |
| V | Sporbarhed: hvert tal kan spores til satser og antagelser |
| VI | Isoleret beregningskerne uden I/O, netværk, AI eller brugerflade |
| VII | Persondata og privatliv |
| VIII | Dansk brugerflade |
| IX | Simpelhed |
| X | Brugeroplevelse: klarhed før fuldstændighed |
| XI (kan ikke fraviges) | Ingen persondata til AI/LLM |

Forfatningen fastlægger også **kildehierarkiet** for satser (lovgivning, myndigheder, lovbestemte
institutioner, sekundære kilder), **den tidligere løsnings rolle** (kun kilde til domæneviden og orakel i
test, aldrig facit) og **kvalitetsporte**: hele testsuiten skal bestå før en sammenlægning, et tal uden for
regelregistret afvises, og en regel uden lovhenvisning afvises.

Øvrige styrende dokumenter:

- **Arbejdsreglerne for udviklingen**<!-- teknisk --> (`CLAUDE.md`)<!-- /teknisk -->: kommandoer, struktur og de regler,
  udvikleren skal følge, fx at persondata aldrig må sendes til AI, og at rigtige rapporter aldrig må gemmes i repositoriet.
- **Domænegrundlaget**<!-- teknisk --> (`docs/domaene/beregningskerne.md`)<!-- /teknisk -->: lovgrundlaget og de kendte
  afvigelser i den tidligere løsning (A1–A12), hver med kilde.
- **Designretningen**<!-- teknisk --> (`docs/ux/designretning.md`)<!-- /teknisk -->: retningslinjer for brugerfladen.
- **Skabelonerne**<!-- teknisk --> (`.specify/templates/`)<!-- /teknisk --> for specifikation, plan, opgaver og tjeklister.

## 4. Processen pr. feature (specifikationsdrevet udvikling)

Hver ændring af betydning er en **feature** med et løbenummer og sin egen mappe. Der er pt. 42 feature-mapper.
Fire af dem (bolig, arv, Monte Carlo-simulering og efterladte) har kun en specifikation. En del af specifikationen om arv er siden bygget i en senere feature.

### 4.1 Trinene

1. **Specifikation.** Brugerens ønske skrives ned ordret som input. Specifikationen beskriver problemet,
   brugerhistorier med prioritet og acceptkriterier ("Givet … når … så …"), krav (FR) og målbare
   succeskriterier (SC). Den er teknologiuafhængig.
2. **Afklaring.** Åbne spørgsmål stilles til produktejeren, typisk med et anbefalet svar. Svarene skrives
   ind i specifikationen med dato og "(produktejer)". Er en regel uklar, researches den mod kildehierarkiet,
   og kilderne skrives i specifikationen.
3. **Plan.** For større features: teknisk plan, research og datamodel. Planen gennemgår alle principper i
   forfatningen ("Constitution Check"). En afvigelse skal begrundes skriftligt, før arbejdet fortsætter.
   Ændringer, der rører persondata, skal beskrive opbevaring og sletning.
4. **Opgaver.** En nummereret liste, hvor testopgaverne kommer før implementeringsopgaverne.
5. **Implementering.** Test skrives og ses fejle, koden skrives, og hele suiten køres (afsnit 5).
6. **Evaluering.** For features med brugerflade en kort UX-evaluering: automatiske målinger (fx svartider
   og tilgængelighed), en heuristisk gennemgang og åbne fund.
7. **Dokumentation.** Metodebeskrivelsen og forklaringerne i løsningen opdateres i samme ændring.

Spec Kit-værktøjets kommandoer er ikke installeret i dette checkout. Trinene følges derfor manuelt med
skabelonerne og hjælpescriptene<!-- teknisk --> i `.specify/templates/` og `.specify/scripts/powershell/`<!-- /teknisk -->.

### 4.2 Artefakter

| Artefakt | Indhold | Hvornår |
|---|---|---|
| Specifikation | Problem, afklaringer, brugerhistorier, krav, succeskriterier, lovgrundlag | Altid |
| Opgaveliste | Nummererede opgaver, test først | Når featuren bygges |
| Plan og research | Teknisk løsning, Constitution Check, kilder | Større features (27 af 42) |
| Datamodel og kontrakt | Ind- og uddata, grænseflader | Kernen, brugerfladen |
| UX-evaluering | Målinger, heuristik, åbne fund | Features med brugerflade |

<!-- teknisk -->
Filerne hedder `spec.md`, `tasks.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/` og
`ux-evaluering.md` i `specs/NNN-navn/`.
<!-- /teknisk -->

### 4.3 Et eksempel: planens slutning og penge tilbage

Produktejeren ønskede at kunne vælge, hvor længe pengene skal række, og et beløb, der skal være tilbage.
Forløbet var:

1. Udvikleren undersøgte koden og fandt, at slutalderen fandtes i kernen, og at "penge tilbage" var
   besluttet, men ikke bygget i en tidligere specifikation. Udvikleren foreslog en løsning og stillede tre
   spørgsmål (par, placering og visning af prisen).
2. Produktejeren svarede. Svarene står i specifikationen med dato.
3. Opgavelisten blev skrevet med test først: håndregnede facit-tal for udjævningen, test af app-laget og
   browsertest.
4. Testene fejlede, koden blev skrevet, og den fulde suite (også browsertestene) bestod lokalt.
5. Ændringen blev lagt op til gennemsyn. Den automatiske kontrol bestod, og produktejeren godkendte
   sammenlægningen udtrykkeligt. Udgivelsen blev kontrolleret på den offentlige side.

## 5. Test først

Princip IV kan ikke fraviges: al beregningslogik udvikles med test først.

- **Rækkefølgen** er: testen skrives, den køres og fejler, så skrives koden, og testen består.
- **Golden cases** er håndregnede facit-tal, helst lovens eller myndighedernes egne eksempler, og med
  kildehenvisning. De regnes ved simple forudsætninger (fx afkast og inflation 0), så de kan efterregnes
  med blyant. En golden case må kun ændres med en skriftlig begrundelse.
- **Regelgrænser** testes lige på, under og over hver tærskel i regelregistret.
- **Fejlrettelser** får en test, der fejler før rettelsen.
- **Standardværdier** ændrer intet: når en ny feature tilføjes, skal alle eksisterende test bestå uændret
  med featurens standardværdier. Det er beviset for, at ændringen ikke flytter andre tal.
- **Hele suiten** kan køres med én kommando uden netværk eller kørende server.

## 6. Testsuiten: hvad der testes, og hvor meget

Suiten har **1.253 test**. De 1.044 køres i Python. De 209 browsertest kører den byggede side i en rigtig
browser (Chromium) med beregningsmotoren i browseren, som borgeren bruger den. Mange test er
parametriserede: én testfunktion afprøves med flere værdier, og hver værdi tælles som én test.

### 6.1 Oversigt

| Kategori | Antal | Hvad testen sikrer |
|---|---|---|
| Regler | 73 | Hver regel for sig (skat, folkepension, ydelser, ATP, udbetalingsalder m.fl.), også ved grænserne |
| Golden cases | 278 | Håndregnede facit-tal for hele beregninger, fx udjævning, skat, partner og depot |
| Egenskaber | 4 (+8 i andre kategorier) | Invarianter med tilfældige input (afsnit 6.3) |
| Differentialtest | 287 | Samme tal som den tidligere løsning, hvor reglen er uændret (afsnit 6.4) |
| Regelregister | 29 | Struktur, kilder, dækning og at ingen satser står i koden (afsnit 6.5) |
| Kontrakter | 28 | Kernens grænseflade, inputvalidering, ingen AI og tilladte pakker (afsnit 6.6) |
| Optimering | 28 | "Find bedste plan" er aldrig dårligere end udgangspunktet og holder sig inden for lovens grænser |
| App-laget | 316 | Oversættelse fra guiden til kernen, visningen, PDF-aflæsningen, forklaringerne og metodesiden |
| Ydeevne | 1 | 40 år og 10 ordninger beregnes på under 100 ms |
| Browser | 209 | Brugerforløb, samme tal som i Python, ingen netværkstrafik, tilgængelighed og mobilbredde (afsnit 6.7) |
| **I alt** | **1.253** | |

<!-- teknisk -->
Mapperne er `tests/regler`, `tests/golden`, `tests/egenskaber`, `tests/differential`, `tests/register`,
`tests/kontrakt`, `tests/optimering`, `tests/app`, `tests/ydeevne` og `tests/browser`. Browsertestene har
markeringen `browser` og springes over i den almindelige kørsel (`addopts = "-m 'not browser'"` i
`pyproject.toml`).
<!-- /teknisk -->

### 6.2 Golden cases

Golden cases er kernen i beviset for, at tallene er rigtige. Eksempler:

- **Udjævning:** med rente og inflation 0 er det faste beløb gennemsnittet af det, der er kommet ind, til og
  med det bindende år. Fx giver udbetalingerne 300, 0 og 0 et fast beløb på 100 hvert år og en opsparing på
  200, 100 og 0. Med 60 tilbage til sidst bliver det 80 hvert år, og opsparingen ender på 60.
- **Skat og ydelser:** konkrete personer med kendte indkomster, hvor skat, pensionstillæg og ældrecheck er
  regnet i hånden efter loven.
- **Branchestandarden:** tallene fra branchens egen vejledning (bilag) gentages.

Hver golden case har en kommentar med regnestykket, så den kan efterregnes.

### 6.3 Egenskabsbaserede test

Med et værktøj, der genererer tilfældige input (Hypothesis), testes egenskaber, der altid skal gælde,
fx at skatten ligger mellem 0 og indkomsten, at marginalskatten er under skatteloftet, at pensionstillægget
falder, når indkomsten stiger, at tillægsprocenten er et helt tal fra 0 til 100, at udjævningen aldrig
låner og aldrig falder, og at fordelingen over tid holder sine andele. Hver egenskab afprøves med op til 300
tilfældige eksempler pr. kørsel.

### 6.4 Differentialtest mod den tidligere løsning

Den tidligere løsning bruges som **orakel**, ikke som facit. Testen sammenligner i to lag:

1. **Regelfunktioner**, hvor reglen er uændret (fx progressiv skat ved otte indkomster i fire kommuner),
   skal give samme tal med en tolerance på 1 øre.
2. **Hele år** med forenklede forudsætninger, hvor den eneste kendte forskel er en dokumenteret fejl i den
   tidligere løsning. Testen kontrollerer, at forskellen netop svarer til fejlen.

Alle afvigelser fra den tidligere løsning skal kunne forklares af en dokumenteret lovrettelse (A1–A12 i
domænegrundlaget) eller et bevidst ændret valg.

### 6.5 Regelregistret

Alle satser for et satsår står i ét register med kilde og status. For 2026 er der 85 poster: 80 er
verificeret mod lov, myndighed eller lovbestemt institution, og 5 bygger på sekundære kilder og vises som
sådan i løsningen. Testene sikrer bl.a.:

- at mindst 90 % af posterne er verificeret,
- at **ingen satser står som tal i beregningskoden**. En test gennemgår koden og afviser tal, der burde stå i
  registret,
- at hver forenkling, kernen bruger, er beskrevet i forenklingsregistret (19 forenklinger), og at
  beregningen markerer, når en forenkling påvirker resultatet,
- at opslag er sporbare, så hvert tal kan føres tilbage til de poster, der indgik.

### 6.6 Kontrakter og sikkerhed

- **Kernens grænseflade:** samme input og samme dato giver altid samme output, og fejl i input giver en
  fejl ved det rigtige felt og aldrig et delvist resultat.
- **Ingen AI (Princip XI):** en test gennemgår al kode og alle afhængigheder og afviser klientbiblioteker
  til AI-tjenester og adresser på AI-tjenester. Den sikrer også, at PDF-aflæsningen altid er den lokale
  parser.
- **Tilladte pakker:** koden, der kører i browseren, må kun bruge Pythons standardbibliotek, projektets egne
  pakker og PDF-læseren. Alt andet afvises.

### 6.7 Browsertest

Browsertestene bygger den statiske side og kører den med Playwright i Chromium, som en borger ville:
indlæser en syntetisk rapport, udfylder guiden, flytter skydere og trækker i tidslinjen. De dækker:

| Område | Hvad der sikres |
|---|---|
| Samme tal som i Python | Beregningen i browseren giver præcis samme svar som i Python (8 testfiler) |
| Intet forlader browseren | Under et helt forløb sender siden ingen data og henter kun sine egne filer |
| Indholdssikkerhedspolitik | Browseren blokerer selv forbindelser til andre domæner, og et helt forløb giver ingen overtrædelser |
| Tilgængelighed | Automatisk kontrol mod WCAG 2.2 AA med axe-core (25 testfiler) |
| Mobilbredde | Ingen vandret rulning ved 360 og 320 pixels (13 testfiler) |
| Brugerforløb | Guiden, resultatet, faner for par, "Find bedste plan", gem og åbn, forklaringerne og metodesiden |
| Gem lokalt | Den gemte fil er krypteret og indeholder ingen persondata i klartekst; forkert adgangskode giver intet resultat |
| Indlæsning | Siden kan bruges, mens motoren indlæses, og giver en klar besked, hvis browseren ikke kan køre den |

### 6.8 Rigtige rapporter

Parseren af PensionsInfo-rapporter testes med en syntetisk rapport, som genereres af testkoden. Derudover
findes en test, der kun kører, når produktejeren peger på en rigtig rapport på sin egen maskine. Den køres
lokalt af produktejeren, og resultatet deles ikke (afsnit 7).

<!-- teknisk -->
`PENSIONSINFO_RAPPORT=<sti> uv run pytest -k rigtig`. Den syntetiske rapport er
`tests/app/pensionsinfo_syntetisk.py`.
<!-- /teknisk -->

### 6.9 Omfang og tid

- Den almindelige kørsel (1.044 test) tager få minutter på en udviklermaskine.
- Den automatiske kontrol (installation, alle test, byg og browsertest) tog fx 40 minutter for den seneste
  feature.
- Dækningsgrad (hvor stor en del af koden testene gennemløber) måles ikke automatisk (afsnit 14).

## 7. Testdata og persondata

- **Kun syntetiske data** i repositoriet: testpersoner, ordninger og en genereret PensionsInfo-rapport.
- **Rigtige rapporter må aldrig gemmes i repositoriet.** Det står i arbejdsreglerne, og parseren må hverken skrive til disk eller logge.
- **Test mod rigtige rapporter** køres kun af produktejeren på egen maskine. Udvikleren (AI-assistenten) får
  hverken rapporten, dens tekst eller testens uddata. Produktejeren har konkret stoppet forsøg på at køre
  sådanne test, hvor uddata ville komme tilbage til assistenten.
- **Scanning før offentliggørelse:** et script gennemsøger hele historikken for persondata og
  hemmeligheder. Det skriver aldrig de fundne værdier ud, kun hvor de står. Det kan også læse navn,
  CPR-nummer og aftalenumre fra en rigtig rapport (kun i hukommelsen) og søge efter netop de værdier.
  Kendte falske fund (fx tal i låsefiler, der ligner datoer) vurderes manuelt.

<!-- teknisk -->
Scriptet er `scripts/scan_historik.py`.
<!-- /teknisk -->

## 8. Byg og leverancekæde

- **Låste afhængigheder.** Python-afhængighederne er låst med versioner og hashes, og den automatiske
  kontrol installerer kun det låste. Der er ingen afhængigheder i kernen, og brugerfladen bruger kun
  PDF-læseren.
- **Browserens filer er låst til SHA-256.** Pyodide (Python i browseren) og alle pakker til PDF-læseren er
  låst til en version og en SHA-256-værdi. Byggescriptet henter filerne og stopper ved enhver afvigelse.
- **Ingen CDN ved brug.** Siden henter kun sine egne filer fra samme adresse. Der indlæses intet fra andre
  domæner, når borgeren bruger løsningen.
- **Byggescriptet** bruger kun Pythons standardbibliotek og laver en statisk side uden server.
- **En ny afhængighed** kræver, at den tilføjes låsefilen med SHA-256, og at testen af tilladte pakker
  opdateres. Det kan derfor ikke ske ubemærket.

<!-- teknisk -->
`uv.lock` (`uv sync --frozen`), `scripts/pyodide_laas.toml`, `scripts/byg_side.py`,
`tests/kontrakt/test_browserpakker.py`.
<!-- /teknisk -->

## 9. Kontinuerlig integration og udgivelse

Løsningen udgives som en statisk side på GitHub Pages. Den automatiske kontrol (GitHub Actions) kører ved hver
ændring:

1. Et rent miljø installeres med de låste afhængigheder.
2. Alle test i Python køres.
3. Siden bygges.
4. En browser installeres, og browsertestene køres mod den byggede side.
5. Den byggede side gemmes.
6. **Kun på hovedgrenen og kun hvis alle trin er bestået** udgives siden.

Forslag til ændringer testes og bygges, men udgives ikke. Kontrollen har kun læseadgang til repositoriet;
kun udgivelsestrinnet har ret til at udgive. En ny kørsel på samme gren afbryder den forrige, så kun den
nyeste version udgives.

Efter en udgivelse kontrollerer udvikleren, at ændringen kan ses på den offentlige side.

<!-- teknisk -->
Workflowet er `.github/workflows/pages.yml` med jobbene `test-og-byg` og `udgiv` (`needs: test-og-byg`,
`if: github.ref == 'refs/heads/main'`, `permissions: contents: read`; udgiv har `pages: write`).
<!-- /teknisk -->

## 10. Ændringer, review og godkendelse

- **Én gren pr. feature.** Der arbejdes aldrig direkte på hovedgrenen.
- **Forslag til ændring** (pull request) med en beskrivelse af ændringen. Den automatiske kontrol kører på
  forslaget.
- **Sammenlægning kun med produktejerens udtrykkelige godkendelse**, og først når den lokale suite og den
  automatiske kontrol er bestået. Udviklingsmiljøet håndhæver det: en sammenlægning uden godkendelse i den
  aktuelle sammenhæng bliver afvist, også når en tidligere godkendelse findes.
- **Gennemsyn:** produktejeren gennemser adfærd, tekster og beslutninger. Udvikleren gennemgår sine
  ændringer mod forfatningen (satser kun i registret, kilde til hver regel, ingen persondata til AI).
  Der er ingen fast, uafhængig menneskelig kodegennemgang (afsnit 14).
- **Historik:** hver ændring har en commit-besked, der beskriver hvad og hvorfor, og ændringer skrevet af
  AI-assistenten er markeret som medforfattet af den. Historikken har pt. over 180 commits og 50
  sammenlægninger.

## 11. Brug af AI i udviklingen

Koden, testene og dokumentationen skrives af en AI-kodeassistent (Claude Code) under produktejerens ledelse.
Det har betydning for revisionen på tre punkter:

1. **AI er et udviklingsværktøj, ikke en del af løsningen.** Løsningen indeholder ingen AI. Beregningen er
   deterministisk (Princip I), og en test afviser enhver forbindelse til AI-tjenester i koden (afsnit 6.6).
2. **Ingen persondata til AI (Princip XI).** Assistenten arbejder kun med kode, syntetiske testdata,
   lovtekster og offentlige kilder. Den får aldrig rapporter, CPR-numre eller borgerens tal (afsnit 7).
3. **Kontrol i stedet for tillid.** Det, assistenten skriver, er bundet af de samme porte som al anden
   kode: test først med håndregnede facit-tal, satser kun fra registret med kilde, differentialtest og
   den automatiske kontrol. Produktejeren træffer alle beslutninger og godkender hver udgivelse.

Assistenten skal følge arbejdsreglerne og forfatningen. Er en regel uklar, skal den spørge produktejeren
eller researche mod kildehierarkiet, ikke gætte.

## 12. Dokumentation og sporbarhed

### 12.1 Fra krav til kode

| Spor | Hvor |
|---|---|
| Ønske og beslutninger | Specifikationen (input ordret, afklaringer med dato) |
| Krav til test | Opgavelisten og testenes beskrivelse, som henviser til krav og succeskriterier |
| Sats til kilde | Regelregistret: hver post har kilde, status og satsår |
| Tal til satser | Hver beregning registrerer de poster og antagelser, der indgik |
| Forenklinger | Forenklingsregistret og afsnit 13 i metodebeskrivelsen |
| Afvigelser fra den tidligere løsning | Domænegrundlaget (A1–A12) med kilde |

### 12.2 Én kilde til metodebeskrivelsen

Metodebeskrivelsen og denne beskrivelse vedligeholdes som én tekst hver. Den fulde tekst med henvisninger
til koden ligger i repositoriet. Siderne i løsningen laves af samme tekst ved byggeriet, uden det rent
tekniske. En test sikrer, at siderne ikke indeholder kodenavne, og at alle henvisninger virker.

### 12.3 Optælling

Tallene i denne beskrivelse kan tælles op igen i repositoriet med testværktøjet og versionsstyringen.

<!-- teknisk -->
```
uv run pytest --collect-only -q -m "browser or not browser"   # antal test pr. fil
git log --oneline | wc -l                                      # commits
ls specs | wc -l                                               # feature-mapper
```
<!-- /teknisk -->

## 13. Årlig satsopdatering

Forfatningen fastlægger proceduren for et nyt satsår:

1. Et nyt satsår tilføjes i registret.
2. Hver post verificeres mod kildehierarkiet, og status sættes derefter.
3. Golden cases opdateres med nye, eksplicit forventede tal. Det er ikke nok, at testene "stadig er
   grønne".

## 14. Begrænsninger og anbefalinger

Revisionen bør være opmærksom på:

| Emne | Status | Anbefaling |
|---|---|---|
| Uafhængig kodegennemgang | Ingen fast, menneskelig gennemgang af koden. Kvaliteten sikres af test først, facit-tal og automatisk kontrol | Stikprøvevis gennemgang af kernen og regelregistret ved en uafhængig fagperson |
| Dækningsgrad | Måles ikke automatisk | Indfør måling af dækningsgrad i den automatiske kontrol |
| Browsere | Browsertestene kører kun i Chromium | Supplér med Firefox og Safari (WebKit) |
| Brugertest | UX-evalueringerne er automatiske målinger og heuristisk gennemgang, ikke test med borgere | Gennemfør brugertest med målgruppen |
| Rigtige rapporter | Parseren afhænger af rapportens layout. Den testes med en syntetisk rapport og lokalt af produktejeren | Fortsæt overvågningen (fund M3 i metodebeskrivelsen) og indsaml anonymiserede layouteksempler |
| Den tidligere løsning som orakel | Differentialtesten dækker kun områder, hvor reglen er uændret | Fjern den, når genopbygningen dækker al funktionalitet (forfatningens regel) |
| Spec Kit | Trinene følges manuelt, ikke med værktøjets kommandoer | Installer kommandoerne, så trinene håndhæves |
