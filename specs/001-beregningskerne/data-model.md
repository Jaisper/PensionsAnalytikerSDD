# Data Model: Beregningskerne og regelregister

Alle input- og output-typer er uforanderlige (frozen) dataklasser. Beløb er i kr. pr. år,
medmindre andet er angivet. Satser er brøker (0,1201 og ikke 12,01). Aldre er hele år.

## Input

### Pensionsprofil

| Felt | Type | Regel |
|---|---|---|
| `foedselsdato` | dato | Påkrævet. Født ≥ 1955-01-01, ellers afvises inputtet. |
| `civilstand` | `enlig` \| `gift_samlevende` | Påkrævet |
| `kommune` | str | Skal findes i kommuneregistret for satsåret |
| `kirkeskat` | brøk \| None | None = ikke medlem af folkekirken (0 %). Ellers kommunens kirkeskattesats som brøk |
| `likvid_formue` | kr | ≥ 0. Bruges til formuegrænsen for ældrecheck (pr. 1/1) |
| `anden_kapitalindkomst` | kr/år | Default 0. Indgår i indtægtsgrundlaget (FR-032) |
| `ordninger` | liste[Ordning] | Kan være tom |
| `atp_aarlig` | kr/år \| None | None = brug registrets fallback, og markér det |
| `partner` | Partner \| None | Påkrævet, hvis civilstand er `gift_samlevende` |

### Ordning

| Felt | Type | Regel |
|---|---|---|
| `id` | str | Unik i profilen |
| `type` | `ratepension` \| `livsvarig` \| `aldersopsparing` \| `kapitalpension` | |
| `oprettet` | dato \| None | Bestemmer tidligste udbetalingsalder (R2) |
| `saldo` | kr | ≥ 0. Værdi på beregningsdatoen |
| `aarlig_indbetaling` | kr/år | ≥ 0. Indbetaling efter AM-bidrag, til start |
| `udbetaling_start_alder` | int | ≥ tidligste lovlige alder (FR-043) |
| `udbetaling_aar` | int \| None | Kun ratepension: 10–30 (R3). Default 10 |
| `i_buffer` | bool | Kun engangsbeløb. Default True (US7) |

### Partner

| Felt | Type | Regel |
|---|---|---|
| `foedselsdato` | dato | Afgør, om partneren er pensionist i et givet år |
| `indkomst_pr_aar` | dict[kalenderår → PartnerIndkomst] | Mangler et år, bruges det seneste kendte år, og det markeres |

**PartnerIndkomst**: `am_pligtig_arbejdsindkomst`, `oevrig_indkomst` (pension, kapital,
ydelser). Kun `oevrig_indkomst` indgår: 100 % hvis partneren er pensionist, ellers 46 % (R1).

### Antagelser

| Felt | Default | Bemærkning |
|---|---|---|
| `afkast_efter_pal` | 0,04 | Forrentning af saldo og ratepension |
| `inflation` | 0,02 | Realværdi |
| `satsregulering` | = `inflation` | FR-060 |
| `loenvaekst` | 0,0 | Vækst i indbetalinger |
| `livsvarig_horisont_alder` | 90 | Mindst 18 år fra start (R6) |
| `buffer_kapitalskat` | 0,27 | Afkastskat på buffer (US7) |
| `folkepension_opsaettelse_aar` | 0 | 0–10 (US5) |

### Kald

`beregn(profil, antagelser, satsaar: int, beregningsdato: date, streng: bool = False)`

## Regelregister

### Registerpost

| Felt | Type | Eksempel |
|---|---|---|
| `id` | str (prikket navnerum) | `skat.bundskat` |
| `vaerdi` | tal \| tabel | `0.1201` |
| `enhed` | `brok` \| `kr_aar` \| `kr_md` \| `aar` \| `tabel` | `brok` |
| `kilde` | str | `PSL § 6; skat.dk` |
| `status` | `verificeret` \| `sekundaer` \| `uverificeret` | `verificeret` |
| `reguleres` | bool | `false` (procent) / `true` (beløb) |

**Satsregulering**: For poster med `reguleres = true` bruges i kalenderår *k*:
`vaerdi × (1 + satsregulering)^(k − satsaar)`.

### Poster (satsår 2026)

