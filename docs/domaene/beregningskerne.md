# Domænegrundlag: Beregningskerne

**Formål**: Input til `/speckit-constitution` og `/speckit-specify` for den første feature
(beregningskerne + satsregister). Samler den domæneviden, der ligger i `legacy/`, og holder
hver regel op mod gældende lovgivning/officielle kilder (gennemgang 2026-10-24).

**Status pr. regel**:
- ✅ **Bekræftet** — legacy-reglen og 2026-værdien stemmer med officiel kilde
- ⚠️ **Afvigelse** — legacy gør noget andet end lovgivningen; den nye kerne skal gøre det rigtigt
- 🟡 **Forenkling** — legacy er en bevidst tilnærmelse; skal være et eksplicit valg i spec
- ❓ **Ikke verificeret** — skal afklares (kandidat til `/speckit-clarify`)

Dokumentet er teknologiuafhængigt. Henvisninger til `legacy/…` er kun sporbarhed.

---

## 1. Afvigelser fra lovgivning fundet i legacy (prioriteret)

| # | Fund | Konsekvens | Kilde |
|---|---|---|---|
| A1 | ⚠️ **AM-bidrag trækkes af private pensionsudbetalinger** (rate/livrente, S-beskattet). AM-bidrag betales ved *indbetaling* til arbejdsgiverordninger og **aldrig ved udbetaling** fra pensionsinstitutter. (`legacy/engine.py` `_netto_s(..., har_am_bidrag=True)`) | Nettoudbetaling fra private ordninger undervurderes systematisk (~8 % af brutto før skat). Påvirker også den personlige indkomst og dermed mellemskat-vurdering. **Største enkeltfejl.** | SKAT: "betales der AM-bidrag ved indbetalingen til ordningen og aldrig ved udbetalingen fra ordningen" (info.skat.dk oid=79226, afsnit B.3); PFA skatteregler. Undtagelse: uafdækkede (direkte) ordninger. |
| A2 | ⚠️ **Tidligste udbetalingsalder = folkepensionsalder − 5 for alle ordninger.** Reglen afhænger af hvornår aftalen er oprettet: før 1/5-2007 → 60 år (overgang efter fødselsår); 1/5-2007–31/12-2017 → fp-alder − 5; fra 2018 → fp-alder − 3 (❓ skal bekræftes for 2018+). | Kan foreslå udbetalingsstart, som ordningen ikke tillader. | Ældre Sagen, "Pensionsudbetalingsalder"; Nordnet-eksempel (2020-aftale: −3 år). |
| A3 | ⚠️ **Mediecheck behandles som skattefri.** Den er skattepligtig ("1.552 kr. (2026) før skat"). Kræver desuden tilkendt folkepension senest 1. januar. | Lille overvurdering af netto (≈ 1.552 × marginalskat/år). | borger.dk, mediecheck |
| A4 | ⚠️ **Partnerens indkomst tælles kun med, når partneren selv er folkepensionist.** Reglen: ægtefællens/samleverens øvrige indkomst (private pensioner, kapitalindkomst, offentlige ydelser) indgår altid; AM-bidragspligtig arbejdsindkomst indgår ikke (lempet fra 2023/2025). Er partneren ikke pensionist, ses der bort fra en del af partnerens indkomst (❓ omfang skal verificeres) og aftrapningen er 32 %. | Pensionstillæg kan overvurderes i år, hvor partneren er under fp-alder men har pensionsudbetalinger. | borger.dk, grundbeløb og pensionstillæg; Ældre Sagen; FT-svar BEU spm. 31 (2023-24) |
| A5 | ⚠️ **Kapital- og aktieindkomst indgår ikke i indtægtsgrundlaget** for pensionstillæg/tillægsprocent. Nettokapitalindkomst og aktieindkomst (udbytte over 5.000 kr.) tæller. Relevant når engangsbeløb placeres som fri formue/buffer. | Pensionstillæg og ældrecheck kan overvurderes for brugere med fri formue. | borger.dk |
| A6 | ⚠️ **Ældrecheck under 200 kr. udbetales ikke.** Mangler i legacy. | Marginal. | borger.dk, ældrecheck |
| A7 | 🟡 **Folkepensionsalder 70 for født 1971+ beskrevet som "ikke endeligt vedtaget".** Den blev vedtaget i maj 2025 (L 149). Værdien i legacy er korrekt — kun begrundelsen er forældet. | Ingen beregningsfejl. | Folketinget L 149 (2024-25); lex.dk |
| A8 | ❓ Kildehenvisning for 40 % afgift af kapitalpension angivet som "PBL § 25" — skal efterprøves (afgiftsbestemmelserne står i PBL kap. 5). Satsen 40 % antages korrekt. | Kildesporbarhed. | — |

