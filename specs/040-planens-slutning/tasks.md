# Tasks: 040 Planens slutning og penge tilbage

- [x] T001 Golden cases: randbetingelsen i `beregn_jaevn` (håndregnet) og i `beregn` (bufferen ender på X i dagens
      kroner, beløbet falder, advarsel ved for stort beløb, validering) — `tests/golden/test_rest_ved_slut.py`
- [x] T002 Kerne: `Antagelser.rest_ved_plan_slut`, `beregn_jaevn(rest_slut=...)`, fremskrivning, validering, advarsler
- [x] T003 App-tests: oversættelse (dig og partner), prisen, relative levetidsscenarier —
      `tests/app/test_planens_slutning_app.py`
- [x] T004 App: `oversaet` (partnerens egne værdier), `beregn` (prisen), `scenarier`/`scenarie` relativt
- [x] T005 Browsertest: felterne i guiden og under "Prøv andre forudsætninger", prisen og par —
      `tests/browser/test_planens_slutning.py`
- [x] T006 UI: trin 5, resultatsiden, prislinjen, usikkerhedstabellen, antagelseslisten
- [x] T007 Dokumentation: `docs/metode.md`, forklaringer

## 040b Ratepension efter planens slutning (fejl, 2026-11-26)

Produktejeren: "beder om at pengene skal stoppe ved 80 år, men den regner alligevel til 84". En ratepension
udbetalt efter slutalderen forlængede planen i stilhed. Valgt: opsparingen er brugt op ved den valgte alder;
årene efter er årets egen indkomst, og en besked forklarer det.

- [x] T020 Golden: `tests/golden/test_udbetaling_efter_plan.py` (håndregnet udjævning, rest ved slutalderen)
- [x] T021 `jaevn.beregn_jaevn(plan_raekker=…)`, `Fremskrivning.jaevn_til_alder`, beskeden `UDBETALING_EFTER_PLAN`
- [x] T022 Hovedtal, forbrugsprofil, "Find bedste plan" og prisen ser kun på årene i planen (app-test)
- [x] T023 Forklaring og `docs/metode.md` afsnit 6.1