| Navnerum | Poster |
|---|---|
| `skat.*` | Bundskat, personfradrag, mellemskat/topskat/top-topskat (sats og grænse), skatteloft × 3, AM-bidrag (kun til indbetalinger) |
| `fp.*` | Grundbeløb, pensionstillæg × 3 (ydelse, fradrag, aftrapning), folkepensionsalder pr. fødselsårsinterval, partnerindkomst-andel (0,46) |
| `tp.*` | Tillægsprocent enlig/gift (bund, trin) |
| `yd.*` | Ældrecheck, formuegrænse, minimum 200 kr., mediecheck |
| `opsat.*` | Venteprocent fra 67 (tabel), fallback pr. år, maks. 10 år |
| `ordning.*` | Ratepensionsloft, rateperiode min./maks., aldersopsparingsloft × 2 og 7-årsgrænse, kapitalpensionsafgift, udbetalingsalder-regler (R2) |
| `atp.*` | Fallback-beløb |
| `kommune.*` | 98 kommuneskattesatser (separat fil) |

## Output

### Fremskrivning

| Felt | Indhold |
|---|---|
| `satsaar`, `beregningsdato` | Ekko af input |
| `folkepensionsalder` | int |
| `aar` | liste[Aarsresultat], én pr. alder fra den første udbetaling til den sidste |
| `jaevn` | JaevnUdbetaling \| None |
| `advarsler` | liste[Advarsel] |
| `antagelser` | De brugte antagelser, inkl. defaults |
| `sporing_samlet` | Alle registerposter, der er brugt, med status |

### Aarsresultat

| Felt | Indhold |
|---|---|
| `alder`, `kalenderaar` | |
| `kilder` | liste[Indkomstkilde]: `kilde_id`, `type`, `brutto`, `skat`, `netto` |
| `personlig_indkomst` | Samlet PI (grundlag for progressiv skat) |
| `skat_i_alt` | Bund + kommune + kirke + progressiv − personfradragets værdi − loftnedslag |
| `indtaegtsgrundlag` | Til pensionstillæg og tillægsprocent |
| `tillaegsprocent` | 0–100 |
| `netto_i_alt`, `netto_real` | |
| `engangsbeloeb_netto` | Udbetalt i året (aldersopsparing, kapitalpension efter afgift) |
| `sporing` | Brugte id'er og antagelser |
| `flag` | `forenkling`, `uverificeret`, `sekundaer`, `skoennet_atp` … |

`Indkomstkilde.type` ∈ {`ratepension`, `livsvarig`, `grundbeloeb`, `pensionstillaeg`, `atp`,
`aeldrecheck`, `mediecheck`}.

### Advarsel

`kode` (fx `RATEPENSION_LOFT`, `MELLEMSKAT_INTERVAL`, `UDBETALING_FOER_LOVLIG_ALDER`,
`ATP_SKOENNET`, `VENTEPROCENT_USIKKER`, `750_TIMER`, `BUFFER_YDELSE_FORENKLING`,
`OPSAT_ANDRE_FORMER`), `besked` (dansk), `aldre` (interval), `registerposter`.

### JaevnUdbetaling (US7)

`niveau_foerste_aar`, `niveau_real`, og pr. år: `alder`, `jaevn`, `normal`, `fra_buffer`,
`til_buffer`, `buffer_rest`.

## Valideringsregler (FR-003)

Fejl kastes som `UgyldigtInput(felt, besked)`:
- fødselsdato før 1955
- negative beløb
- dublerede ordnings-id'er
- ratepension uden for 10–30 år
- start før lovlig alder
- opsættelse > 10 år
- ukendt kommune
- ukendt satsår
- gift uden partner

Streng tilstand kaster `UverificeretRegel(id, kilde)`.

## Rækkefølge i et år (T8)

1. Aktive udbetalinger (rate efter § 11 A, livsvarig annuitet, engangsbeløb)
2. Indtægtsgrundlag = private S-udbetalinger + ATP + anden kapitalindkomst + partnerandel
3. Pensionstillæg (regel efter civilstand og partnerstatus) × ventefaktor
4. Tillægsprocent → ældrecheck (formue, minimum) og mediecheck
5. PI = alle S-udbetalinger + grundbeløb + tillæg + ATP + checks (intet AM-bidrag)
6. Skat samlet. Den fordeles forholdsmæssigt på kilderne (FR-024), så summen er lig totalen