---

## 2. Regler og satser 2026

### 2.1 Indkomstskat (personlig indkomst)

| Regel | 2026-værdi | Status | Kilde |
|---|---|---|---|
| Bundskat | 12,01 % | ✅ | PSL § 6; skat.dk |
| Personfradrag (voksne) | 54.100 kr. | ✅ | Skatteministeriet, PSL § 10/20 |
| Mellemskat | 7,5 % af PI over 641.200 kr. | ✅ | PSL § 7 (L 138, 2023-24); skat.dk |
| Topskat | 7,5 % af PI over 777.900 kr. | ✅ | PSL § 7 a; skat.dk |
| Top-topskat | 5 % af PI over 2.592.700 kr. | ✅ (en kilde siger 2.592.500 — brug skat.dk) | PSL § 8; skat.dk |
| Skrå skatteloft | 44,57 % / 52,07 % / 57,07 % (mellem/top/top-top), ekskl. kirkeskat | ✅ | PSL § 19 stk. 1 |
| Kommuneskat | Pr. kommune (98 satser) | ✅ (legacy har 2026-tabel fra svmn.dk) | Skatteministeriet |
| Kirkeskat | Pr. kommune, valgfri | 🟡 legacy bruger 0,7 % default | — |
| AM-bidrag | 8 % — **kun** af lønindkomst og pensionsindbetalinger, ikke udbetalinger | ⚠️ se A1 | AMBL § 1; SKAT |
| Pensionsafkastskat (PAL) | 15,3 % | ✅ | PAL § 2 |
| Aktieindkomst | 27 % op til 79.400 kr., derefter 42 % | ❓ en kilde siger 63.300 kr. | dinero.dk, Ældre Sagen |

**Skatteloft — vigtig egenskab**: Fordi hvert loft er netop "forrige loft + trinsatsen", er
nedslaget pr. krone ens på alle tre trin (= kommuneskat − 25,06 %, hvis positiv), og det
gælder for al PI over mellemskattegrænsen. Legacy udnytter dette og er dermed korrekt — den
nye kerne skal have en test, der fastholder det.

### 2.2 Folkepension

| Regel | 2026-værdi | Status | Kilde |
|---|---|---|---|
| Grundbeløb | 7.544 kr./md. (90.528 kr./år), uafhængigt af anden indkomst | ✅ | Ældre Sagen; borger.dk |
| Pensionstillæg, enlig | 8.729 kr./md. (104.748 kr./år) | ✅ | Ældre Sagen |
| Pensionstillæg, gift/samlevende | 4.467 kr./md. (53.604 kr./år) | ✅ | Ældre Sagen |
| Fradragsbeløb, enlig | 99.200 kr.; aftrapning 30,9 %; bortfald 438.200 kr. | ✅ (104.748/0,309 + 99.200 = 438.190) | borger.dk |
| Fradragsbeløb, gift — begge pensionister | 198.800 kr.; 16 % (hver); bortfald 533.800 kr. | ✅ (53.604/0,16 + 198.800 = 533.825) | borger.dk |
| Fradragsbeløb, gift — partner ikke pensionist | 198.800 kr.; 32 %; bortfald 366.400 kr. | ✅ (53.604/0,32 + 198.800 = 366.312) | borger.dk |
| Indtægtsgrundlag | ATP, private pensionsudbetalinger, nettokapitalindkomst, aktieindkomst (> 5.000 kr. udbytte), underholdsbidrag; partners øvrige indkomst. **Ikke** egen arbejdsindkomst. | ⚠️ se A4, A5 | borger.dk |
| Folkepensionsalder | 67 (født 1955–1962), 68 (1963–1966), 69 (1967–1970), 70 (1971+) | ✅ (A7) — ❓ født før 1955 er ikke modelleret | Lov om social pension § 1a; L 149 |
| Satsregulering 2027 | 2,6 % | ✅ (info) | Ældre Sagen |

### 2.3 Personlig tillægsprocent og afledte ydelser

