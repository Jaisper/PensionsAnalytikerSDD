# Tasks: Kør i browseren

## Fase 1: Forberedelse

- [x] T001 Erstat pydantic med dataclasses i `pdfimport/aflaeser.py` (D5). Hele suiten skal være grøn, og pydantic fjernes fra afhængighederne
- [x] T002 [P] `scripts/pyodide_laas.toml`: Pyodide 0.27.7 og wheels med versioner og SHA-256

## Fase 2: Indgangspunkt (US1)

- [x] T003 Test først: `tests/app/test_app.py` med cases fra `test_api.py` og `test_pdf_api.py` mod `app.kommuner/beregn/pdf`, inklusive fejlformat og 25 MB. Testen skal være rød
- [x] T004 Implementér `src/pensionsoverblik/app.py` (D1). T003 skal være grøn
- [x] T005 Flyt `test_graenser.py` til indgangspunktet. Slet `api.py`, `test_api.py` og `test_pdf_api.py`, og fjern fastapi, uvicorn og httpx

## Fase 3: Byg og worker (US1, US2)

- [x] T006 `scripts/byg_side.py` (D4) med hash-tjek. `_site/` i .gitignore
- [x] T007 Test først: `tests/browser/test_pyodide.py` med ækvivalens mod CPython (golden case, GUIDE og syntetisk rapport) og netværkskontrol. Testen skal være rød
- [x] T008 `static/worker.js` (D2) og `kald()` i `app.js` (D3). Relative stier i `index.html`. T007 skal være grøn

## Fase 4: Indlæsning (US3)

- [x] T009 Indlæsningsbanner med statuslinje, kø for "Beregn", fejl med "Prøv igen" og besked uden WebAssembly
- [x] T010 Gennemgang i headless Chrome: første og andet besøg (tider mod SC-002), skydere (SC-003), axe og 360 px

## Fase 5: Udgivelse (US2)

- [x] T011 `.github/workflows/pages.yml` (D7)
- [x] T012 `scripts/scan_historik.py` (D8). Kør på hele historikken og rapportér fund til brugeren
- [x] T013 **Kræver brugerens bekræftelse:** ryd eventuelle fund, gør repoet offentligt, slå Pages til og verificér den udgivne side

## Fase 6: Afslutning

- [x] T014 README, CLAUDE.md (kommandoer uden uvicorn), research R002 og UX-evaluering
- [x] T015 Kortere opstart: PDF-læseren hentes efter opstart (research R005)
