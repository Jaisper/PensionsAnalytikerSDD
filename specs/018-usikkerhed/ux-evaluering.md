# UX-evaluering: Usikkerhed om afkast og inflation

**Dato**: 2026-10-26 · **Metode**: browsertests (`tests/browser/test_usikkerhed.py`), headless Chrome,
og en lokal måling med syntetiske data.

| Måling | Resultat | Krav |
|---|---|---|
| Spændet under hovedtallet ("mellem X og Y kr.") med link til tabellen | ja (test) | US1 |
| Tabellen har syv rækker: dit valg og seks scenarier | ja (test) | US1 |
| Spænd og tabel følger fanen Dig/Partner/Samlet | ja (test) | US1 |
| En ny beregning afbryder de gamle scenarier | ja (test) | US2 |
| Samme beløb i Pyodide og CPython | ja (test) | SC-003 |
| Seks scenarier i browseren | enlig 0,31 s, par 0,87 s | SC-004 < 3 s |
| axe (med åben tabel) og 360 px | 0 fejl, ingen scroll | FR-005 |

## Heuristik (kort)

- **Synlighed:** Usikkerheden står lige under tallet, den handler om, og ikke kun i en
  fold-ud længere nede.
- **Ærlighed:** Teksten siger, at tallene er eksempler og ikke grænser, og den nævner
  spændenes størrelse (Princip V).
- **Respons:** Spændet viser "Regner …", indtil scenarierne er færdige. Resultatet vises først
  og bliver aldrig forsinket af usikkerheden.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| U1 | Scenarierne ændrer afkast og inflation i alle år på én gang. Udsving fra år til år (sekvensrisiko) kræver 016 (Monte Carlo) | 1 |
