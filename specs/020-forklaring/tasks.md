# Tasks: 020 Forklaring

## Del 1: forenklingsregistret (før 017)

- [x] T001 [P] `tests/register/test_forenklinger.py`: markeringer ↔ register, felter, unikke id'er
- [x] T002 [P] `tests/app/test_forenklinger_app.py`: visningens `forenklinger` (anvendte markerede + altid)
- [x] T003 `register/forenklinger.toml` og `register.forenklinger()`
- [x] T004 `fremskrivning.py`: markering for opsparingens skat før første udbetaling
- [x] T005 `visning.py`: `forenklinger`
- [x] T006 `index.html`/`app.js`: fold-ud "Se vores forenklinger". Browsertest
- [x] T007 Domænedokumentet peger på registret. Hele suiten grøn

## Del 2: resten af 020a (efter 017)

- [x] T008 [P] `tests/golden/test_aarsdetaljer.py`: skat pr. type afstemmer, tillæg før modregning, formue mod grænse (SC-002)
- [x] T009 [P] `tests/app/test_forklaringer.py`: kataloget dækker inventar, registerposter og advarsler; tre niveauer; ingen beløb; LIX under 35 (SC-001, SC-005)
- [x] T010 [P] `tests/app/test_forklaring_visning.py`: årets kilder og detaljer afstemmer, ændringens årsag, hovedtallets største kilder
- [x] T011 Kernen: `Skatteberegning.fordeling`, `Aarsdetaljer` på hvert år (FR-003)
- [x] T012 `forklaringer.toml` og `forklaring.katalog()`; `app.forklaringer()`
- [x] T013 Visningen: kilder, detaljer, ændring og opsparing pr. år; hovedtallets forklaring
- [x] T014 Brugerflade: niveauvalg (huskes lokalt), "Hvordan fremkommer tallet?", "Dit år" fra grafen og tabellen
- [x] T015 `tests/browser/test_forklaring.py`: tre niveauer, niveauet huskes, afstemning, klik i grafen, under 300 ms, axe og 360 px, Pyodide = CPython

## Del 3: 020b

- [x] T016 [P] `tests/app/test_forklaring_020b.py`: hver visning og hvert kort har et emne; ordliste med tre niveauer og LIX; realfaktor i graf og formue
- [x] T017 Kataloget: læsevejledninger (hovedtal, graf, tidslinje, opsparingsgraf, faner, statusikoner, beløb), forbehold, kort → emner, ordliste
- [x] T018 Skifter mellem dagens og årets kroner (graf, tabel, opsparingsgraf, formue og kort; huskes lokalt). Hovedtallet er altid i dagens kroner
- [x] T019 "Sådan læser du …" ved hver visning; grafens nævner kun de viste serier
- [x] T020 Kortenes "i" følger niveauet; ordliste i "Sådan har vi regnet"
- [x] T021 Rulbare tabeller kan nås med tastaturet (axe scrollable-region-focusable)
- [x] T022 `tests/browser/test_forklaring_020b.py`

- [x] T023 020c: "Sådan har vi fundet forslaget" på tre niveauer med søgningens omfang og forbehold (`tests/browser/test_forklaring_020c.py`)

## Del 5: 020d
