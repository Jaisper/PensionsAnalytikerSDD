# Tasks: Kapitalpensionens muligheder og en realistisk buffer

## Fase 1: Lovgrundlag og skat

- [x] T001 Registret: 4 nye poster (D1) med kilde og status
- [x] T002 Test først: `tests/regler/test_skat_kapitalindkomst.py` (golden, regnet i hånden fra PSL)
- [x] T003 `beregn_skat(pi, ki, ...)` med bundfradrag og skatteloft for kapitalindkomst

## Fase 2: Kapitalpensionens former (US1–US3)

- [x] T004 Test først: `tests/golden/test_kapitalpension_former.py`
- [x] T005 Model, validering og planer: `afgift_betalt`, `udbetalingsform` (portioner, ratepension, livsvarig) og advarsler

## Fase 3: Realistisk buffer (US4)

- [x] T006 Test først: `tests/golden/test_buffer_realistisk.py`
- [x] T007 `_aar_for_aar(KI, F)`, fastpunkt, `beregn_jaevn` med brutto-rente, `skat_kapitalindkomst`, og `buffer_kapitalskat` fjernet. Golden-ændringer begrundes

## Fase 4: Indgang, PDF og visning

- [x] T008 Test først og implementering: `oversaet`, `omsaet` (PDF), `graenser` og visning (tabel og engangsbeløb)

## Fase 5: Optimering (US5)

- [x] T009 Test først og implementering: formdimension, `Plan.form`, `anvend` og `app.optimer`. Mål hastigheden (SC-003)

## Fase 6: Brugerflade

- [x] T010 Test først: `tests/browser/test_kapitalpension.py`
- [x] T011 Kortets felter, tidslinjen, markører for portioner, forslagstekst og antagelsesliste
- [x] T012 Gennemgang med syntetisk og rigtig rapport (lokalt): axe, 360 px og tider

## Fase 7: Afslutning

- [x] T013 Domænedokument (afvigelser og forenklinger), UX-evaluering, README og CLAUDE.md
