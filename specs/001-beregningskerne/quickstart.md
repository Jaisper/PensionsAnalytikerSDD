# Quickstart: Beregningskerne

## Opsætning

```bash
uv sync            # installerer pakken + dev-afhængigheder
uv run pytest      # hele suiten (differentialtest skippes, hvis legacy/ mangler)
```

## Eksempel

```python
from datetime import date
from pensionskerne import beregn, Pensionsprofil, Ordning, Antagelser

profil = Pensionsprofil(
    foedselsdato=date(1963, 5, 1),
    civilstand="enlig",
    kommune="aarhus",
    kirkeskat=None,
    likvid_formue=50_000,
    ordninger=[
        Ordning(id="rate1", type="ratepension", oprettet=date(2010, 1, 1),
                saldo=1_000_000, aarlig_indbetaling=0,
                udbetaling_start_alder=65, udbetaling_aar=10),
    ],
)
res = beregn(profil, Antagelser(afkast_efter_pal=0.0, inflation=0.0),
             satsaar=2026, beregningsdato=date(2026, 10, 24))

aar65 = next(a for a in res.aar if a.alder == 65)
assert aar65.kilder[0].brutto == 100_000          # § 11 A: 1.000.000 / 10
print(aar65.netto_i_alt, aar65.sporing)
print(res.folkepensionsalder)                      # 68
print([a.kode for a in res.advarsler])
```

## Validering af scenarier

Hvert acceptance scenario i [spec.md](spec.md) har en test i `tests/golden/` eller
`tests/regler/`. Testen har samme ID som scenariet (fx `test_us1_s2_g03`).

## Ny satsår (SC-006)

1. Kopiér `src/pensionskerne/register/2026.toml` til `2027.toml`, og opdatér værdier, kilder
   og status.
2. Tilføj `kommuner_2027.toml`.
3. Tilføj golden cases for 2027 med nye, eksplicit forventede tal.
4. Kør `uv run pytest`. Der må ikke være behov for at ændre koden i `regler/`.
