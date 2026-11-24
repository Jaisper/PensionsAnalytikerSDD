# Feature Specification: Metodebeskrivelsen i løsningen

**Feature Branch**: `039-metode-i-loesningen`

**Created**: 2026-11-24

**Status**: Implementeret

**Input**: "md skal også kunne læses i pænt format i selve løsningen! – hvor det alt for tekniske som fx
labels er ryddet ud."

## Afklaring

- **Én kilde**: `docs/metode.md` er både revisionens dokument (GitHub) og siden i løsningen. Der vedligeholdes
  ikke to tekster.
- **Det tekniske** markeres i kilden med `<!-- teknisk -->…<!-- /teknisk -->`. GitHub viser ikke kommentarerne, så
  revisionen ser alt. En markering, der dækker hele afsnit, står på egne linjer, så GitHub stadig viser
  overskrifter og fed skrift rigtigt.
- **Automatisk på siden**: links til filer i repositoriet bliver til tekst, kodeformatering bliver til tekst, og
  featurenumre ("feature 010", "(018 og 019)") fjernes.
- **Byggetrinnet** laver siden `saadan-fungerer.html` (kun standardbiblioteket, som resten af `byg_side.py`).

## Afklaring 2026-11-24 (039b)

- Linket fra beregningen fik siden til at erstatte beregningen, og da intet gemmes, var tallene væk. → Siden
  åbnes i en ny fane, og linket siger det: "Sådan fungerer løsningen (åbner i en ny fane)". Knappen "Tilbage til
  beregningen" lukker fanen. Åbnet direkte (fx et link delt med revisionen) går knappen til beregningen
  (produktejer). Fravalgt: siden indlejret i selve løsningen.

## Requirements

- **FR-001**: Siden "Sådan fungerer løsningen" MUST bygges fra `docs/metode.md` og linkes fra sidefoden og
  metodesiden.
- **FR-002**: Siden MUST NOT indeholde kodenavne: filer, stier, funktioner, snake_case, camelCase, koder som
  `RATEPENSION_LOFT`, registerposter eller featurenumre (testet).
- **FR-003**: Siden MUST have en indholdsfortegnelse med fungerende ankre, en CSP (kun sidens eget script, `script-src 'self'`), opfylde WCAG 2.2 AA (axe-core) og kunne læses ved 360 px.
- **FR-004**: Siden MUST linke til den fulde metodebeskrivelse til revision.

## Success Criteria

- **SC-001**: `tests/app/test_metode_side.py` (konvertering, ingen kodenavne, ankre, CSP) og
  `tests/browser/test_saadan_fungerer.py` (åbnes fra forsiden, ingen CSP-overtrædelser, axe og 360 px) er grønne.
