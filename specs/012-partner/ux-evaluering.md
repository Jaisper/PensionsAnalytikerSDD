# UX-evaluering: Partner

**Dato**: 2026-10-25 · **Metode**: browsertests (`tests/browser/test_partner.py`), headless Chrome
og lokalt med en rigtig rapport indlæst som partner (kun sand/falsk udskrevet).

| Måling | Resultat | Krav |
|---|---|---|
| Guiden får trinnet "Din partners ordninger" kun ved "Hele din partners pension" | ja (test) | US1 |
| Partnerens rapport udfylder kun partneren (id'er p1, p2, …) | ja (test) | US1 |
| Fanerne Dig/Partner/Samlet, betjenes med piletaster | ja (test) | FR-006 |
| Træk under Partner ændrer kun partneren, og fanen bliver valgt | ja (test) | US2 |
| Samlet er lig dit beløb plus partnerens (syntetisk og rigtig rapport) | ja | SC-003 |
| Ændring → nye tal for to profiler | 0,43 s (inkl. 300 ms pause) | SC-005 < 2 s |
| Samme resultat i Pyodide og CPython | ja (test) | SC-004 |
| axe (Samlet) og 360 px | 0 fejl, ingen scroll | FR-008 |

## Heuristik (kort)

- **Synlighed og mærkning:** Overskriften siger "Du kan …", "Din partner kan …" eller "I kan
  forvente ca.". Hero, overblik og links følger fanen.
- **Konsistens:** Under Partner er det de samme komponenter som under Dig (graf, buffer,
  tidslinje, Find bedste plan).
- **Overblik:** Samlet viser først jeres samlede beløb og hvert beløb for sig. Derefter kommer
  grafen pr. kalenderår, hvor de to personer har hver sin farve, og den fælles tidslinje.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| P1 | Den fælles tidslinje er placeret i procent af aksen og flugter ikke pixel for pixel med grafens søjler | 1 |
| P2 | Under Samlet kan der ikke redigeres. Man skifter til Dig eller Partner | 1 |
