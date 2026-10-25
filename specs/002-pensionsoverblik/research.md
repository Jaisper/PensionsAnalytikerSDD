# Research: Pensionsoverblik

**Feature**: [spec.md](spec.md) · **Dato**: 2026-10-24

## R1. Arkitektur (brugerens valg 2026-10-24)

- **Beslutning**: Lille FastAPI-server, der kalder `pensionskerne.beregn`, og en statisk
  frontend (HTML/CSS/JS uden build-trin). Serveren er stateless: input lever kun i
  requesten.
- **Begrundelse**:
  - Enkelt at bygge og drive.
  - De kommende features (PDF-import og AI) kræver alligevel en server.
  - Kernen genbruges uændret.
- **Forkastet**:
  - Pyodide: 10 MB opstart, og senere features kræver server alligevel.
  - HTMX: øjeblikkelig opdatering ved skydeknapper bliver besværlig.

## R2. Afhængigheder (Princip IX)

| Afhængighed | Hvorfor | Alternativ forkastet |
|---|---|---|
| `fastapi` + `uvicorn` | HTTP-API og validering af JSON | `http.server`: ingen validering og mere egen kode |
| `httpx` (dev) | FastAPI's `TestClient` | — |
| Chart.js 4.4.1 (cdnjs, pinnet) | Stablede søjler og tooltips. Ét bibliotek | Håndskrevet SVG: mere kode |

Kernen forbliver uden afhængigheder. App-afhængighederne ligger i en separat
dependency-gruppe (`app`).

## R3. Hovedtallet

- **Beslutning**: Hovedtallet er `jaevn.niveau_real / 12`, afrundet til nærmeste 100 kr. med
  "ca.". Findes der ingen jævn udbetaling, bruges netto i det første hele år med
  folkepension i dagens kroner.
- **Begrundelse**: Svarer på "hvad får jeg om måneden" med ét stabilt tal i dagens
  købekraft. Legacy brugte samme begreb, men viste det midt i en tabel.

## R4. Dagens kroner i grafen

- **Problem**: Kernen leverer `netto_real` pr. år, men ikke pr. kilde. At deflatere i
  brugerfladen ville være beregning (FR-001).
- **Beslutning**: Kernen får et nyt felt `Aarsresultat.realfaktor` (en MINOR
  kontraktudvidelse). Visningslaget ganger kun med kernens faktor.

## R5. Privatliv (Princip VII)

- Request-bodies logges ikke. Access-loggen viser kun metode og sti.
- Der er ingen cookies, ingen session på serveren og ingen tracking. Det eneste eksterne
  script er en pinnet Chart.js fra cdnjs.
- Guidens første trin fortæller, at oplysningerne kun bruges til beregningen og ikke gemmes.

## R6. Tilgængelighed og verifikation

- **Automatisk**: axe-core køres i browseren mod resultatsiden (SC-003).
- **Heuristisk evaluering**: Nielsens 10, dokumenteret i `ux-evaluering.md` (FR-054).
- **Graf**: Grafen har en `<table>` som alternativ (FR-023). Lærredet får `role="img"` og
  en beskrivende `aria-label`.

## R7. Visuel identitet

Følger [docs/ux/designretning.md](../../docs/ux/designretning.md): petrol som primærfarve,
sand som accent og faste kildefarver. Velliv er kun inspiration til layoutet.

## R8. Pensionsstart som skydeknap (FR-041)

Kernen har en startalder pr. ordning. Skydeknappen "Private ordninger starter som" sætter
samme startalder for alle løbende ordninger. Er den ulovlig for en ordning, vises kernens
valideringsfejl ved skydeknappen, og den forrige værdi bevares.