| Regel | 2026-værdi | Status | Kilde |
|---|---|---|---|
| Tillægsprocent, enlig | 100 % op til 35.700 kr.; −1 point pr. påbegyndt 635 kr.; 0 ved 99.200 kr. | ✅ | Ældre Sagen |
| Tillægsprocent, gift | 100 % op til 70.600 kr.; −1 point pr. 1.282 kr.; 0 ved 198.800 kr. | ✅ | Ældre Sagen |
| Ældrecheck | 26.900 kr./år × tillægsprocent; skattepligtig; < 200 kr. udbetales ikke | ✅ / ⚠️ A6 | borger.dk |
| Formuegrænse ældrecheck | Likvid formue ≤ 108.000 kr. pr. 1. januar (samme for par). Hård tærskel. | ✅ | borger.dk |
| Mediecheck | 1.552 kr./år, kræver tillægsprocent 100 og folkepension tilkendt senest 1/1; **skattepligtig**; ikke formueafhængig | ✅ / ⚠️ A3 | borger.dk |
| Tillægsprocent ≠ pensionstillæggets aftrapning | To uafhængige regler — må aldrig slås sammen | ✅ | (legacy-invariant, golden G-42) |

### 2.4 Opsat folkepension (ventetillæg)

| Regel | Værdi | Status | Kilde |
|---|---|---|---|
| Formel | venteprocent = opsatte måneder / gennemsnitlig restlevetid i måneder ved den alder, opsættelsen ophører; afrundet. Ganges på grundbeløb **og** pensionstillæg. | ✅ | Ældre Sagen; Lovguiden § 90 |
| Tabel fra 67 år (2026) | 1: 5,71 · 2: 11,94 · 3: 18,75 · 4: 26,23 · 5: 34,48 · 6: 43,37 · 7: 53,50 · 8: 64,43 · 9: 76,60 · 10: 90,23 % | ✅ (primærkilde: restlevetidstabel i Udbetaling Danmarks satsvejledning ❓) | Ældre Sagen |
| Betingelse | ≥ 750 arbejdstimer pr. år i opsættelsesperioden; maks. 10 år; højst 2 perioder | ✅ — legacy tjekker ikke kravet | Ældre Sagen |
| Udbetalingsformer (optjent fra 1/7-2018) | Livsvarigt tillæg (default) · forhøjet tillæg i 10 år · engangsbeløb for grundbeløb + 10-årigt forhøjet tillæg | 🟡 legacy modellerer kun livsvarigt | Ældre Sagen |
| Andre opsættelsesaldre end 67 | Kræver restlevetidstabel | 🟡 legacy bruger flad 5,71 %/år (ikke verificeret) | — |

### 2.5 Private pensionsordninger

