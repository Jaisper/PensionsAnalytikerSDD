# Kontrakt: Kernens offentlige grænseflade

Kernen er et Python-bibliotek (`pensionskerne`). Kontrakten er den eneste vej ind. Alt andet
er internt og kan ændres uden varsel.

```python
from datetime import date
from pensionskerne import (
    beregn, Pensionsprofil, Ordning, Partner, PartnerIndkomst, Antagelser,
    Fremskrivning, UgyldigtInput, UverificeretRegel, register,
)

def beregn(
    profil: Pensionsprofil,
    antagelser: Antagelser,
    satsaar: int,
    beregningsdato: date,
    streng: bool = False,
) -> Fremskrivning: ...
```

## Garantier

| # | Garanti | Krav |
|---|---|---|
| K1 | Ren funktion: ingen I/O ud over at læse de indlejrede registerfiler, ingen global tilstand, intet `date.today()` | FR-001, Princip VI |
| K2 | `beregn(x) == beregn(x)` for identisk input | FR-002 |
| K3 | Ugyldigt input giver `UgyldigtInput` med `felt` og en dansk `besked`. Der returneres aldrig et delvist resultat | FR-003 |
| K4 | `streng=True` og en ikke-verificeret post i brug giver `UverificeretRegel` | FR-012 |
| K5 | For hvert `Aarsresultat`: Σ kilder.skat = `skat_i_alt` (±0,01) og Σ kilder.netto = `netto_i_alt` | FR-024 |
| K6 | Hvert `Aarsresultat.sporing` er ikke-tom og består kun af gyldige register-id'er eller antagelsesnavne | FR-071, SC-004 |
| K7 | `skat_i_alt ≤ personlig_indkomst`, og netto ≥ 0 for hver kilde | Invariant |

## Registeradgang (kun læsning)

```python
register.satsaar() -> list[int]                       # fx [2026]
register.post(satsaar: int, id: str) -> Registerpost  # id, vaerdi, enhed, kilde, status, reguleres
register.poster(satsaar: int) -> list[Registerpost]
register.kommuner(satsaar: int) -> dict[str, float]
```

Bruges af senere features (forklaring, UI) til at vise satser og kilder. Satser må ikke
kopieres ud af registret (Princip II).

## Versionering

Kontrakten følger semantisk versionering i `pyproject.toml`. Felter i output må tilføjes
(MINOR). Hvis felter fjernes eller omdøbes, er det en MAJOR-ændring.
