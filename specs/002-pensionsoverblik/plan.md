# Implementation Plan: Pensionsoverblik

**Branch**: `002-pensionsoverblik` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

## Summary

En lille, stateless FastAPI-app (`pensionsoverblik`) omsætter guidedata til kernens
`Pensionsprofil`, kalder `beregn` og returnerer en visningsmodel. Visningsmodellen er ren
omformatering. En statisk frontend viser modellen:
- hovedtal først
- graf og kildekort
- foldbare detaljer
- antagelser med skydeknapper

Layoutet følger [designretningen](../../docs/ux/designretning.md) (velliv-inspireret layout
med egen identitet).

## Technical Context

**Language/Version**: Python ≥ 3.11; HTML5, CSS custom properties, ES2020 uden build

**Primary Dependencies**:
- `fastapi`, `uvicorn` (gruppe `app`)
- `httpx` (dev)
- Chart.js 4.4.1 fra cdnjs

**Storage**: Ingen

**Testing**:
- pytest: visningsmodel mod kernen, API og privatliv
- axe-core i browseren
- heuristisk evaluering

**Target Platform**: Moderne browsere, desktop og mobil (360 px+)

**Project Type**: Web (server og statisk frontend) i samme repo som kernen

**Performance Goals**: `POST /api/beregn` < 1 s

**Constraints**:
- Ingen persistens og ingen logning af input
- WCAG 2.2 AA
- Ingen karruseller

## Constitution Check

| # | Princip | Gate | Status |
|---|---|---|---|
| I | Deterministisk beregning | Alle tal fra `beregn`. Visningslaget formaterer, summerer og ganger kun med kernens `realfaktor` | ✅ |
| II | Regelregister | Satser i "Sådan har vi regnet" hentes via `register`. Ingen tal i frontend | ✅ |
| III | Lovgivningen er facit | Ingen nye regler | ✅ |
| IV | Test først | Visnings- og API-tests skrives før implementeringen | ✅ |
| V | Sporbarhed | Advarsler placeres kontekstuelt. Satser med kilde og status | ✅ |
| VI | Isoleret kerne | Kernen er uændret bortset fra `realfaktor` (MINOR). Beregningsdato sættes i API-laget | ✅ |
| VII | Persondata | Stateless, ingen logning af body, ingen cookies, info i guiden | ✅ |
| VIII | Dansk brugerflade | Dansk tekst og `Intl.NumberFormat` med `da-DK` | ✅ |
| IX | Simpelhed | Tre afhængigheder (research R2). Ingen build-trin | ✅ |
| X | Brugeroplevelse | Svaret først, fold-ud, (i)-forklaringer, faste kildefarver, WCAG AA og heuristisk evaluering før merge | ✅ |

## Project Structure

```text
src/pensionsoverblik/
├── __init__.py
├── api.py            # FastAPI: /, /api/kommuner, /api/beregn
├── oversaet.py       # guidedata → Pensionsprofil/Antagelser
├── visning.py        # Fremskrivning → visningsmodel (ren omformatering)
├── katalog.py        # korttyper og advarselskatalog (tekster, ikoner, placering)
└── static/
    ├── index.html
    ├── app.css
    └── app.js
tests/app/
├── test_visning.py   # SC-004: visningsmodel = kernens tal
├── test_api.py       # 200/422, feltfejl, kommuneliste
└── test_privatliv.py # ingen persistens, ingen body i logs
```

## Complexity Tracking

Ingen overtrædelser.
