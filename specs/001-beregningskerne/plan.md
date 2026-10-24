# Implementation Plan: Beregningskerne og regelregister

**Branch**: `001-beregningskerne` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-beregningskerne/spec.md`

## Summary

Et rent Python-bibliotek, `pensionskerne`, med én offentlig funktion: `beregn(profil,
antagelser, satsaar, beregningsdato, streng)`. Den fremskriver brutto, skat og netto år for år
for private pensionsordninger, folkepension, ATP og tillægsstyrede ydelser efter 2026-reglerne.

Alle lovbestemte værdier ligger som data i et regelregister i TOML-format, med kilde og status
pr. post. Sporingen opstår automatisk, fordi hvert opslag går gennem ét registreringspunkt.

Kernen retter de legacy-afvigelser, der er fundet:

| # | Rettelse |
|---|---|
| A1 | Intet AM-bidrag af pensionsudbetalinger |
| A2 | Udbetalingsalder efter oprettelsesdato |
| A3 | Mediecheck beskattes |
| A4 | Partnerens indkomst indgår med 46 % |
| A5 | Kapitalindkomst indgår i indtægtsgrundlaget |
| A6 | Ældrecheck under 200 kr. udbetales ikke |
| A9 | Ratepension efter PBL § 11 A i stedet for annuitet |

Korrektheden dokumenteres med golden cases, grænseværdier, property-tests og en
differentialtest mod `legacy/engine.py`, hvor alle afvigelser skal være forklaret.

## Technical Context

**Language/Version**: Python ≥ 3.11 (udviklingsmiljø: 3.11.9)

**Primary Dependencies**: Ingen runtime-afhængigheder (standardbibliotek, `tomllib`). Dev:
`pytest`, `hypothesis`.

**Storage**: Ingen. Registret er indlejrede, skrivebeskyttede TOML-filer i pakken.

**Testing**: pytest (golden, grænse, enhed, kontrakt), hypothesis (invarianter),
differentialtest mod `legacy/` (skippes, hvis mappen mangler).

**Target Platform**: Platformsuafhængigt bibliotek (Windows-udvikling, senere server).

**Project Type**: Library

**Performance Goals**: Fuld fremskrivning (40 år, 10 ordninger) < 100 ms (SC-005)

**Constraints**:
- Ingen I/O ud over registret
- Ingen `date.today()`
- Deterministisk
- Hele testsuiten kører med én kommando (`uv run pytest`) uden netværk og uden server

**Scale/Scope**:
- ~45 registerposter + 98 kommuner
- 6 regelmoduler
- 7 user stories
- ~40 funktionelle krav

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Princip | Gate | Status |
|---|---|---|---|
| I | Deterministisk beregning | Kernen indeholder ingen AI. K1/K2 i kontrakten sikrer determinisme | ✅ |
| II | Regelregister | Alle satser i `register/*.toml` med kilde, satsår og status. En test scanner `src/` for numeriske litteraler ud over 0, 1, 12 og 100 (T-LINT) | ✅ |
| III | Lovgivningen er facit | Research R1–R7 afklarer lovspørgsmålene. A1–A6 og A9 rettes. Forenklinger (R6 fallback, FR-081) markeres i output | ✅ |
| IV | Test først | tasks.md ordner test-opgaver før implementering pr. story. Golden, grænse, property og differential er planlagt (research T7) | ✅ |
| V | Sporbarhed | `Regelopslag` (T5) giver sporing pr. år. Flag og advarsler indgår i output (data-model) | ✅ |
| VI | Isoleret kerne | Beregningsdato er input. Ingen I/O. Én offentlig funktion (kontrakt K1) | ✅ |
| VII | Persondata | Kernen gemmer og logger intet. Profilen lever kun i kaldet | ✅ (ikke relevant ud over det) |
| VIII | Dansk brugerflade | Advarsler og fejlbeskeder er på dansk. Talformatering hører til senere UI-feature | ✅ |
| IX | Simpelhed | Én pakke uden runtime-afhængigheder. `hypothesis` som eneste ekstra dev-afhængighed er begrundet i research T2 | ✅ |
| X | Brugeroplevelse | Ingen UI i denne feature. Advarsler har kode, kort dansk besked og aldersinterval, så en senere UI kan vise dem kontekstuelt | ✅ (ikke relevant ud over det) |

**Re-check efter Phase 1**: ✅ Designet i data-model og kontrakt introducerer ingen nye
komponenter eller afhængigheder.

## Project Structure

### Documentation (this feature)

```text
specs/001-beregningskerne/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/kerne-api.md
├── checklists/requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml                    # uv-projekt, pakke "pensionskerne", dev: pytest, hypothesis
src/pensionskerne/
├── __init__.py                   # offentlig API (kontrakt)
├── model.py                      # input/output-dataklasser, UgyldigtInput, UverificeretRegel
├── register/
│   ├── __init__.py               # indlæsning, Registerpost, satsregulering
│   ├── opslag.py                 # Regelopslag: sporing + streng tilstand
│   ├── 2026.toml
│   └── kommuner_2026.toml
├── regler/
│   ├── skat.py                   # PI-skat, personfradrag, progression, skatteloft, fordeling
│   ├── folkepension.py           # fp-alder, grundbeløb, pensionstillæg, indtægtsgrundlag
│   ├── ydelser.py                # tillægsprocent, ældrecheck, mediecheck
│   ├── opsat.py                  # venteprocent
│   ├── udbetalingsalder.py       # tidligste lovlige alder (R2)
│   └── ordninger.py              # FV, § 11 A-rate, livsvarig, engangsbeløb, lofter
├── validering.py                 # FR-003
├── fremskrivning.py              # år-for-år-orkestrering (data-model "Rækkefølge i et år")
└── jaevn.py                      # US7

tests/
├── golden/                       # G-02 … VT-1 + nye cases for A1–A9
├── regler/                       # enhed + grænseværdier pr. regelmodul
├── egenskaber/                   # hypothesis-invarianter (K5, K7, monotonicitet)
├── kontrakt/                     # K1–K7, validering, streng tilstand
├── register/                     # alle poster har kilde/status; T-LINT; kommuner = 98
├── differential/                 # mod legacy/engine.py (research T7)
└── ydeevne/                      # SC-005
```

**Structure Decision**: Ét enkelt bibliotek med src-layout. Regelmodulerne svarer til
lovområderne, så en revisor kan læse ét modul pr. regelområde. Der er ingen CLI eller API i
denne feature. De kommer i senere features og kalder `beregn`.

## Phase 0 / Phase 1 artefakter

- **Research**: [research.md](research.md). R1–R7 er lovspørgsmål og T1–T8 tekniske valg.
- **Data model**: [data-model.md](data-model.md)
- **Kontrakt**: [contracts/kerne-api.md](contracts/kerne-api.md)
- **Quickstart**: [quickstart.md](quickstart.md)

## Følgeopdatering af domænegrundlaget

`docs/domaene/beregningskerne.md` opdateres:
- med A9 (ratepension § 11 A)
- med svarene på de åbne spørgsmål (R1–R5)
- med rettelsen af A8's paragrafhenvisning

## Complexity Tracking

Ingen overtrædelser. Tabellen er tom.
