# Tasks: Indlæsning af PensionsInfo-rapport

**Tests**: Påkrævet (Princip IV). De skrives før implementeringen.

- [x] T001 Afhængigheder `pdfplumber` og `anthropic` i gruppe `app`
- [x] T002 [P] Tests `tests/app/test_pdf_tekst.py`: CPR-fjernelse, århundrede-reglen, sidefilter, tom tekst → fejl (US3, FR-002)
- [x] T003 [P] Tests `tests/app/test_pdf_omsaet.py`: alle kategorier, ATP, folkepension og forsikring ignoreres, periode → antal år, oprettelse udledt, afgift betalt, manglende saldo og startalder (US2, SC-004)
- [x] T004 [P] Tests `tests/app/test_pdf_api.py`: status, samtykke, ikke-PDF, for stor fil, scannet PDF, succes med falsk aflæser, ingen filer skrevet, ingen CPR i den sendte tekst (US1, US3, SC-002, SC-003)
- [x] T005 Implementér `pdfimport/tekst.py`
- [x] T006 Implementér `pdfimport/omsaet.py`
- [x] T007 Implementér `pdfimport/aflaeser.py` (skema og ClaudeAflaeser)
- [x] T008 Endpoints `GET /api/pdf/status` og `POST /api/pdf` i `api.py`
- [x] T009 Frontend: upload-kort med samtykke, fremdrift, fejl, udfyldning og usikkerheder
- [x] T010 Gennemgang i headless Chrome (desktop og mobil), axe-core
- [x] T011 Docs: README, CLAUDE.md og domænegrundlag (legacy-afvigelser rettet)

## Status 2026-10-24

- Alle opgaver gennemført. 32 nye tests (tekst og CPR, omsætning, API, skema).
- Browsergennemgang mod testserver med falsk aflæser: samtykke, fremdrift, udfyldning,
  usikkerheder, validering og beregning virker. axe-core: 0 overtrædelser. Ingen vandret scroll
  ved 360 px.
- **Ikke testet:** et live-kald mod Claude (ingen nøgle i miljøet) og rigtige PensionsInfo-rapporter.
  Skal verificeres manuelt med `ANTHROPIC_API_KEY` sat og en rigtig rapport, før funktionen bruges.