| Regel | 2026-værdi | Status | Kilde |
|---|---|---|---|
| Ratepension — fradragsloft for indbetaling | 68.700 kr./år; overskydende → livsvarig | ✅ | skat.dk |
| Ratepension — udbetalingsperiode | 10–30 år (legacy: fra PDF, ellers 15) | ❓ lovens min./maks. skal bekræftes | PBL |
| Livrente/livsvarig | Udbetales livsvarigt; kerne skal bruge en udbetalingshorisont | 🟡 legacy: max(18, 90 − startalder) | Finanstilsynets levetidsbenchmark (❓) |
| Aldersopsparing — indbetalingsloft | 9.900 kr.; 64.200 kr. hvis < 7 år til fp-alder | ✅ | skat.dk JV C.A.10.2.6.3.3.1 |
| Aldersopsparing — udbetaling | Skattefri (afgift betalt ved indbetaling) | ✅ | PBL |
| Kapitalpension (oprettet før 2013) | 40 % afgift ved udbetaling | ✅ sats / ❓ paragraf (A8) | PBL |
| Tidligste udbetaling | Afhænger af oprettelsesdato | ⚠️ se A2 | Ældre Sagen |
| Livsvarig påbegyndt før fp-alder | Ydelsen reduceres | 🟡 ikke modelleret (PDF'ens tal antages at afspejle det) | Ældre Sagen |
| ATP Livslang Pension | Fra fp-alder; påvirkes ikke af opsat folkepension; fallback 1.445 kr./md. (gennemsnit) | ✅ | ATP.dk |
| Engangscheck 2026 | 2.500 kr. skattefri (formue ≤ 350.000 kr.) — engangsforekomst | 🟡 bevidst ikke modelleret | fm.dk |

---

## 3. Modelleringsantagelser (ikke lovgivning — skal være eksplicitte valg)

Disse er ikke regler, der kan "valideres mod loven". Det er antagelser, som spec'en skal
nævne og brugeren skal kunne se:

1. **Afkast er efter PAL-skat** (brugerens input). PAL indgår derfor ikke selv i beregningen.
2. **Satsregulering af skattegrænser, folkepension og ATP i fremtidige år** — legacy bruger
   inflationsantagelsen som proxy. Reelt følger satsreguleringen lønudviklingen (2027: 2,6 %).
   Forslag: separat parameter "satsreguleringsprocent" med inflation som default.
3. **Fremskrivning af saldo**: FV med evt. voksende indbetalinger (lønvækst) frem til start.
4. **Udbetaling som annuitet** over perioden med samme afkast.
5. **Proportional fordeling af progressiv skat og personfradrag** på indkomststrømme
   (for at kunne vise netto pr. ordning). Summen er korrekt; fordelingen er en konvention.
6. **Engangsbeløb som "buffer"/jævn udbetaling**: netto engangsbeløb placeres frit og
   forrentes efter en flad kapitalskat (legacy 27 %), og der beregnes et udjævnet månedligt
   niveau, der stiger med inflationen. Det er en præsentationsmodel, ikke et lovkrav.
7. **Ingen arbejdsindkomst efter pensionsalderen** (påvirker hverken pensionstillæg eller
   750-timers-kravet i modellen).
8. **Livsvarig horisont**: legacy bruger levetid til 90 år, mindst 18 år. Bør erstattes af en
   kildet levetidsantagelse eller en eksplicit brugerparameter.
9. **Fødselsdags-uafhængig kalenderårsomregning** mellem to personer i en husstand.

---

## 4. Invarianter fra legacy, der bør overføres

- **Beregning er deterministisk og fuldført, før nogen AI præsenterer tal.** AI'en beregner aldrig.
- **Ét kildested pr. sats** med værdi, kilde (lov/URL), gyldighedsår og verifikationsstatus.
  Legacy havde tidligere flere modstridende kopier af samme sats, og det gav reelle fejl.
- **Sporbarhed**: hvert beregnet tal kan føres tilbage til de satser/regler, der blev brugt
  (legacy: `spor`-liste og "strict mode", der afviser uverificerede satser).
- **Tre separate pensionstillægsregler** (enlig / gift-begge-pensionister / gift-partner-ikke-
  pensionist), som vælges år for år efter partnerens status.
- **Advarsler** som en del af resultatet (ratepension over loft, høj marginalskat i
  aldersintervaller, usikker venteprocent osv.).

---

## 5. Golden cases (facit fra legacy, bekræftet mod 2026-satser)

Disse kan overføres direkte som acceptkriterier. De rører ikke AM-bidrag (A1), så de er
fortsat gyldige.

| ID | Input | Forventet |
|---|---|---|
| G-02 | PI = 641.200 kr., kommune 25 % | Progressiv skat = 0 |
| G-02b | PI = 741.200 kr., kommune 25 % | Progressiv skat = 7.500 kr. |
| G-03 | PI = 900.000 kr., kommune 25 % | (900.000−641.200)·7,5 % + (900.000−777.900)·7,5 % = 28.567,50 kr.; intet loftnedslag |
| G-03b | PI = 900.000 kr., kommune 25,71 % | Loftnedslag > 0 (marginal 52,72 % > 52,07 %) |
| G-40 | Tillægsprocent enlig | 0 kr.→100; 35.700→100; 36.335→99; 99.200→0 |
| G-41 | Tillægsprocent gift | 70.600→100; 198.800→0 |
| G-42 | Enlig, indtægtsgrundlag 99.200 kr. | Tillægsprocent 0, men pensionstillæg uberørt = 104.748 kr. |
| G-43 | Formue 108.000 / 108.001 kr., tillægsprocent 100 | Ældrecheck 26.900 / 0; mediecheck uændret |
| FP-1 | Født 1962 / 1963 / 1967 / 1971 | Fp-alder 67 / 68 / 69 / 70 |
| PT-1 | Gift, indtægtsgrundlag 300.000 kr. | Begge pensionister (16 %) giver højere tillæg end partner ikke pensionist (32 %) |
| VT-1 | Opsættelse fra 67 i 3 år | Grundbeløb og tillæg × 1,1875 |

**Differentialtest mod legacy**: Ud over golden cases kan den nye kerne køres mod
`legacy/engine.py` på et sæt testprofiler. Alle forskelle skal kunne forklares af A1–A6
eller af bevidste ændringer i antagelserne (afsnit 3).

---

## 6. Åbne spørgsmål til `/speckit-clarify`

1. Hvor stor en del af en ikke-pensionist-partners indkomst ses der bort fra i
   pensionstillæggets indtægtsgrundlag i 2026 (A4)? Kræver primærkilde (Lov om social
   pension § 32 a / Udbetaling Danmark).
2. Udbetalingsalder for ordninger oprettet fra 2018 (A2): bekræft fp-alder − 3.
3. Skal kernen modellere personer født før 1955 (fp-alder under 67)? Forslag: nej, afvis input.
4. Skal opsat folkepension understøtte de tre udbetalingsformer eller kun livsvarigt tillæg?
5. Kilde til restlevetid (ventetillæg ved andre aldre end 67, og livsvarig horisont):
   Udbetaling Danmarks satsvejledning og/eller Finanstilsynets levetidsbenchmark.
6. Satsregulering: separat parameter eller fortsat koblet til inflation?
7. Skal kernen regne på flere satsår (2026, 2027, …), eller kun ét regelsæt ad gangen?
8. Kapital- og aktieindkomst fra fri formue/buffer: skal den indgå i indtægtsgrundlaget (A5)?
   Det kobler buffermodellen til pensionstillægget.
9. Ratepensionens tilladte udbetalingsperiode (min./maks. år).

---

## 7. Uden for denne feature (kommer i senere features)

PDF-import fra PensionsInfo · AI-forklaring/chat · Optimering af udbetalingsrækkefølge
(sekventering) · Fuld husstandsmodel med to profiler · Forsikringsanalyse · UI.

## Kilder

- [skat.dk — bundskat, mellemskat, topskat og toptopskat](https://skat.dk/hjaelp/bundskat-mellemskat-topskat-og-toptopskat)
- [info.skat.dk — AM-bidrag og pension (B.3)](https://info.skat.dk/data.aspx?oid=79226)
- [tax.dk — mellemskat](https://tax.dk/skat/mellemskat.htm) · [topskat](https://tax.dk/skat/topskat.htm)
- [Folketinget L 138 (2023-24) — skattereform, som vedtaget](https://folketingstidende.dk/samling/20231/lovforslag/L138/20231_L138_som_vedtaget.pdf)
- [Folketinget L 149 (2024-25) — folkepensionsalder](https://www.ft.dk/samling/20241/lovforslag/L149/bilag/1/2982817.pdf)
- [borger.dk — grundbeløb og pensionstillæg](https://www.borger.dk/pension-og-efterloen/folkepension-oversigt/foer-du-gaar-paa-folkepension/folkepension-grundbeloeb-pensionstillaeg)
- [borger.dk — ældrecheck](https://www.borger.dk/pension-og-efterloen/folkepension-oversigt/folkepension-aeldrecheck)
- [borger.dk — mediecheck](https://www.borger.dk/pension-og-efterloen/tillaeg-til-folke--og-foertidspension/mediecheck)
- [Ældre Sagen — folkepensionens størrelse](https://www.aeldresagen.dk/viden-og-raadgivning/vaerd-at-vide/f/folkepension-og-foertidspension/folkepension/folkepensionens-stoerrelse)
- [Ældre Sagen — opsat folkepension](https://www.aeldresagen.dk/viden-og-raadgivning/vaerd-at-vide/f/folkepension-og-foertidspension/folkepension/opsat-folkepension)
- [Ældre Sagen — pensionsudbetalingsalder](https://www.aeldresagen.dk/viden-og-raadgivning/vaerd-at-vide/p/pensioner---private/forskellige-oplysninger-om-pension/pensionsudbetalingsalder)
- [Ældre Sagen — den personlige tillægsprocent](https://www.aeldresagen.dk/viden-og-raadgivning/vaerd-at-vide/f/folkepension-og-foertidspension/folkepension/den-personlige-tillaegsprocent)
- [Lovguiden — § 90 opgørelse af venteprocent](https://www.lovguiden.dk/loven/vejledning-om-ansøgning-om-folkepension-samt-tillæg-til-folkepension-og-førtidspension-tilkendt-efter-reglerne-før-2003/90-opgørelse-af-venteprocent-ved-livsvarigt-tillæg)
- [lex.dk — folkepension og pensionsalder](https://lex.dk/folkepension_og_pensionsalder)
- [dinero.dk — personfradrag](https://dinero.dk/ordbog/personfradrag/) · [bundskat](https://dinero.dk/ordbog/bundskat)
- [Nordnet — hvornår kan jeg få udbetalt min pension](https://www.nordnet.dk/dk/kundskab/academy/pension/hvornar-kan-jeg-fa-udbetalt-min-pension)
