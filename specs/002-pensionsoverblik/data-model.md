# Data Model: Pensionsoverblik

## Guidedata (request til `POST /api/beregn`)

```json
{
  "person": {"foedselsdato": "1963-05-01", "civilstand": "enlig", "kommune": "aarhus",
             "folkekirkemedlem": false, "likvid_formue": 50000, "atp_aarlig": null,
             "partner": null},
  "ordninger": [{"id": "o1", "type": "ratepension", "saldo": 1000000, "aarlig_indbetaling": 0,
                 "udbetaling_start_alder": 65, "udbetaling_aar": 10, "oprettet": "2010-01-01"}],
  "antagelser": {"afkast_efter_pal": 0.04, "inflation": 0.02, "folkepension_opsaettelse_aar": 0}
}
```

`partner` (hvis gift): `{"foedselsdato": "...", "oevrig_indkomst_aar": 120000}`. Beløbet bruges
for alle år (forenkling, jf. spec Assumptions).

## Visningsmodel (response)

| Felt | Indhold | Kilde i kernen |
|---|---|---|
| `hovedtal` | `maaned` (afrundet til 100), `fra_alder`, `type` (`jaevn` \| `foerste_fp_aar`) | `jaevn.niveau_real / 12`, ellers første hele folkepensionsår |
| `kort[]` | `noegle`, `titel`, `forklaring`, `farve`, `netto_maaned` (første hele år, dagens kr.), `fra_alder`, `til_alder`, `advarsler[]`, `detaljer[]` (alder, brutto, skat, netto pr. år) | `Aarsresultat.kilder` × `realfaktor` |
| `graf` | `aldre[]`, `serier[]` (én pr. korttype: netto/md. i dagens kr.), `markeringer[]` | samme + `Advarsel.aldre` |
| `hovedtal_advarsler[]`, `generelle_advarsler[]` | Placerede advarsler | `Advarsel` |
| `antagelser` | De brugte antagelser | `Fremskrivning.antagelser` |
| `aar[]` | Pr. år: alder, PI, skat, netto, netto i dagens kr., indtægtsgrundlag, tillægsprocent | `Aarsresultat` |
| `satser[]` | Brugte registerposter: id, værdi, kilde, status | `sporing_samlet` + `register.post` |
| `folkepensionsalder` | | `Fremskrivning.folkepensionsalder` |

**Korttyper**:

| Kildetyper | Kortnøgle | Titel |
|---|---|---|
| grundbeloeb + pensionstillaeg | `folkepension` | Folkepension |
| atp | `atp` | ATP |
| ratepension | `ratepension` | Ratepension |
| livsvarig | `livsvarig` | Livsvarig pension |
| aeldrecheck + mediecheck | `checks` | Ældrecheck og mediecheck |

## Advarselskatalog

| Kode | Placering | Ikon |
|---|---|---|
| `ATP_SKOENNET` | kort `atp` | ≈ |
| `RATEPENSION_LOFT` | kort `ratepension` | ! |
| `750_TIMER`, `OPSAT_ANDRE_FORMER` | kort `folkepension` | ! / ≈ |
| `MELLEMSKAT_INTERVAL` | graf (markering) og generel | ! |
| `BUFFER_YDELSE_FORENKLING`, `JAEVN_FORUDSAETTER_SENERE_UDBETALINGER` | hovedtal | ≈ |
| `UDBETALING_FOER_LOVLIG_ALDER` | generel | ! |
| ukendt kode | generel | ! |

## Fejl (422)

`{"felt": "<kernens felt>", "besked": "<dansk>"}`.
