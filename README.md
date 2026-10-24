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
| [001 Beregningskerne og regelregister](specs/001-beregningskerne/) | Implementeret (`src/pensionskerne/`). 414 tests inkl. differentialtest mod legacy. T-REG (primærkildetjek af sidste poster) udestår |

```bash
uv sync
uv run pytest
```

## Legacy-løsningen

Kan stadig køres fra `legacy/`-mappen (`start.bat`, eller `py tests/test_*.py`).
Se [legacy/README.md](legacy/README.md).

## Arbejdsgang

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement`
