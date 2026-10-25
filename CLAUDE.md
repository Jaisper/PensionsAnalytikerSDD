# PensionsAnalytikerSDD

Greenfield-genopbygning af PensionsAnalytiker med Spec Kit. Læs først
[.specify/memory/constitution.md](.specify/memory/constitution.md). Den har forrang.

## Kommandoer

```bash
uv sync                 # miljø
uv run pytest           # hele suiten (inkl. differentialtest mod legacy/)
uv run uvicorn pensionsoverblik.api:app --port 8002   # brugerfladen (uden --reload; den hænger på Windows)
```

## Struktur

- `src/pensionskerne/`: beregningskernen (feature 001). Én offentlig funktion, `beregn`.
  - `register/<år>.toml`: ALLE satser med kilde og status. Ingen tal i `regler/` (testes af
    `tests/register/test_ingen_litteraler.py`).
  - `regler/`: ét modul pr. lovområde. Rene funktioner, som læser satser via `Regelopslag`.
  - `fremskrivning.py`: år-for-år-orkestrering. `jaevn.py`: jævn udbetaling.
- `src/pensionsoverblik/`: brugerflade (feature 002). FastAPI + statisk HTML/CSS/JS uden build. Visningslaget
  må kun omformatere kernens tal. UX følger forfatningens Princip X og `docs/ux/designretning.md`.
- `src/pensionsoverblik/pdfimport/`: PDF-indlæsning (feature 003). Lokal, deterministisk parser (`pensionsinfo.py`).
  Intet må skrives til disk eller logs. Rigtige rapporter må aldrig committes — test lokalt med
  `PENSIONSINFO_RAPPORT=<sti> uv run pytest -k rigtig`.
- `specs/NNN-*/`: spec, plan, research, data-model, kontrakt og tasks pr. feature.
- `docs/domaene/`: domænegrundlag og legacy-afvigelser (A1–A9).
- `legacy/`: kun reference og orakel. Der bygges ikke videre på den.

## Regler for arbejdet

- **Ingen persondata til AI/LLM** (Princip XI, NON-NEGOTIABLE). Ingen AI-klienter, -afhængigheder eller
  -endpoints i `src/` (`tests/kontrakt/test_ingen_ai.py`). En AI-funktion må kun bruge generisk indhold.

- Lovgivningen er facit (Princip III). En ny regel eller sats kræver en kilde i registret.
- Test først (Princip IV). En ændring af en golden case kræver begrundelse.
- Spec Kit-skills er ikke installeret i dette checkout. Følg trinene manuelt med
  `.specify/templates` og `.specify/scripts/powershell`.
