# UX-evaluering: Afkast pr. år og "dårlige år først" (023a)

**Dato**: 2026-10-28 · **Metode**: browsertests (`tests/browser/test_usikkerhed.py`), headless Chrome.

| Måling | Resultat | Krav |
|---|---|---|
| "Dårlige år først" og "Gode år først" står i tabellen med årenes afkast og "derefter" dit valg | ja (test) | FR-003 |
| Alle scenarier (nu ti) er regnet under 3 s efter resultatet | ja (test) | 018 SC-004 |
| Samme tal i browseren som i CPython | ja (test) | Princip IX |
| Spændet ved hovedtallet er uændret (kun afkast og inflation) | ja (kode og test) | 018 |
| axe og 360 px | 0 fejl | Princip X |

## Heuristik (kort)

- **Ærlighed**: Introteksten siger, at det er de to første år efter, du går på pension, og at tallene
  er eksempler. Forklaringen nævner kilden og at livrenten ikke følger årets afkast.
- **Forståelse**: Rækken viser den konkrete procent og årstallene, så borgeren kan se, hvor
  voldsomt det er.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| A1 | "Gode år først" er ofte lig "Dit valg", fordi det første år er det laveste. Overvej at forklare det i rækken | 2 |
| A2 | Stress-størrelsen kan ikke ændres af borgeren | 1 |
| A3 | Afkast pr. aktivtype mangler (023b) | 1 |
