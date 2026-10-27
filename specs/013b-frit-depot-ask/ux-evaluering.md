# UX-evaluering: Frit depot og aktiesparekonto

**Dato**: 2026-10-27 · **Metode**: browsertests (`tests/browser/test_depot_ask.py`), headless Chrome.

| Måling | Resultat | Krav |
|---|---|---|
| Depot med gevinst og aktiesparekonto sendes fra guiden og beskattes i resultatet | ja (test) | US1, US2 |
| Tom gevinst giver standardandelen | ja (test) | 013, Clarifications |
| Løbende indskud uden løn giver en fejl ved feltet | ja (test) | FR-002 |
| axe på opsparingstrinnet | 0 fejl | Princip X |
| Fastpunktet konvergerer med depot og aktiesparekonto over ældrechecks grænse | ja (golden test) | Plan, risiko |

## Heuristik (kort)

- **Genkendelighed**: Felterne følger bankens opdeling: "Penge i banken og obligationer", "frit
  depot" og "aktiesparekonto". Obligationsforeninger står under bank, fordi de beskattes som renter.
- **Ærlighed**: Teksten siger, at en tom gevinst betyder halvdelen af værdien, og i hvilken
  rækkefølge opsparingen bruges. Udbytte er ikke med. Det står under forenklingerne.
- **Byrde**: Trinnet har nu flere felter. De er alle valgfri, og trinnet kan springes over.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| D1 | Trækrækkefølgen kan kun ændres i kernen og oversættelsen, ikke i guiden. Det kommer med "Optimér trækrækkefølge" | 1 |
| D2 | Partneren kan ikke angive løbende indskud på aktiesparekontoen | 1 |
| D3 | Trinnet er blevet langt. Overvej at folde depot og aktiesparekonto ind bag "Har du aktier?" | 2 |
