# UX-evaluering: Kapitalpensionens muligheder

**Dato**: 2026-10-25 · **Metode**: browsertests (`tests/browser/test_kapitalpension.py` og
`test_optimering.py`), headless Chrome ved 1366 og 360 px, axe-core 4.9.1. Lokalt også med en
rigtig rapport (kun tal og sand/falsk er udskrevet; ingen skærmbilleder af den er gemt).

## Målinger

| Måling | Resultat | Krav |
|---|---|---|
| Kortets felter: udbetalingsform, antal år og "afgiften er allerede betalt", med hjælp under felterne | ja | FR-009 |
| Omlægning slået fra ved betalt afgift | ja (test) | US1 |
| Portioner som bjælke med greb. Grænser følger 20-årsfristen (2–16 portioner fra 65 år) | ja (test) | FR-003 |
| Forslag med formændring ("ét beløb → i portioner over 8 år") | ja | US5 |
| Find bedste plan, syntetisk / rigtig | 7,6 s / 13,1 s med statuslinje og "Afbryd" | SC-003 (4 ordninger) |
| Samme resultat i Pyodide og CPython | ja (test) | SC-004 |
| axe | 0 overtrædelser | FR-012 |
| Vandret scroll ved 360 px | nej | FR-012 |

## Heuristik (kort)

- **Klart sprog (Princip X):**
  - "Hvordan vil du have den udbetalt?" med fire valg.
  - Konsekvensen står under feltet, fx "Hver portion beskattes med 40 % afgift. Resten bliver i
    pensionen, hvor afkastet beskattes lavt (15,3 %)."
  - Omlægning siger, at den kræver en aftale med selskabet.
- **Fejlforebyggelse (5):** Valg, der ikke er lovlige (omlægning med betalt afgift), er slået fra.
  Grebet kan ikke trækkes ud over fristen.
- **Brugerkontrol (3):** "Afbryd" under en lang søgning beholder planen uændret.
- **Ærlighed:** Bufferen er ikke længere et pænt gennemsnit. Skatten af den står i tabellen
  ("Skat af buffer pr. md."), og forudsætningen står ved hovedtallet.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| G1 | Find bedste plan tager 13 s med 5 ordninger. "Afbryd" findes, men hurtigere ville være bedre (fx en hurtigere år-for-år-beregning) | 2 |
| G2 | Borgeren kan ikke vælge aktier som investering for bufferen (aktieindkomst) | 1 |
