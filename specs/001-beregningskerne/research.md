# Research: Beregningskerne og regelregister

**Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Dato**: 2026-10-24

Phase 0 afklarer to ting: de lovspørgsmål, som spec'en henviser til plan-fasen (Princip III),
og de tekniske valg.

---

## Del A — Lovspørgsmål

### R1. Partnerens indkomst, når partneren ikke er pensionist (A4)

- **Beslutning**:
  - Partnerens AM-bidragspligtige arbejdsindkomst indgår ikke i indtægtsgrundlaget.
  - Af partnerens øvrige indkomst (private pensionsudbetalinger, kapitalindkomst, offentlige
    ydelser) ses der bort fra 54 %, så **46 % indgår**.
  - Er partneren selv pensionist, indgår partnerens øvrige indkomst fuldt ud. Partnerens
    arbejdsindkomst indgår stadig ikke.
- **Kilde**: borger.dk, "Grundbeløb og pensionstillæg" (niveau 2) og Lov om social pension
  § 32 a (niveau 1). Ældre Sagen og pensionisttilskud.dk siger det samme.
- **Registerstatus**: `verificeret` (borger.dk). Ordlyden i § 32 a i den gældende
  lovbekendtgørelse kontrolleres i opgave T-REG (se tasks).
- **Forkastet alternativ**: Legacy, hvor partnerens indkomst kun tæller, når partneren selv
  er pensionist. Det er forkert efter § 32 a.

### R2. Tidligste udbetalingsalder for private ordninger (A2)

- **Beslutning**: Reglen afhænger af, hvornår aftalen er oprettet:

  | Aftale oprettet | Tidligste udbetaling |
  |---|---|
  | Før 1/5-2007 | 60 år for personer født til og med 1958; 60½ for født 1/1–30/6-1959; 61 for født 1/7–31/12-1959; 61½ for født 1/1–30/6-1960; ellers fp-alder − 3 |
  | 1/5-2007 – 31/12-2017 | Fp-alder − 5 |
  | Fra 1/1-2018 | Fp-alder − 3 |
  | Ukendt oprettelsesdato | Den mest restriktive regel (fp-alder − 3), og det markeres |

- **Kilde**: info.skat.dk (Den juridiske vejledning C.A.10.2.8.2, niveau 2): "For
  pensionsordninger oprettet fra den 1. januar 2018, er pensionsudbetalingsalderen 3 år før
  folkepensionsalderen." Ældre Sagen bekræfter overgangsreglerne efter fødselsår.
- **Registerstatus**: 2018-reglen er `verificeret`. Overgangsreglen for aftaler før 2007 har
  status `sekundær kilde`, indtil PBL § 1 A er slået op.
- **Bemærk**: Målgruppen er født 1955 eller senere, så alle tre aftaleperioder er relevante.

### R3. Ratepensionens udbetalingsperiode og rateberegning (nyt fund: A9)

- **Beslutning**:
  - Udbetalingsperioden skal være mindst 10 år.
  - Den sidste rate må senest falde i kalenderåret 30 år efter pensionsudbetalingsalderen
    (PBL § 11 A).
  - **Årsraten = ordningens værdi ved årets begyndelse / antal resterende år** (PBL § 11 A,
    stk. 2, nr. 1). Med positivt afkast stiger raten derfor over tid.
- **Kilde**: PBL § 11 A og Den juridiske vejledning C.A.10.2.2.4.1 (niveau 1/2).
- **Konsekvens**: Legacy bruger en annuitetsformel, der giver en flad rate. Det er en
  afvigelse fra loven og registreres som **A9** i domænegrundlaget. Ved afkast 0 er de to
  metoder ens, og det bruges i differentialtesten.
- **Undtagelse**: Rateudbetaling af aldersopsparing før pensionsudbetalingsalderen er ikke
  omfattet af 10-årskravet. Det er ikke relevant for denne feature (aldersopsparing udbetales
  som engangsbeløb).

### R4. Afgift af kapitalpension (A8)

- **Beslutning**: 40 % afgift ved udbetaling efter **PBL § 25, stk. 1, nr. 1**.
  *Rettet i T-REG:* Den første version af denne research påstod, at det var § 30, og at
  legacy tog fejl. Den juridiske vejledning henviser til § 25, stk. 1, nr. 1. Legacy havde ret.
- **Kilde**: Den juridiske vejledning C.A.10.2.5.4.1 (niveau 2) henviser til 40 % afgift ved
  udbetaling.
- **Registerstatus**: Satsen er `verificeret`. Paragrafnummeret bekræftes mod lovteksten i
  T-REG.

### R5. Grænsen for aktieindkomst 2026

- **Beslutning**: Grænsen er **ikke nødvendig i denne feature**. Bufferens afkastskat er en
  antagelse (en flad procent, default 27 %) og ikke en lovberegning. Grænsen (79.400 kr. pr.
  person i 2026, flere sekundære kilder; FT-svar 2025: 75.800 kr. i 2025-niveau) noteres i
  domænegrundlaget til en senere feature om fri formue.

