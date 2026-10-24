# Tasks: Pensionsoverblik

**Input**: plan.md, spec.md, research.md, data-model.md, contracts/api.md.
**Tests**: Påkrævet (Princip IV). Test-opgaverne kommer før implementeringen i hver fase.

## Phase 1: Setup

- [ ] T001 Tilføj dependency-gruppe `app` (fastapi, uvicorn) og `httpx` i dev i `pyproject.toml`. Tilføj `src/pensionsoverblik` som pakke
- [ ] T002 [P] Tilføj kommunenavne (officielle navne fra regnearket) i `register/kommuner_2026.toml` og `register.kommunenavne(aar)`
- [ ] T003 [P] Tilføj `Aarsresultat.realfaktor` i kernen (research R4) med test

## Phase 2: Foundational

- [ ] T004 [P] Tests i `tests/app/test_oversaet.py`: guidedata → `Pensionsprofil`/`Antagelser`, inkl. partner
- [ ] T005 Implementér `src/pensionsoverblik/oversaet.py`
- [ ] T006 [P] Implementér `src/pensionsoverblik/katalog.py` (korttyper og advarselskatalog)

## Phase 3: US1 + US2 — svaret og kilderne (P1) 🎯 MVP

- [ ] T007 [P] [US1] Tests i `tests/app/test_visning.py`: hovedtal (jævn og fallback) og afrunding til 100
- [ ] T008 [P] [US2] Tests i `tests/app/test_visning.py`: kort og graf matcher kernen for 5 profiler (SC-004). Detaljer pr. år
- [ ] T009 [US1/US2] Implementér `src/pensionsoverblik/visning.py`
- [ ] T010 [P] Tests i `tests/app/test_api.py`: `/api/kommuner`, `/api/beregn` 200/422 med felt
- [ ] T011 Implementér `src/pensionsoverblik/api.py`
- [ ] T012 [US1/US2] Frontend: `static/index.html`, `app.css` (designtokens, layout efter designretningen) og `app.js` (resultatside: hero, graf, kort, tabelalternativ)

## Phase 4: US3 — guide (P1)

- [ ] T013 [US3] Frontend-guide i 3 trin med fremdrift, tilbage-knap, typeafhængige felter, (i)-forklaringer og feltfejl fra API

## Phase 5: US4 + US5 — advarsler og antagelser (P2)

- [ ] T014 [P] [US4] Tests: hver kendt advarselskode placeres som i kataloget. Ukendt kode → generel
- [ ] T015 [US4] Frontend: advarsler på kort, hero og graf
- [ ] T016 [US5] Frontend: skydeknapper (afkast, inflation, pensionsstart, opsættelse) med debounce, genberegning og "Nulstil"

## Phase 6: US6 — sådan har vi regnet (P3)

- [ ] T017 [US6] Frontend: foldbar årstabel og satsliste med kilde og status

## Phase 7: Polish

- [ ] T018 [P] Privatlivstest i `tests/app/test_privatliv.py`: ingen body i logs, ingen cookies, ingen filer skrevet
- [ ] T019 Kør appen, gennemgå siden i browseren (desktop og 360 px) og kør axe-core. Ret fund
- [ ] T020 Heuristisk evaluering (Nielsens 10) i `specs/002-pensionsoverblik/ux-evaluering.md` (FR-054)
- [ ] T021 README og CLAUDE.md: start af appen
