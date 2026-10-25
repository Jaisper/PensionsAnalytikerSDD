# UX-evaluering: Find bedste plan og engangsbeløb som buffer

**Dato**: 2026-10-25 · **Metode**: browsertests (`tests/browser/test_optimering.py`), headless
Chrome ved 1366 og 360 px, axe-core 4.9.1. Lokalt også med en rigtig rapport (ingen
skærmbilleder af den er gemt).

## Målinger

| Måling | Resultat | Krav |
|---|---|---|
| Optimering i browseren, syntetisk / rigtig rapport | 3,3 s / 3,5 s | SC-003 < 10 s |
| Samme forslag i Pyodide og CPython | ja (test) | SC-002 |
| Efter "Anvend" er det faste beløb lig forslagets | ja (test) | SC-004 |
| axe med forslag vist | 0 overtrædelser | FR-009 |
| Vandret scroll ved 360 px | nej | FR-009 |

## Heuristik (kort)

- **Synlighed (1):** Statuslinjen viser fremdriften. Forslaget siger, hvor meget mere, før og
  efter, og præcis hvad der flyttes.
- **Brugerkontrol (3):** Intet ændres, før borgeren trykker "Anvend". "Behold min plan" og
  enhver egen ændring fjerner forslaget.
- **Genkendelse (6):** De stiplede bjælker viser forslaget på samme tidslinje, som borgeren
  selv trækker i.
- **Ærlighed:** "Vi har afprøvet 889 af 16,6 mio. mulige kombinationer – de mest lovende, men
  ikke alle."
- **Buffer-valget** står ved engangsbeløbet med en forklaring under feltet. Tidslinjen viser
  et udfyldt punkt ("til buffer") eller en ring ("udbetales direkte").

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| E1 | "Fast beløb hele perioden" og hovedtallet kan afvige, når der er engangsbeløb senere. Forslaget forklarer det faste beløb, men hovedtallet viser niveauet efter sidste engangsbeløb | 2 |
| E2 | Mens optimeringen kører (cirka 3 s), venter andre beregninger i køen | 1 |
