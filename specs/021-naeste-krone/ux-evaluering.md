# UX-evaluering: Hvor skal næste krone hen?

**Dato**: 2026-10-27 · **Metode**: browsertests (`tests/browser/test_naeste_krone.py`), headless Chrome.

| Måling | Resultat | Krav |
|---|---|---|
| Fire alternativer med fast beløb, forskel, skattefordel nu og skat og mindre tillæg senere | ja (test) | US1, FR-003 |
| Tid for sammenligningen i browseren | 0,56 s | SC: under 3 s |
| Ratepensionsfælden forklares med borgerens tal, når aldersopsparing giver mere | ja (app-test) | US2 |
| Loftet vises som "loftet er nået" for aldersopsparing og aktiesparekonto | ja (app-test) | US3 |
| Uden løn beder siden om lønnen | ja (test) | – |
| axe med resultatet | 0 fejl | Princip X |

## Heuristik (kort)

- **Ærlighed**: Teksten siger, hvordan alternativerne er gjort sammenlignelige (samme løn efter
  skat), at alle typer har samme afkast, og at det er et regnestykke, ikke et råd.
- **Målet** er det faste beløb i gennemsnit fra stopalderen, ikke hovedtallet (det laveste niveau).
  Det står i omfangsteksten.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| N1 | En engangsindbetaling er ikke med endnu (variant i spec'en) | 1 |
| N2 | Afdrag på lån kommer med 014 | 1 |
| N3 | Har borgeren få år til stopalderen, er forskellene små og afrundes til hele kroner. Overvej at vise dem over hele perioden | 2 |
