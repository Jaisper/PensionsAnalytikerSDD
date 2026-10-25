# Tasks: Find bedste plan og engangsbeløb som buffer

## Kerne (US1)

- [ ] T001 Test først: `tests/optimering/test_optimering.py` og egenskabstest. Testene skal være røde
- [ ] T002 `pensionskerne/optimering.py`: mål, værn, søgerum, søgning og fremdrift. T001 skal være grøn
- [ ] T003 Mål hastigheden i CPython og Pyodide, og sæt `maks_evalueringer` efter SC-003

## Indgang og worker

- [ ] T004 Test først: `app.optimer` i `tests/app/test_app.py`. Planen anvendt giver hovedtal lig `efter`
- [ ] T005 `app.optimer`, fremdrift i workeren og `kald(..., vedFremdrift)`

## Brugerflade (US1, US2)

- [ ] T006 Test først: `tests/browser/test_optimering.py`
- [ ] T007 "Find bedste plan", forslagsboks, spøgelsesbjælker, "Anvend"/"Behold" og forældede svar
- [ ] T008 "Brug som buffer" i guiden og datapanelet. Punkt eller ring i tidslinjen
- [ ] T009 Gennemgang i headless Chrome med syntetisk og rigtig rapport (lokalt): tid (SC-003), axe og 360 px

## Afslutning

- [ ] T010 Domænedokument (legacy-afvigelser for optimeringen), research, UX-evaluering og README
