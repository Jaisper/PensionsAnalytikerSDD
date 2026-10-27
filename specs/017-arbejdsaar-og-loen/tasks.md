# Tasks: 017 Arbejdsår og løn

## Fase 1: Tests (røde)

- [x] T001 [P] `tests/regler/test_skat_loen.py`: ligningsmæssige fradrag kun i kommune- og kirkeskat. Beskæftigelses-, job- og seniorfradrag på, under og over grænserne (håndregnet)
- [x] T002 [P] `tests/golden/test_loen.py`:
  - uden løn uændret
  - løn giver rækker fra i dag med AM-bidrag og skat
  - pensionsindbetaling fradrages og stopper ved stopalderen
  - udjævning fra stopalderen, og banken bygger bro (US2)
  - indkomsthul med advarsel
  - folkepensionist med løn: tillægget er uændret, og tillægsprocenten falder over bundfradraget (SC-004)
- [x] T003 [P] `tests/app/test_loen_app.py`: guide → kerne (`person.loen`, partnerens), `stopalder` (US3), visningens løn-kort
- [x] T004 [P] `tests/register/test_forenklinger.py` er stadig grøn med de nye markeringer

## Fase 2: Kerne

- [x] T005 Registret: nye poster og AM-bidragets kilde
- [x] T006 `regler/skat.py`: `ligningsmaessige_fradrag`. `regler/loen.py`: fradragene
- [x] T007 `model.py`: `Loen`, `Kildetype` "loen", `Fremskrivning.jaevn_fra_alder`
- [x] T008 `fremskrivning.py`: arbejdsår, skat af løn, udjævning fra stopalderen, tillægsprocent, advarsel
- [x] T009 `optimering.py`: vinduet fra `jaevn_fra_alder`
- [x] T010 `validering.py`: løn

## Fase 3: Indgang, visning og brugerflade

- [x] T011 `oversaet.py`, `visning.py` (løn-kort, hovedtal og graf fra `jaevn_fra_alder`), `katalog.py`, `app.py` (`stopalder`), `worker.js`
- [x] T012 `index.html`/`app.js`: felter i trin 1 og partnertrinnet, "Hvornår kan jeg stoppe?"
- [x] T013 Forenklingsregistret: `ingen_loen` markeret, ny forenkling for pensionsindbetaling
- [x] T014 Browsertests: løn ændrer resultatet, stopalder-søgning og "Brug denne alder", axe og 360 px, Pyodide = CPython

## Fase 4: Afslutning

- [x] T015 Domænedokument afsnit 7i, `ux-evaluering.md`, roadmap
- [x] T016 Hele suiten grøn
