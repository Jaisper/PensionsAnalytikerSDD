# Tasks: 030 Stopalderen følger første udbetaling

- [x] T001 Test først: `tests/golden/test_stopalder_foelger.py`, ændrede golden cases i `tests/optimering/test_pensionsalder.py` (begrundet i docstring), `tests/app/test_graenser.py` (`aktuel`), `tests/app/test_naeste_krone_app.py` og `tests/browser/test_stopalder_graf.py` (punktet følger første udbetaling). Røde før ændringen
- [x] T002 `model.stopalder` og `bruges_i_fast_beloeb`; fremskrivning og validering bruger den (FR-001, FR-002)
- [x] T003 Optimeringen holder den udledte stopalder fast og afviser kandidater med en anden første udbetaling (FR-003)
- [x] T004 "Næste krone" og `graenser()["stopalder"]["aktuel"]`; punktet i tidslinjen (025) viser den udledte stopalder (FR-002)
- [x] T005 Hjælpetekst ved feltet og forklaringen til den bedste plan (FR-004)
- [x] T006 Hele suiten grøn, også browsertestene
