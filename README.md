# PensionsAnalytikerSDD

Beslutningsstøtteværktøj til dansk pensionsplanlægning, genopbygget fra bunden med
spec-driven development ([Spec Kit](https://github.com/github/spec-kit)).

**Prøv det:** <https://jaisper.github.io/PensionsAnalytikerSDD/>

Borgeren indlæser sin rapport fra PensionsInfo eller udfylder en kort guide. Værktøjet viser så,
hvad borgeren kan forvente at få udbetalt om måneden efter skat. Det finder den plan for udbetalingerne,
der giver det højeste faste beløb, og forklarer, hvordan tallet er regnet.

## Privatliv

- **Alt kører i browseren.** Beregningen og PDF-aflæsningen er Python, som kører i browseren via
  [Pyodide](https://pyodide.org). Der er ingen server, og ingen oplysninger forlader borgerens
  computer.
- **Ingen AI på persondata** (forfatningens Princip XI). PensionsInfo-rapporten læses af en lokal,
  regelbaseret parser. `src/` må ikke indeholde AI-klienter, -afhængigheder eller -endpoints, og det
  håndhæves af en test (`tests/kontrakt/test_ingen_ai.py`).
- **Intet gemmes, medmindre borgeren beder om det.** "Gem" laver en fil, som er krypteret med
  browserens Web Crypto og ligger på borgerens egen computer.

## Hvad værktøjet kan

**Indlæsning**
- Upload af PensionsInfo-rapporten (PDF). Guiden udfyldes med ordninger, saldi, udbetalinger og
  forsikringer (003, 031).
- Løn som på lønsedlen: månedsløn og pensionsprocenter. Nettolønnen vises til sammenligning (017b–c).
- Partner som fuld profil, også med egen rapport (012). Frie midler i bank, frit depot og
  aktiesparekonto (013, 013b).

**Beregning**
- År for år fra i dag til planens slutning: skat, folkepension med pensionstillæg, ældrecheck,
  ratepension, livrente, kapitalpension og frie midler (001, 009, 013).
- Ægtefæller overfører personfradrag og bundfradrag for kapitalindkomst, og ydelserne regnes for
  husstanden (012).
- **Det faste beløb:** udbetalingerne udjævnes til ét beløb om måneden. Engangsbeløb kan lægges i en
  buffer, der beskattes som kapitalindkomst. Det faste beløb låner aldrig af senere udbetalinger, og
  bufferen går aldrig i minus (008, 010, 029).
- **Den bedste plan:** optimeringen flytter udbetalingernes start og varighed og vælger
  kapitalpensionens udbetalingsform. Den finder det højeste faste beløb efter skat og regnes med det
  samme, mens "Finder bedste plan …" vises (007, 007b, 032). Uden en valgt stopalder stopper lønnen,
  når den første udbetaling begynder (030).
- "Hvornår kan jeg stoppe?" og "Hvor skal næste krone hen?" (017, 021).

**Usikkerhed**
- Spænd for afkast (±1 procentpoint) og inflation (±0,5 procentpoint) (018).
- Levetid som scenarie: planen til 85 og 95 år (019).
- Afkast pr. år med "dårlige år først" (023a).

**Visning**
- Hovedtal, graf og tidslinje. Hver ordning er en bjælke, som kan trækkes i tid med mus eller
  tastatur (004, 006, 025). Stopalderen er et punkt, der kan trækkes.
- Søjler med "Fra din buffer" og "Sættes til side", og bufferens ind, ud og saldo år for år (027, 029).
- Forklaring i tre niveauer, skift mellem nominelle beløb og dagens kroner, udskrift og eksport til
  rådgiveren (020).
- Forsikringer fra rapporten under "Hvis du bliver syg eller dør" (031).
- WCAG 2.2 AA. axe-core kører i browsertestene.

## Principper

Projektets [forfatning](.specify/memory/constitution.md) har forrang for alt andet. Kort fortalt:

| | Princip |
|---|---|
| I | Deterministisk beregning. AI'en beregner aldrig |
| II | Ét regelregister med kildehenvisning for hver sats |
| III | Lovgivningen er facit |
| IV | Test først med facit-tal. En ændret golden case kræver en begrundelse |
| V | Sporbarhed: borgeren kan se, hvordan tallet er regnet |
| VI | Beregningskernen er isoleret fra brugerfladen |
| VII | Persondata og privatliv |
| VIII | Dansk brugerflade |
| IX | Simpelhed |
| X | Brugeroplevelse: klarhed før fuldstændighed (se også [designretning.md](docs/ux/designretning.md)) |
| XI | Ingen persondata til AI/LLM |

## Arkitektur

```
PensionsInfo-PDF ──► pdfimport ──► guide (svar) ──► pensionskerne.beregn ──► visning ──► HTML/JS
                                                    ▲
                                       register/2026.toml (satser med kilde)
```

| Sti | Indhold |
|---|---|
| `src/pensionskerne/` | Beregningskernen. Ren Python uden afhængigheder og med én offentlig funktion, `beregn` |
| `src/pensionskerne/register/` | Alle satser for året (`2026.toml`) med kilde og status, plus kommuneskatter og forenklinger. 65 af 66 satser er verificeret mod primærkilder |
| `src/pensionskerne/regler/` | Ét modul pr. lovområde (skat, folkepension, ydelser, aktier, udbetalingsalder, opsat pension, løn). Rene funktioner uden tal; satserne læses fra registret |
| `src/pensionskerne/fremskrivning.py` | År-for-år-fremskrivningen, inklusive bufferens fastpunkt |
| `src/pensionskerne/jaevn.py`, `optimering.py` | Det faste beløb og søgningen efter den bedste plan |
| `src/pensionsoverblik/` | Brugerfladen: statisk HTML, CSS og JS uden build. `app.py` er indgangspunktet, som kører i en web worker via Pyodide. Visningslaget omformaterer kun kernens tal |
| `src/pensionsoverblik/pdfimport/` | Lokal, deterministisk parser til PensionsInfo-rapporten. Intet skrives til disk eller logs |
| `scripts/byg_side.py` | Bygger den statiske side til `_site/` |
| `scripts/pyodide_laas.toml` | Låste versioner af Pyodide og pakkerne med SHA-256 |
| `scripts/scan_historik.py` | Scanner git-historikken for persondata før push |
| `specs/NNN-*/` | Én mappe pr. feature: `spec.md`, `plan.md`, `tasks.md` og eventuelt research, datamodel og kontrakt |
| `docs/` | [Domænegrundlag og legacy-afvigelser](docs/domaene/beregningskerne.md), [roadmap](docs/roadmap.md), [modning](docs/modning.md) og [designretning](docs/ux/designretning.md) |
| `legacy/` | Den oprindelige løsning (tag `legacy-v1`). **Kun reference og orakel**, se nedenfor |

`src/` må kun importere standardbiblioteket, projektets egne pakker og pdfplumber/pdfminer, fordi
alt skal kunne køre i Pyodide. En ny afhængighed skal låses i `scripts/pyodide_laas.toml`.

## Kom i gang

Kræver Python 3.11+ og [uv](https://docs.astral.sh/uv/).

```bash
uv sync                                        # miljø
uv run pytest                                  # CPython-suiten (uden browsertests)
uv run python scripts/byg_side.py              # statisk side i _site/
uv run python -m http.server -d _site 8002     # åbn http://127.0.0.1:8002
uv run playwright install chromium             # første gang, før browsertestene
uv run pytest -m browser                       # samme kode i Pyodide, sammenlignet med CPython
```

Rigtige PensionsInfo-rapporter må aldrig committes. Test lokalt mod din egen med:

```bash
PENSIONSINFO_RAPPORT=<sti til PDF> uv run pytest -k rigtig
```

## Tests

Ca. 1.000 tests: 880 i CPython-suiten og 139 browsertests.

| Mappe | Hvad den tester |
|---|---|
| `tests/regler/`, `tests/register/` | Hver regel mod lovens eksempler og satserne mod registret. Ingen tal i `regler/` |
| `tests/golden/` | Hele beregninger med facit-tal |
| `tests/differential/` | Den nye kerne mod legacy-løsningen som orakel |
| `tests/egenskaber/` | Egenskabsbaserede tests (Hypothesis) |
| `tests/optimering/` | Den bedste plan |
| `tests/kontrakt/` | Grænser: ingen AI, kun tilladte pakker i browseren, kernens offentlige API og validering af input |
| `tests/app/` | Visningslaget og PDF-aflæsningen mod syntetiske rapporter |
| `tests/browser/` | Den byggede side i Chromium (Playwright): Pyodide mod CPython, tilgængelighed og brugerforløb |
| `tests/ydeevne/` | Beregningen tager under 100 ms |

GitHub Actions ([pages.yml](.github/workflows/pages.yml)) kører begge suiter på hver pull request.
Fra `main` udgives siden på GitHub Pages.

## Features

| Feature | Indhold |
|---|---|
| [001 Beregningskerne og regelregister](specs/001-beregningskerne/) | Kernen, registret og differentialtesten mod legacy. Én sats har stadig kun en sekundær kilde (PBL § 1 A) |
| [002 Pensionsoverblik](specs/002-pensionsoverblik/) | Guide og resultat med hovedtal, graf, kort og skydere. [UX-evaluering](specs/002-pensionsoverblik/ux-evaluering.md) |
| [003 Indlæsning af PensionsInfo-rapport](specs/003-pdf-import/) | PDF til guide med en lokal, regelbaseret parser |
| [004 Tidslinje og datapanel](specs/004-tidslinje/) | "Dine oplysninger", graf i fuld bredde og tidslinje |
| [005 Kør i browseren](specs/005-browser/) | Pyodide, ingen server og udgivelse på GitHub Pages |
| [006 Bjælker, der trækkes](specs/006-traek-bjaelker/) | Tidslinjens bjælker er selv kontrollerne |
| [007 Find bedste plan](specs/007-optimering/) | Optimering og engangsbeløb som buffer |
| [007b Den bedste plan med det samme](specs/007b-auto-optimering/) | Den bedste plan er hovedtallet, og borgeren kan skifte til sin egen |
| [008 Buffer i grafen](specs/008-buffer-i-grafen/) | Engangsbeløb i grafen og det faste beløb som hovedtal |
| [009 Kapitalpension](specs/009-kapitalpension/) | Ét beløb, portioner (PBL § 26) eller omlagt (§ 41) |
| [010 Udjævning uden lån](specs/010-ingen-laan/) | Det faste beløb stiger i trin og låner aldrig |
| [012 Partner](specs/012-partner/) | To profiler og fanerne Dig, Partner og Samlet |
| [013 Husstandsbalance](specs/013-husstandsbalance/) | Frie midler i udbetalingsplanen |
| [013b Frit depot og aktiesparekonto](specs/013b-frit-depot-ask/) | Aktieindkomst og lagerbeskatning |
| [017 Arbejdsår og løn](specs/017-arbejdsaar-og-loen/) | "Hvornår kan jeg stoppe?" |
| [017b Nettoløn](specs/017b-nettoloen/) | Nettoløn ved hovedtallet og regulerede indbetalinger |
| [017c Løn som på lønsedlen](specs/017c-loenseddel/) | Månedsløn og pensionsprocenter |
| [018 Usikkerhed](specs/018-usikkerhed/) | Spænd for afkast og inflation |
| [019 Levetid](specs/019-levetid/) | Planen til 85 og 95 år |
| [020 Forklaring](specs/020-forklaring/) | Tre niveauer, dagens kroner og udskrift. Brugertesten (SC-004) udestår |
| [021 Næste krone](specs/021-naeste-krone/) | Hvor skal næste krone hen? |
| [023 Afkast pr. år](specs/023-afkast-pr-aar/) | 023a: "dårlige år først". 023b (afkast pr. aktivtype) udestår |
| [024 Gem lokalt](specs/024-gem-lokalt/) | Krypteret fil på borgerens egen computer |
| [025 Stopalderen i grafen](specs/025-stopalder-i-grafen/) | Stopalderen som et punkt, der kan trækkes |
| [027 Bufferen i søjlerne](specs/027-buffer-i-soejlen/) | "Fra din buffer" og "Sættes til side" |
| [028 Talrullen](specs/028-talrulle/) | Erstattet af 032 |
| [029 Bufferen ind, ud og saldo](specs/029-buffer-ind-ud/) | Bufferen år for år |
| [030 Stopalderen følger](specs/030-stopalder-foelger/) | Uden valgt stopalder stopper lønnen ved første udbetaling |
| [031 Dine forsikringer](specs/031-risikodaekninger/) | Dækninger ved død, tab af arbejdsevne, kritisk sygdom og sundhed fra rapporten |
| [032 "Finder bedste plan …"](specs/032-finder-plan/) | Tekst i stedet for talrullen under søgningen |

**Specificeret, ikke bygget:** [014 Bolig og friværdi](specs/014-bolig/), [015 Arv](specs/015-arv/),
[016 Monte Carlo](specs/016-monte-carlo/) og [022 Hvad hvis min partner dør?](specs/022-efterladte/).
Rækkefølgen og idéerne står i [roadmap.md](docs/roadmap.md) og [modning.md](docs/modning.md).

## Arbejdsgang

Hver feature følger Spec Kit: forfatning → specify → clarify → plan → tasks → implement. Spec Kit-skills
er ikke installeret i dette checkout, så trinene følges manuelt med skabelonerne i `.specify/templates`
og scripts i `.specify/scripts/powershell`.

En feature får sin egen branch (`NNN-navn`) og pull request. Den merges først, når hele suiten er
grøn, også browsertestene.

## Legacy-løsningen

`legacy/` er den oprindelige løsning. Den er kilde til domæneviden, satser med kildehenvisninger og
testcases og bruges som orakel for den nye kerne. Der bygges ikke videre på den. Kendte afvigelser
fra legacy (A1–A9) står i [docs/domaene/beregningskerne.md](docs/domaene/beregningskerne.md).

Den kan stadig køres fra `legacy/` (`start.bat` eller `py tests/test_*.py`).
Se [legacy/README.md](legacy/README.md).
