# Implementation Plan: 035 Branchestandard

**Branch**: `035-branchestandard` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md) |
**Dato**: 2026-11-04

## Overblik

Branchestandarden er et lag **før** den eksisterende fremskrivning. Kernen finder tre afkaststier pr.
ordning (trin 1–2) og kører derefter den uændrede `beregn` tre gange, én gang pr. sti (trin 3). Skat,
ydelser, udjævning og optimering er dermed de samme på alle tre forløb (FR-006), og med `egne`
kører præcis den samme kode som i dag (SC-001).

## Tekniske beslutninger

### Kerne (`src/pensionskerne/`)

- **`model.py`**:
  - `Antagelser.beregningsgrundlag: Literal["egne", "branchestandard"] = "egne"`. Standarden i
    kernen er `egne`, så alle eksisterende kald og golden cases er uændrede. Brugerfladen vælger
    `branchestandard` for nye input (US1).
  - `Ordning.afkast_forloeb: Mapping[int, float]` (pr. kalenderår, efter PAL og
    investeringsomkostninger) overstyrer `Antagelser.afkast_i_aar` for den ordning. Tom = som i dag.
  - `Ordning.portefoelje: Portefoeljeskoen | None` med aktieandel, kilde (`skoen`, `standard`,
    `angivet`, `selskab`) og kalibreringsafvigelse.
  - `Ordning.gebyr_pr_aar: float = 0.0` er den faste administrationsomkostning i dagens kroner.
    Den trækkes i depotet hvert år og reguleres med inflationen (henstillingen pkt. 7.2).
  - `Fremskrivning.prognose: dict[str, Fremskrivning] | None` med nøglerne `hoej`, `forventet` og
    `lav`. Hovedresultatet er `forventet`.
- **`prognose.py`** (nyt, rene funktioner):
  - `forudsaetninger(opslag) -> Forudsaetningssaet` læser Rådets sæt fra registret.
  - `portefoelje_vaegte(aktieandel, aar_fra_nu)` mapper til klasse 1/5 (år 1–10) og
    obligationer/aktier (år 11+).
  - `mu_sigma(vaegte, periode)`.
  - `trin1(depot, praemier, faktorer, mu, sigma) -> (M, V)`.
  - `fraktil(M, V, p)`.
  - `trin2(...) -> dict[str, list[float]]` giver de tre stier. Når depotet løber tør, bruges det
    seneste beregnelige afkast (R1).
  - `trin3_afkast(sti, pal)` omregner stien til afkast efter PAL.
- **`kalibrering.py`** (nyt):
  - `kalibrer_aktieandel(ordning, selskabsprognose, ...)` er en bisektion på [0, 1] med tolerance
    0,1 procentpoint og højst 40 iterationer (FR-012). Den giver aktieandelen og afvigelsen.
  - Ratepension og aldersopsparing kalibreres først. En livsvarig ordning hos samme selskab og med
    samme investeringsform arver skønnet.
  - Gennemsnitsrente kalibrerer et fladt afkast (σ = 0), der genskaber selskabets prognose
    (FR-014). Så er høj = lav = forventet, og kun forventet vises.
- **`fremskrivning.py`**:
  - `afkast_i(alder)` får ordningen med og bruger `ordning.afkast_forloeb`, før den falder tilbage
    på det fælles forløb.
  - `gebyr_pr_aar` trækkes i ordningens depot.
  - `beregn` med `branchestandard`: Prognoselaget bygger tre profiler med forløb og kalder den
    eksisterende fremskrivning tre gange.
- **Inflation (forenkling `branchestandard_en_inflation`)**:
  - v1 bruger én inflation for hele forløbet: Rådets langsigtede 2,0 % (år 11+). Den bruges både
    til satsregulering og til dagens kroner.
  - Rådets 1,8 % for år 1–10 påvirker kun afkastet via de nominelle afkast.
  - En inflation pr. år kræver et kumuleret indeks i `Regelopslag` og er en senere udvidelse. Den
    står i forenklingsregistret og i forklaringen.
- **Livsvarige forløb**: Med `branchestandard` bliver livrentens horisont pensionsalderen plus
  Finanstilsynets forventede restlevetid (benchmark i registret) i stedet for 90 år. Med `egne` er
  den uændret.
- **Bufferen og frie midler**: Følger fortsat `Antagelser.afkast_efter_pal` (forventet forløb). De er
  ikke pensionsordninger og er ikke omfattet af henstillingen (forenkling
  `branchestandard_buffer_fast_afkast`).

### Register (`register/`)

- Rådets sæt for 1. halvår 2027 som poster `raadet.*` i `2026.toml` (registret læser én fil pr. satsår):
  - afkast pr. periode og aktivklasse
  - standardafvigelser og korrelationsmatrix
  - investeringsomkostninger og inflation
  - kilde, udgivelsesdato (2.11.2026) og status `verificeret`
- Et nyt sæt erstatter posterne med ny kilde og dato. Udgivelsesdatoen vises i brugerfladen.
- Nye antagelser i `2026.toml`:
  - `branchestandard.standardprofil` (aktieandel pr. år til pension med begrundelse)
  - `branchestandard.gebyr_pr_aar`
  - `branchestandard.kalibrering_tolerance`
  - `levetid.benchmark_restlevetid` (Finanstilsynet, med kilde)
