# Tasks: 013 Husstandsbalance – opsparing uden for pension (bank)

Test først (Princip IV). [P] = kan laves parallelt.

## Fase 1: Tests (røde)

- [x] T001 [P] `tests/golden/test_opsparing.py`: kernens aktiver
  - uden opsparing: identisk med før (alle års netto og det faste beløb)
  - bank i planen: det faste beløb stiger. Bufferen er aldrig negativ og ender i 0 (010)
  - urørt bank: saldo = S₀ · (1 + r)ⁿ. Afkastet er kapitalindkomst og beskattes (bundfradrag 55.000 kr.)
  - formuen krydser ældrechecks formuegrænse: ældrechecken bortfalder i præcis de år (SC-003)
  - restformue = startformue + afkast − træk (US4)
- [x] T002 [P] `tests/kontrakt/test_validering.py`: negativ saldo, ukendt type og dublet-id afvises med felt `opsparing[id]...`
- [x] T003 [P] `tests/golden/test_husstand.py`: partnerens urørte opsparing tæller i ældrechecken hos den anden
- [x] T004 [P] `tests/app/test_opsparing_app.py`: guide-JSON → kerne (`person.opsparing`, partnerens), visningens `formue` og `samlet.formue`

## Fase 2: Kerne

- [x] T005 `model.py`: `Aktiv`, `Pensionsprofil.opsparing`, `FormueAar`, `Fremskrivning.formue` og `formue_primo()`
- [x] T006 `validering.py`: aktiver
- [x] T007 `fremskrivning.py`: aktiver før tabellen, i planen (indsættes i bufferen), urørte (kapitalindkomst og formue). Advarsel om opsparing opdateres
- [x] T008 `husstand.py`: `partner_fra` bruger `formue_primo()`. `bufferens_ki_og_formue` fjernes

## Fase 3: Indgang og visning

- [x] T009 `oversaet.py`: `opsparing` for begge personer
- [x] T010 `visning.py`: `formue` (dagens kroner, restformue). `app.py`: `samlet.formue`
- [x] T011 `katalog.py`: advarselstekst

## Fase 4: Brugerflade

- [x] T012 `index.html`/`app.js`: trin 4 "Opsparing uden for pension", forventninger bliver trin 5. Feltet i trin 1 fjernes
- [x] T013 `app.js`: fold-ud "Din formue over tid" og husstandens formue under "Samlet"
- [x] T014 Browsertests: `conftest.koer_guide` og partnertests får det ekstra trin, `test_opsparing.py` (beløb ændrer hovedtallet, axe, 360 px, Pyodide = CPython)

## Fase 5: Afslutning

- [x] T015 `docs/domaene/beregningskerne.md` afsnit 7g. `ux-evaluering.md`
- [x] T016 Hele suiten og browsertests grønne. Byg siden og tjek i browseren
