# UX-evaluering: Arbejdsår og løn

**Dato**: 2026-10-27 · **Metode**: browsertests (`tests/browser/test_loen.py`), headless Chrome,
og en lokal måling med syntetiske data.

| Måling | Resultat | Krav |
|---|---|---|
| Løn og stopalder i "Om dig" er valgfrie. Uden dem er resultatet uændret | ja (test, golden) | US1, SC-001 |
| Kortet "Løn" og det faste beløb fra stopalderen | ja (test) | US1, FR-004 |
| Banken bygger bro fra stop til første udbetaling. Indkomsthul giver en advarsel | ja (golden) | US2, SC-003 |
| "Hvornår kan jeg stoppe?" svarer og oplyser søgningens omfang. "Brug X år" sætter stopalderen og regner forfra | ja (test) | US3, FR-007 |
| Uden løn beder vi om lønnen | ja (test) | US3 |
| Folkepensionist med løn: tillægget er uændret, og tillægsprocenten falder | ja (golden) | US4, SC-004 |
| Samme svar i Pyodide og CPython | ja (test) | SC-005 |
| "Hvornår kan jeg stoppe?" i browseren (seks aldre) | enlig 0,18 s, par 0,45 s | SC-006 < 5 s |
| axe (med svar) og 360 px | 0 fejl, ingen scroll | FR-010 |

## Heuristik (kort)

- **Valgfrit og forklaret:** Lønfeltet siger, hvad borgeren får ud af at udfylde det.
  Stopalderen har en standard (folkepensionsalderen).
- **Kontrol:** "Brug X år" ændrer kun stopalderen. Borgeren ser det nye resultat med det samme
  og kan rette alderen i "Dine oplysninger".
- **Ærlighed:** Når ønsket ikke kan nås, siger svaret det og viser det højeste mulige beløb.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| A1 | Stopalderen kan ikke trækkes på tidslinjen som ordningerne | 1 |
| A2 | "Hvornår kan jeg stoppe?" findes kun for dig, ikke for partneren | 1 |
| A3 | Partnerens deltidsløn kan ikke angives (kun løn og stopalder) | 1 |
