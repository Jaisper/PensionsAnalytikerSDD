# Research: 035 Branchestandard

**Dato**: 2026-11-04

## R1. Henstillingen (version og metode)

- LP-information 20/20, 7.10.2020, er den nyeste på fogp.dk/branchesamarbejde/pension. Ændringen fra
  LP-info 35/19 er kun pkt. 7.2: år 1–5 og 6–10, men investeringsomkostninger for år 1–10.
- **Trin 1 (appendix 1)**: Rekursion for middelværdi og varians mellem t(n−1) og t(n):
  - M(tₙ) = M(tₙ₋₁)·F(tₙ₋₁)·e^{μΔt} + I(tₙ)
  - V(tₙ) = F(tₙ₋₁)²·e^{2μΔt}·((V(tₙ₋₁) + M(tₙ₋₁)²)·e^{σ²Δt} − M(tₙ₋₁)²)
  - μ = ln(1 + Σ wᵢ·nettoafkastᵢ), hvor nettoafkast = Rådets afkast − investeringsomkostninger.
  - σ = √(wᵀ S w), hvor S_ij = ρ_ij σ_i σ_j.
  - F er udbetalingsfaktoren (1 i opsparingen; fx 0,9 ved første rate af en tiårig ratepension).
  - Fraktil: x_p = exp(b·N⁻¹(p) + a − b²/2), hvor a = ln M og b² = ln(1 + V·e^{−2a}).
- **Trin 2**: Middel regnes med forventet afkast. Fraktilstien fra s til t er
  r = (depot_t − præmie_t) / (depot_s · udbetalingsfaktor_s) − 1.
- **Trin 3**: Fremregning på hver sti med omkostninger, PAL og kontoteknik.
- **Depotet løber tør**: Valgmulighed 1 (seneste beregnelige afkast resten af perioden) bruges, som
  spec'en siger.
- `N⁻¹(0,95)` = 1,6448536… kan regnes med stdlib (`statistics.NormalDist().inv_cdf`). Det virker i
  Pyodide.

## R2. Facit: bilag 2 (taleksempel)

Arket "Fraktilafkast Udledning årlige" er en ren golden case for trin 1–2 (SC-002):

| Input | Værdi |
|---|---|
| Initialopsparing | 1.000 |
| Præmie | 100 om året, prisindekseret 2 % (100; 102; 104,04; …) |
| Pensionstidspunkt | om 10 år, alder 55 → 65 |
| Udbetaling | tiårig ratepension (faktor 0,9; 0,889; … 0) |
| μ/σ | 0,0869/0,20 til 61 år, så nedtrapning: 62: 0,06995/0,12; 63: 0,05482/0,08; 64: 0,04248/0,06; 65: 0,03333/0,05; 66: 0,02718/0,045; 67+: 0,01903/0,04 |

Forventede værdier (uddrag; fulde tal tages ind i testen fra regnearket med kildeangivelse):

| t | Alder | M | V | 5 %-depot | 95 %-depot | sti 5 % | sti 95 % |
|---|---|---|---|---|---|---|---|
| 1 | 56 | 1.302 | 58.750 | 944,7 | 1.734 | −0,2339 | 0,4836 |
| 2 | 57 | 1.524 | 155.100 | 971,4 | 2.242 | −0,08188 | 0,2328 |
| 10 | 65 | 3.816 | 3.168.000 | 1.667 | 7.174 | 0,03456 | 0,04853 |

Arket "Prognoseberegning årlige skridt" er facit for trin 3 i eksemplets enkle kontoteknik (PAL
15,3 %, saldoomkostning 0,8 %, fast gebyr 1.000 kr., inflation 2 %), fx 95 %-ydelsen ved 65 år =
665.500 kr. Trin 3 i kernen bruger kernens egen kontoteknik, så det ark bruges kun til at teste
omregningen af stien (PAL og omkostninger), ikke kernens skat.

## R3. Rådets forudsætninger, 1. halvår 2027

Offentliggjort 2.11.2026 på afkastforventninger.dk (regneark
"afkastforventninger-1-halvar-2027.xlsx"). De afløser 2. halvår 2026 og skal ind i registret som et
nyt forudsætningssæt med dato.

**År 1–10**: 10 aktivklasser. Uddrag for blandingsporteføljen:

| Aktivklasse | Afkast 1–5 | Afkast 6–10 | Afkast 1–10 | Std.afv. | Inv.omk. 1–10 |
|---|---|---|---|---|---|
| Stats- og realkreditobligationer | 3,4 % | 3,6 % | 3,5 % | 4,3 % | 0,22 % |
| Globale aktier (developed) | 6,6 % | 7,7 % | 7,1 % | 16,5 % | 0,45 % |

Korrelationen mellem de to er 0,1. Regnearket har alle 10 klasser og den fulde korrelationsmatrix.
Det hele tages ind i registret, selv om v1 kun bruger to klasser.

**År 11+**: Tre aktivklasser.

| Aktivklasse | Afkast | Std.afv. | Inv.omk. |
|---|---|---|---|
| Obligationer | 3,5 % | 8 % | 0,22 % |
| Illikvide aktiver | 6,5 % | 12 % | 0,22 % |
| Aktier | 6,5 % | 18 % | 0,45 % |

Korrelationer: obligationer–illikvide 0, obligationer–aktier 0, illikvide–aktier 0,3.

**Inflation**: 1,8 % (år 1–5, 6–10 og 1–10) og 2,0 % (år 11+).

**Afledt**: Blandingsporteføljen *a* aktier og (1 − *a*) obligationer flytter fra klasse 5/1 i år
1–10 til aktier/obligationer i år 11+. Afkast og varians er monotone i *a* i alle perioder, så
bisektionen i kalibreringen er veldefineret.

## R4. Kernen i dag

- `Antagelser.afkast_efter_pal` og `afkast_forloeb` (023a) er fælles for alle ordninger.
  Branchestandarden kræver et forløb pr. ordning.
- Én inflation (`inflation`/`effektiv_satsregulering`) styrer både satsregulering (`Regelopslag`)
  og omregningen til dagens kroner. Rådets inflation skifter fra 1,8 % til 2,0 % efter år 10.
- Livrenten regnes over en fast horisont (`livsvarig_horisont_alder` = 90). 019 ændrer kun planens
  slutalder. Finanstilsynets levetidsbenchmark findes ikke i registret.
- PDF-importen (003) omregner selskabets udbetalingsprognose til en nutidsværdi for at fordele
  saldoen og aflæser ikke investeringsformen.

## Åbne punkter til implementeringen

- **Levetidsbenchmark**: Aktuel version og form (forventet restlevetid pr. alder inkl.
  levetidsforbedringer) hentes fra Finanstilsynet og lægges i registret.
- **Investeringsform i rapporten**: Hvor i PensionsInfo-rapporten den står, og hvordan den er
  formuleret. Den syntetiske rapport (`tests/app/pensionsinfo_syntetisk.py`) udvides tilsvarende.
- **Selskabets prognose ved flere aldre**: US4 kræver en prognose ved en anden alder end den, der
  kalibreres på. Har rapporten kun én alder pr. produkt, sammenlignes på tværs af ordninger hos
  samme selskab i stedet (kalibrér på ratepensionen, test på livrenten).
