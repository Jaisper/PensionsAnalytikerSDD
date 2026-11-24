# Tasks: 039 Metodebeskrivelsen i løsningen

- [x] T001 Spec og afklaring (2026-11-24)
- [x] T002 Test først: konvertering og "ingen kodenavne" (røde mod den umarkerede tekst: 105 linjer)
- [x] T003 Konverter i `scripts/metode_html.py` (kun standardbiblioteket) og byggetrin i `byg_side.py`
- [x] T004 Markér det tekniske i `docs/metode.md`; blokmarkeringer på egne linjer af hensyn til GitHub
- [x] T005 Siden: indholdsfortegnelse efter titlen, læsbare tabeller, CSP, links fra sidefod og metodeside
- [x] T006 Browsertest: åbnes fra forsiden, ingen CSP-overtrædelser, axe og 360 px
- [x] T007 (039b) Ny fane fra beregningen, "Tilbage til beregningen" lukker fanen; beregningen bliver stående (testet)

## Fund undervejs

- En markering i starten af en linje gør linjen til rå HTML på GitHub (overskrift og fed skrift vises ikke).
  Blokmarkeringer står derfor på egne linjer med tomme linjer omkring.
- Tabeller og formler, der kan rulle vandret, skal kunne nås med tastaturet (`tabindex="0"`, axe).
- 039b: Siden åbnes i en ny fane fra beregningen (`?fra=beregning`), og "Tilbage til beregningen" lukker fanen.
  Knappens script ligger på sidens egen adresse, så CSP'en er nu `script-src 'self'`.