- `forenklinger.toml`:
  - `kalibrering_opsuger_omkostninger`
  - `kalibrering_opsuger_levetid`
  - `kalibrering_ingen_nedtrapning`
  - `branchestandard_en_inflation`
  - `branchestandard_buffer_fast_afkast`
  - `gennemsnitsrente_som_fladt_afkast`

### PDF-import (FR-015, `src/pensionsoverblik/pdfimport/`)

- Pr. produkt bevares den forventede udbetaling (beløb pr. år, form, startalder og udbetalingsår),
  før den omregnes til en nutidsværdi.
- Investeringsformen aflæses ("Markedsrente", "Gennemsnitsrente", "Flere investeringsformer",
  "Ingen oplysninger"). Ukendt tekst giver "Ingen oplysninger".
- Den syntetiske rapport udvides med investeringsform og en ratepension og en livrente hos samme
  selskab (US4).

### Indgangslag og brugerflade (`src/pensionsoverblik/`)

- `oversaet.py`: `antagelser.beregningsgrundlag`. Gemte input uden feltet bliver `egne` (US1-3).
  Nye guide-input bliver `branchestandard`. Aktieandel pr. ordning (angivet af dig).
- `visning.py`: De tre niveauer i hovedtallet og grafen. Benævnelserne kommer fra kataloget (FR-007).
  Porteføljeskønnet og kilden pr. ordning. Sammenligningen med selskabets prognose (US4).
- `app.js` og `index.html`:
  - Skifteren over hovedtallet.
  - Grafens tre forløb skelnes med linjetype og tekst (FR-010). Den eksisterende ±-vifte (018)
    erstattes af de tre forløb, når branchestandarden er valgt.
  - Aktieandelen kan rettes i ordningens detaljer.
- `forklaringer.toml`: Emnerne `beregningsgrundlag`, `prognose_niveauer`, `tretrinsmetoden`,
  `raadets_forudsaetninger`, `portefoelje_skoen` og `sammenligning_selskab`. Henstillingens tekst om
  usikkerhed (appendix 2) tilpasses til efter skat. Det skal fremgå, at det er en branchestandard og
  ikke lov.
- `katalog.py`: Advarsler for kalibreringsgrænse (0 % eller 100 %) og stor afvigelse mod selskabets
  prognose.

### 016 Monte Carlo

- 016's spec markeres som erstattet af 035 for usikkerhedsviften (clarify 2026-11-04).

## Constitution Check (1.2.0)

| Princip | Vurdering |
|---|---|
| I. Deterministisk beregning | ✅ Analytisk metode, bisektion med fast tolerance og iterationer. Ingen tilfældighed |
| II. Regelregister | ✅ Rådets sæt, profiler, gebyr og benchmark i registret med kilde og status |
| III. Lovgivningen er facit | ✅ Henstillingen er branchestandard og står sådan. Forenklinger i registret |
| IV. Test først | ✅ Bilag 2 som golden case før koden (SC-002). Rundturstest for kalibreringen (SC-007) |
| V. Sporbarhed | ✅ Porteføljens kilde og kalibreringsafvigelse følger ordningen og vises |
| VI. Isoleret kerne | ✅ Prognoselaget er i kernen. Visningen formaterer kun |
| VII. Persondata | ✅ Intet nyt forlader browseren. PDF-importen skriver intet til disk |
| VIII. Dansk brugerflade | ✅ Branchens benævnelser + "efter skat" |
| IX. Simpelhed | ⚠️ Stor feature. Opdelt i faser, og `egne` er uændret |
| X. Brugeroplevelse | ✅ Én skifter. Tre niveauer med mønster og tekst |
| XI. Ingen persondata til AI | ✅ Ingen AI. FR-009 venter på 026 og bruger kun kataloget |

## Faser

1. **Trin 1–2 i kernen** mod bilag 2 (SC-002). Rådets sæt i registret.
2. **Trin 3 og tre forløb**: per-ordning-forløb, gebyr og `prognose` i `Fremskrivning`. Golden
   cases for rate, livsvarig og aldersopsparing (SC-003). `egne` uændret (SC-001).
3. **PDF-import** (FR-015) og **kalibrering** med rundturstest (SC-007).
4. **Brugerflade**: skifter, tre niveauer, porteføljeskøn, sammenligning og forklaringer.
5. **Browser og ydelse**: Pyodide = CPython (SC-006), under 2 s (SC-005).

## Risici

- **Ydelse**: Tre fulde fremskrivninger pr. beregning, og optimeringen bruger kun det forventede
  forløb. Høj og lav regnes først efter optimeringen. Det måles i fase 5. Er det for langsomt,
  regnes høj og lav i en separat besked fra workeren.
- **Selskabets prognose ved én alder**: Se research. US4 kan blive en sammenligning på tværs af
  ordninger.
- **Rigtige rapporter**: Investeringsformens ordlyd verificeres lokalt med
  `PENSIONSINFO_RAPPORT=<sti> uv run pytest -k rigtig`. Intet fra rigtige rapporter committes.
