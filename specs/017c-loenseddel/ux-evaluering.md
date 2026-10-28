# UX-evaluering: Løn som på lønsedlen

**Dato**: 2026-10-28 · **Metode**: browsertests (`tests/browser/test_loenseddel.py`), headless Chrome.

| Måling | Resultat | Krav |
|---|---|---|
| Månedsløn og procenter sendes som årsløn og andele ("8,5" → 0,085) | ja (test) | US1, FR-005 |
| Rapportens indbetaling pr. måned vises ved procenterne og som % af lønnen | ja (test) | US2, FR-006 |
| Indlæste ordninger med indbetaling er markeret "Indbetales via din løn" | ja (test) | US3 |
| Procenter uden ordning fra lønnen giver fejl ved feltet | ja (test) | FR-004 |
| Fil gemt med årsløn åbnes som månedsløn | ja (test) | FR-005 |
| axe på ordningstrinnet | 0 fejl | Princip X |

## Heuristik (kort)

- **Genkendelighed**: Felterne hedder som på lønsedlen. Hintet fra rapporten er et tjek, ikke et
  forslag, og vi udfylder ikke procenterne for borgeren.
- **Ærlighed**: Forenklingen (procent af hele bruttolønnen) står i forenklingsregistret.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| L1 | Afkrydsningen "Indbetales via din løn" vises også uden procenter, hvor den ikke betyder noget | 1 |
| L2 | Pensionsgivende løn og tillæg uden pension kan ikke skrives særskilt | 1 |
