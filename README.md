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
| [004 Tidslinje og datapanel](specs/004-tidslinje/) | Legacy-mønstret: datapanel ("Dine oplysninger"), graf i fuld bredde og en tidslinje under grafen, hvor hver ordning flyttes i tid med skydere |
| [009 Kapitalpension](specs/009-kapitalpension/) | Kapitalpension som ét beløb, i portioner (PBL § 26) eller omlagt til rate eller livrente (§ 41). Afgift allerede betalt. Bufferen beskattes som kapitalindkomst og tæller i pensionstillæg og ældrecheck. Optimeringen vælger udbetalingsform |
| [008 Buffer i grafen](specs/008-buffer-i-grafen/) | Engangsbeløb vises i grafen (buffer eller udbetales), bufferen år for år under grafen, linjen hedder "Fast beløb, hvis du udjævner", og hovedtallet er det faste beløb hele perioden |
| [007 Find bedste plan](specs/007-optimering/) | Optimering som i legacy: højeste faste beløb efter skat hele perioden uden nye indkomsthuller. Forslag med "Anvend" og stiplede bjælker. Engangsbeløb kan bruges som buffer eller udbetales direkte |
| [006 Bjælker, der trækkes](specs/006-traek-bjaelker/) | Tidslinjens bjælker er selv kontrollerne: træk for at flytte, træk i grebet for ratepensionens varighed, klik for ‹ › og tastatur. WCAG 2.2 AA |
| [005 Kør i browseren](specs/005-browser/) | Hele beregningen og PDF-aflæsningen kører i browseren (Pyodide). Ingen server, og intet forlader borgerens computer. Udgives som statisk side på GitHub Pages |
| [003 Indlæsning af PensionsInfo-rapport](specs/003-pdf-import/) | Upload af PDF → guiden udfyldes. Lokal, regelbaseret parser (ingen AI, Princip XI), testet mod en rigtig rapport |

```bash
uv sync
uv run pytest                                  # CPython-suiten
uv run python scripts/byg_side.py              # statisk side i _site/
uv run python -m http.server -d _site 8002     # åbn http://127.0.0.1:8002
uv run pytest -m browser                       # samme kode i Pyodide, sammenlignet med CPython
```

## Legacy-løsningen

Kan stadig køres fra `legacy/`-mappen (`start.bat`, eller `py tests/test_*.py`).
Se [legacy/README.md](legacy/README.md).

## Arbejdsgang

`/speckit-constitution` → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement`
