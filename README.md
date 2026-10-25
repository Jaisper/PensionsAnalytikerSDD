# PensionsAnalytikerSDD

Beslutningsstøtteværktøj til dansk pensionsplanlægning — genopbygget fra bunden med
spec-driven development ([Spec Kit](https://github.com/github/spec-kit)).

## Struktur

| Sti | Indhold |
|---|---|
| `.specify/memory/constitution.md` | Projektets forfatning (principper) |
| `specs/NNN-*/` | Én mappe pr. feature: `spec.md`, `plan.md`, `tasks.md` m.m. |
| `legacy/` | Den oprindelige løsning (tag `legacy-v1`). **Kun reference** — kilde til domæneviden, satser med kildehenvisninger og testcases, og orakel for den nye beregningskerne. Der bygges ikke videre på den. |

## Status

| Feature | Status |
|---|---|
| [001 Beregningskerne og regelregister](specs/001-beregningskerne/) | Implementeret (`src/pensionskerne/`). 424 tests inkl. differentialtest mod legacy. 47/48 satser verificeret mod primærkilder |

| [002 Pensionsoverblik](specs/002-pensionsoverblik/) | Brugerflade: guide → resultat med hovedtal, graf, kort og skydere. axe-core 0 fejl, heuristisk evaluering i [ux-evaluering.md](specs/002-pensionsoverblik/ux-evaluering.md) |
| [003 Indlæsning af PensionsInfo-rapport](specs/003-pdf-import/) | Infrastruktur klar (upload, lokalt tekstudtræk, omsætning, UI). **Slået fra**, indtil en lokal parser er bygget mod en rigtig rapport. Ingen AI (Princip XI) |

```bash
uv sync
uv run pytest
uv run uvicorn pensionsoverblik.api:app --port 8002   # åbn http://127.0.0.1:8002
```

## Legacy-løsningen

Kan stadig køres fra `legacy/`-mappen (`start.bat`, eller `py tests/test_*.py`).
Se [legacy/README.md](legacy/README.md).

## Arbejdsgang

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement`
