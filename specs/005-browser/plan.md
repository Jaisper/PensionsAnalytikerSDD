# Implementation Plan: Kør i browseren

**Branch**: `005-browser` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

Hele applikationen flyttes ind i browseren. Python-koden (kerne, oversættelse, visning og
PDF-parser) køres uændret i Pyodide i en Web Worker. Et lille Python-indgangspunkt erstatter de
tre FastAPI-endpoints med samme JSON og samme fejlformat. `app.js` kalder workeren i stedet for
`fetch("/api/...")`. Et byggescript samler en statisk mappe `_site/` med HTML/CSS/JS, worker,
Pyodide-filer og låste wheels. En GitHub Action tester, bygger og udgiver på GitHub Pages.
FastAPI fjernes.

## Technical Context

- **Language/Version**:
  - Python ≥ 3.11: CPython til test, Pyodide 0.27.7 (Python 3.12) i browseren
  - JavaScript (ES2020, uden build)
- **Primary Dependencies**:
  - pdfplumber 0.11.10 og pdfminer.six 20260107, som før
  - Pyodide 0.27.7, ny og lagt i siden
  - Fjernes: fastapi, uvicorn, httpx og pydantic
- **Storage**: Ingen. Alt ligger i workerens hukommelse.
- **Testing**:
  - pytest som før
  - Ny browsertest med Playwright og headless Chromium: Pyodide sammenlignes med CPython, og
    netværket kontrolleres
- **Target Platform**: Statisk host (GitHub Pages) og moderne browsere med WebAssembly
- **Project Type**: Statisk webapp med Python-kerne i WebAssembly
- **Performance Goals**: Klar på under 8 s ved første besøg og under 3 s ved senere besøg.
  Genberegning på under 1 s.
- **Constraints**:
  - Ingen persondata over netværket
  - Ingen runtime-afhængighed af PyPI eller CDN, bortset fra Chart.js
- **Scale/Scope**: cirka 15 MB statiske filer. Én side.

## Design

### D1 Indgangspunkt `src/pensionsoverblik/app.py`

Rene funktioner. Ingen I/O og ingen `date.today()`: datoen sendes ind fra browseren (Princip VI).

```python
def kommuner() -> list[dict]
def beregn(guide: dict, idag: str) -> dict          # som /api/beregn
def pdf(data: bytes) -> dict                        # som /api/pdf
```

Fejl returneres som data og ikke som HTTP-status, så workeren kan sende dem videre:
`{"ok": True, "data": ...}` eller `{"ok": False, "fejl": {"kode", "felt", "besked"}}`. Koderne
er de samme som i dag (`ikke_pdf`, `ulaeselig`, `ingen_tekst`, `ukendt_format`, `for_stor`,
`ugyldigt_input`). Grænsen på 25 MB tjekkes både i JS, før filen sendes til workeren, og i
`pdf()`.

### D2 Worker `static/worker.js`

1. Første besked: indlæs `pyodide/pyodide.mjs` og kald
   `loadPackage([...wheel-URL'er fra py/manifest.json])`. Der bruges ingen micropip og intet PyPI.
2. Importér `pensionsoverblik.app`.
3. Protokol: `{id, op, args}` giver `{id, svar}`. Status sendes undervejs som
   `{status: "indlaeser", andel}`, som bruges til statuslinjen i US3.
4. PDF'en overføres som `ArrayBuffer` (transferable) og konverteres med `.to_bytes()`.

### D3 `app.js`

- `kald(op, args)` returnerer et Promise. `fetch("/api/kommuner" | "/api/beregn" | "/api/pdf")`
  erstattes.
- `/api/pdf/status` udgår, fordi aflæsningen altid er til stede.
- Indlæsningsbanner: "Gør beregningen klar …" med `<progress>` og `aria-live`, og "Prøv igen"
  ved fejl.
- Køen: "Beregn" før workeren er klar venter på den samme Promise (US3-2).

### D4 Byggescript `scripts/byg_side.py` (stdlib)

1. `uv build --wheel`, hvorefter projektets wheel lægges i `_site/py/`.
2. Pyodide-kernefilerne hentes fra den låste release:
   - `pyodide.mjs`
   - `pyodide.asm.js`
   - `pyodide.asm.wasm`
   - `python_stdlib.zip`
   - `pyodide-lock.json`
3. Wheels fra Pyodides lock (cryptography, cffi og pycparser) lægges i `_site/py/`.
4. Rene wheels fra PyPI (pdfminer.six, pdfplumber og charset-normalizer) hentes med `pip
   download --no-deps --only-binary=:all:` i låste versioner og lægges i `_site/py/`.
5. Alle downloads tjekkes mod en SHA-256 i `scripts/pyodide_laas.toml` (ét sted for versioner og
   hashes). Byggescriptet fejler ved afvigelse.
6. `static/*` kopieres. Script-stierne i `index.html` er relative, så siden virker under
   `/<repo>/` på Pages.
7. `py/manifest.json` får listen af wheels.