### R6. Restlevetid (ventetillæg ved andre aldre end 67, livsvarig horisont)

- **Beslutning**:
  - **Ventetillæg fra 67 år** bruger 2026-tabellen fra Ældre Sagen (`sekundær kilde`).
  - **Andre opsættelsesaldre** bruger lovens formel, hvis registret har en restlevetidstabel.
    Ellers bruges en flad sats på 5,71 % pr. år, der markeres som forenkling (status
    `uverificeret`).
  - **Livsvarig udbetalingshorisont** er en **antagelse** (default: til 90 år, mindst 18 år)
    og ikke en registerpost.
- **Begrundelse**: Udbetaling Danmarks restlevetidstabel og Finanstilsynets
  levetidsbenchmark er ikke fundet i maskinlæsbar form. Strukturen (en valgfri tabel i
  registret) gør det muligt at tilføje den senere uden at ændre koden (SC-006).

### R6b. Middellevetider (opdatering under implementeringen)

- **Fund**: Beskæftigelsesministeriets *Vejledning om regulering pr. 1. januar 2026 af satser*
  (VEJ nr. 10077 af 10/11/2025), tabel 16, indeholder de officielle middellevetider i
  måneder til venteprocenten for livsvarigt tillæg (alder 65–80 år, pr. måned).
- **Beslutning**: Tabellen erstatter Ældre Sagens 67-tabel og den flade fallback. Den
  reproducerer Ældre Sagens tal eksakt (12/210 = 5,71 %, 120/133 = 90,23 %). Opsættelse kan
  nu beregnes korrekt for alle folkepensionsaldre (67–70) uden forenkling.
- **Samme vejledning** (tabel 12 og 15) er nu primærkilde for grundbeløb, pensionstillæg,
  fradragsbeløb, aftrapningsprocenter, tillægsprocentens grænser og trin, partnerandelen
  på 54 %, ældrecheck, minimumsbeløb og mediecheck.
- **Risiko**: Fradragsbeløbene på 99.200 og 198.800 kr. og tillægsprocentens bundgrænser
  indeholder en **midlertidig forhøjelse** (§ 49 c: 9.800 og 19.700 kr.). Bortfalder den,
  falder grænserne i fremtidige år. Kernen satsregulerer i dag hele beløbet. Udløbsdatoen
  afklares i T-REG.

### R7. Kommuneskat 2026

- **Beslutning**: Overtag legacy-tabellen (98 kommuner) som registerdata med kilden
  "Skatteministeriet, Kommuneskattesatser 2026 (svmn.dk)". Status er `sekundær kilde`,
  indtil den er krydstjekket mod det officielle regneark i T-REG. Kirkeskat er input pr.
  person (default 0,7 %).

---

## Del B — Tekniske valg

### T1. Sprog og runtime

- **Beslutning**: Python ≥ 3.11 (installeret: 3.11.9). Valgt af brugeren 2026-10-24.
- **Begrundelse**:
  - Legacy er Python, så differentialtesten kan importere `legacy/engine.py` direkte.
  - Domænet er beregningstungt og ikke I/O-tungt.
  - Senere features (web-API, PDF-import, AI) har modne Python-biblioteker.

### T2. Afhængigheder

- **Beslutning**:
  - **Kernen**: ingen runtime-afhængigheder. Den bruger kun standardbiblioteket, inkl.
    `tomllib` til registret.
  - **Test**: `pytest` og `hypothesis` (property-baserede tests af invarianter som
    monotonicitet og "skat ≤ indkomst").
  - **Projektstyring**: `uv` med `pyproject.toml`.
- **Begrundelse**: Princip IX (simpelhed). `hypothesis` er den ene tilføjede
  testafhængighed. Den er begrundet ved, at tærskel- og aftrapningsregler har mange
  grænsetilfælde, som håndskrevne cases ikke dækker.

### T3. Talrepræsentation

- **Beslutning**: `float` internt. Der afrundes kun i præsentation, og testene bruger en
  tolerance (0,01 kr. for regelfunktioner og 1 kr. for fremskrivninger). Undtagelse:
  - **Tillægsprocentens trin** beregnes med heltal, så "påbegyndt trin" er eksakt.
- **Begrundelse**:
  - Kernen er en fremskrivning og ikke en skatteopgørelse. Renters rente, potenser og
    annuiteter er naturlige i `float`.
  - `Decimal` giver ingen reel præcisionsgevinst over 40 år med usikre antagelser, men gør
    koden tungere.
  - Legacy er `float`, så differentialtesten bliver enkel.
- **Forkastet alternativ**: `Decimal` overalt.

### T4. Regelregistrets format

- **Beslutning**: Én TOML-fil pr. satsår (`register/2026.toml`) plus `kommuner_2026.toml`.
  Hver post har `id`, `vaerdi`, `enhed`, `kilde`, `status` og `reguleres` (om beløbet
  satsreguleres i fremtidige år).
- **Begrundelse**:
  - Data og kode er adskilt (Princip II).
  - Formatet kan læses og reviewes af ikke-udviklere.
  - `tomllib` findes i standardbiblioteket.
  - Et nyt satsår er en ny fil (SC-006).
