# PensionsAnalytikerSDD

Beslutningsstøtteværktøj til dansk pensionsplanlægning — genopbygget fra bunden med
spec-driven development ([Spec Kit](https://github.com/github/spec-kit)).

## Struktur

| Sti | Indhold |
|---|---|
| `.specify/memory/constitution.md` | Projektets forfatning (principper) |
| `specs/NNN-*/` | Én mappe pr. feature: `spec.md`, `plan.md`, `tasks.md` m.m. |
| `legacy/` | Den oprindelige løsning (tag `legacy-v1`). **Kun reference** — kilde til domæneviden, satser med kildehenvisninger og testcases, og orakel for den nye beregningskerne. Der bygges ikke videre på den. |

## Legacy-løsningen

Kan stadig køres fra `legacy/`-mappen (`start.bat`, eller `py tests/test_*.py`).
Se [legacy/README.md](legacy/README.md).

## Arbejdsgang

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement`
