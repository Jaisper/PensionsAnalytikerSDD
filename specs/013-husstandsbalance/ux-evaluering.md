# UX-evaluering: Opsparing uden for pension

**Dato**: 2026-10-25 · **Metode**: browsertests (`tests/browser/test_opsparing.py`), headless Chrome,
og en lokal måling med syntetiske data.

| Måling | Resultat | Krav |
|---|---|---|
| Nyt trin 4 "Din opsparing uden for pension". Alle felter er valgfrie, så trinnet kan springes over | ja (test) | US1 |
| Overslag over partneren: kun "Din partners opsparing" (tæller i ældrechecken). Fuld partner: partnerens egen opsparing | ja (test) | US1 |
| Opsparing hæver hovedtallet | ja (test) | US2 |
| Fold-ud "Din opsparing uden for pension over tid" med restformue og tabel pr. år | ja (test) | US4 |
| "Samlet" viser husstandens restformue | ja (app-test) | US4 |
| Samme resultat i Pyodide og CPython | ja (test) | SC-005 |
| Ny beregning for to profiler med opsparing | 0,16 s (median af 5) | SC-006 < 2 s |
| axe (opsparingstrinnet, par) og 360 px | 0 fejl, ingen scroll | FR-009 |

## Heuristik (kort)

- **Forklaring i konteksten:** Trinnet siger, hvorfor der spørges: opsparingen påvirker skat,
  pensionstillæg og ældrecheck. Hjælpeteksten under feltet siger, hvordan den regnes.
- **Klare navne:** Nøgletallet hedder nu "Pensionsopsparing i dag", så det ikke forveksles med
  opsparing uden for pension. Grafen over bufferen hedder "Opsparing uden for pension, som bruges
  i din faste udbetaling".
- **Brugerens kontrol:** Afkrydsningen "Brug opsparingen i min faste udbetaling" lader borgeren
  holde opsparingen urørt. Så vokser den og ses som restformue.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| O1 | Guiden er ét klik længere for alle, også dem uden opsparing | 1 |
| O2 | Restformuen for opsparing i planen er altid 0 (udjævningen bruger den op). Det forklares i fold-ud'en, men "bevar et beløb" kommer først med 015 | 1 |