- **Forkastet alternativ**: Python-moduler med dataclasses, som i legacy. De blander data og
  kode og gør det fristende at regne i registret.

### T5. Sporing

- **Beslutning**: Alle opslag i registret og antagelserne går gennem ét `Regelopslag`-objekt
  pr. beregnet år. Det registrerer de brugte id'er og flag (forenkling, uverificeret,
  sekundær) og håndhæver streng tilstand.
- **Begrundelse**: Sporingen bliver en sideeffekt af selve opslaget, så den ikke kan glemmes
  (FR-071 og SC-004).

### T6. Arkitektur

- **Beslutning**: Rene funktioner pr. regelområde:
  - `skat`
  - `folkepension`
  - `ydelser`
  - `ordninger`
  - `opsat`
  - `udbetalingsalder`

  `fremskrivning` orkestrerer år for år. `jaevn` er et separat lag oven på
  fremskrivningen (US7). Den offentlige grænseflade er én funktion, `beregn(...)`, plus
  input- og output-dataklasser.
- **Begrundelse**: Princip VI. Hver regel kan testes isoleret mod golden cases.

### T7. Differentialtest mod legacy

- **Beslutning**: `tests/differential/` importerer `legacy/engine.py` og sammenligner tre
  lag:
  1. **Regelfunktioner med uændret regel** skal være ens på ±0,01:
     - progressiv skat
     - pensionstillæg (enlig og gift-begge-pensionister)
     - tillægsprocent
     - ældrecheck uden minimumsregel
     - fp-alder
     - fremtidsværdi (FV)
  2. **Fulde fremskrivninger med afkast 0**, hvor A9 ikke giver forskel. Her skal
     nettoforskellen pr. år svare til den beregnede effekt af A1 (AM-bidrag ×
     (1 − marginalskat)) + A3 (skat af mediecheck) ± 1 kr.
  3. **Øvrige profiler**: Forskelle rapporteres i en tabel og skal være forklaret ved et
     A-nummer i testens forventningsfil.
- Testen springes over (skip med besked), hvis `legacy/` ikke findes.

### T8. Ydelser med selvreference

- **Problem**: Ældrecheck og mediecheck er skattepligtige, men indgår ikke selv i
  indtægtsgrundlaget. Skatten afhænger dog af den samlede personlige indkomst, som også
  omfatter dem.
- **Beslutning**: Beregn rækkefølgen i et år sådan:
  1. Indtægtsgrundlag
  2. Pensionstillæg, tillægsprocent, ældrecheck og mediecheck
  3. Samlet personlig indkomst (inkl. checks)
  4. Skat

  Der er ingen iteration, fordi indtægtsgrundlaget ikke afhænger af checks eller skat.
  Legacy beskattede ældrechecken separat med en lille inkonsistens. Det rettes her.

---

## T-REG status (2026-10-24) — afsluttet

Primærkilder: lov om social pension (LBK nr. 1123 af 21/10/2024), VEJ nr. 10077/2025,
Den juridiske vejledning og Skatteministeriets regneark kommuneskattesatser_2026.xlsx.

| Punkt | Resultat |
|---|---|
| § 29, stk. 5 / § 49, stk. 1, nr. 4 (54 %) | ✅ bekræftet. Partnerens arbejdsindkomst ses der helt bort fra (§ 29, stk. 1, nr. 10) |
| § 29, stk. 6 | 🆕 **A11**: indtægtsgrundlaget afrundes nedad til 100 kr. Implementeret |
| § 49 c | 🆕 **A12**: forhøjelsen af fradragene aftrappes lineært til 0 i 2034. Fradragene er delt i grundbeløb og forhøjelse. Implementeret |
| § 1 a | 🆕 **A10**: født 1.1.–30.6.1955 → 66½ år. Kernen understøtter født ≥ 1.7.1955 |
| § 31, stk. 2 | ✅ "nedsættes med 1 pct. for hvert beløb" → fulde trin (som implementeret) |
| § 15 e, stk. 1 | ✅ venteprocent afrundes til to decimaler |
| § 72 d | ✅ kræver ret til folkepension inden 1. januar (som implementeret); formuegrænsen gælder husstandens samlede formue |
| PBL § 11 A | ✅ JV C.A.10.2.2.4.1 |
| PBL § 25, stk. 1, nr. 1 (40 %) | ✅ — A8 var en fejl i plan-researchen, ikke i legacy |
| Kommuneskat 2026 | ✅ alle 98 identiske med Skatteministeriets regneark. Kirkeskat pr. kommune tilføjet fra samme regneark. Regnearkets "Nedslag" = kommuneskat − 25,06 = skatteloftsnedslaget, som kernen beregner |
| PBL § 1 A (aftaler før 2007, overgang efter fødselsdato) | ⏳ fortsat `sekundaer` (Ældre Sagen). Bruges kun ved ukendt oprettelsesdato eller aftaler før 2007 |

Registret: 47 af 48 poster er `verificeret` (98 %), og kommuneregistret er `verificeret`.
Streng tilstand kan nu beregne almindelige profiler.