Lokalt: `uv run python scripts/byg_side.py && uv run python -m http.server -d _site 8002`.

### D5 Fjern pydantic (research R002)

`aflaeser.py` bruger `BaseModel` som ren datastruktur. Det er en rest fra AI-tiden, hvor
JSON skulle valideres. Den erstattes af `@dataclass`, hvilket fjerner pydantic, pydantic_core,
typing_extensions og annotated_types (cirka 3 MB i browseren). Konstruktion med nøgleord er
uændret.

### D6 Tests

- `tests/app/test_app.py` erstatter `test_api.py` og `test_pdf_api.py`: samme cases, men mod
  indgangspunktet. `test_graenser.py` tilpasses.
- `tests/browser/test_pyodide.py`, markeret `browser` og sprunget over, hvis `_site/` eller
  Playwright mangler:
  - **Ækvivalens:** golden case, `GUIDE` og den syntetiske rapport i Pyodide mod CPython.
    Aflæsning, hovedtal, grænser og advarsler skal være identiske. Øvrige tal må højst afvige
    10⁻⁹ relativt.
  - **Netværk (FR-003):** Et helt forløb i `index.html` med upload, guide, resultat og skyder
    logger alle requests. Efter indlæsningen må der være 0 requests, og ingen request må være
    andet end en GET af egne filer eller Chart.js.
  - **UX:** axe og 360 px på resultatsiden og indlæsningsbanneret.
- `tests/kontrakt/test_ingen_ai.py` er uændret og dækker også `worker.js`.

### D7 Udgivelse `.github/workflows/pages.yml`

Ved push til `main` og manuelt:
1. `uv sync` og `uv run pytest` (uden browser)
2. Byg siden
3. `playwright install chromium` og `pytest -m browser`
4. `actions/upload-pages-artifact` og `actions/deploy-pages`

Actions låses til versioner.

### D8 Offentligt repo

Før repoet gøres offentligt:
- `scripts/scan_historik.py` gennemgår alle commits og alle filer for CPR-mønstre med gyldig
  dato og 7.-ciffer-regel, 10-cifrede numre, kendte navne fra rigtige rapporter (gives
  lokalt som argument, ikke committet) og nøglemønstre.
- Fund ryddes med `git filter-repo`, inden der pushes.
- Selve skiftet til offentligt sker først efter brugerens bekræftelse (udadvendt handling).

## Constitution Check

| # | Princip | Gate | Status |
|---|---|---|---|
| I | Deterministisk beregning | Samme Python-kode i browseren. Ingen regler i JS. Ækvivalenstest mod CPython | [x] |
| II | Regelregister | Uændret. TOML følger med i wheel'et | [x] |
| III | Lovgivningen er facit | Ingen regelændringer | [x] |
| IV | Test først | test_app og browsertest skrives før indgangspunkt og worker | [x] |
| V | Sporbarhed | Visningen er uændret | [x] |
| VI | Isoleret kerne | `idag` gives ind fra browseren. Kernen er uændret | [x] |
| VII | Persondata | Bedre end før: intet forlader browseren. Ingen server, ingen logs. Netværkstest | [x] |
| VIII | Dansk brugerflade | Indlæsnings- og fejlbeskeder på dansk | [x] |
| IX | Simpelhed | Pyodide og Playwright begrundet nedenfor. FastAPI, uvicorn, httpx og pydantic fjernes | [x] |
| X | Brugeroplevelse | Indlæsningsbanner med status, beregning uden frysning, axe og 360 px | [x] |
| XI | Ingen persondata til AI/LLM | Ingen AI. Kontrakttest uændret | [x] |

## Project Structure

```text
src/pensionsoverblik/
  app.py                 NY: indgangspunkt (erstatter api.py)
  api.py                 SLETTES
  pdfimport/aflaeser.py  pydantic → dataclass
  static/
    index.html           relative stier, indlæsningsbanner
    app.js               kald() i stedet for fetch
    worker.js            NY
scripts/
  byg_side.py            NY
  pyodide_laas.toml      NY: versioner og SHA-256
  scan_historik.py       NY
tests/
  app/test_app.py        NY (erstatter test_api.py og test_pdf_api.py)
  browser/test_pyodide.py NY
.github/workflows/pages.yml NY
_site/                   bygget, i .gitignore
```

## Complexity Tracking

| Tilføjelse | Hvorfor | Simplere alternativ afvist |
|---|---|---|
| Pyodide (cirka 13 MB) | Kører den eksisterende Python-kerne i browseren uden server | En JS-omskrivning ville give to implementeringer af reglerne (Princip I). Det var en server, der forhindrede brugen af en statisk host |
| Web Worker | Beregningen tager cirka 200 ms og opstarten cirka 3 s. I hovedtråden ville skyderne fryse | Hovedtråden er afvist på grund af frysning (Princip X) |
| Playwright (kun dev og CI) | Den eneste måde at bevise, at browseren regner som CPython, og at intet sendes | Node med Pyodide tester ikke den rigtige worker og det rigtige netværk |
