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
| A6 | ⚠️ **Ældrecheck under 200 kr. udbetales ikke.** Mangler i legacy. | Ingen med 2026-satser: laveste tillægsprocent (1) giver 269 kr. Implementeret for fremtidige satser. | borger.dk, ældrecheck |
| A7 | 🟡 **Folkepensionsalder 70 for født 1971+ beskrevet som "ikke endeligt vedtaget".** Den blev vedtaget i maj 2025 (L 149). Værdien i legacy er korrekt — kun begrundelsen er forældet. | Ingen beregningsfejl. | Folketinget L 149 (2024-25); lex.dk |
| A8 | ✅ ~~Forkert paragraf~~ — **legacy havde ret**: 40 % afgift af kapitalpension står i PBL § 25, stk. 1, nr. 1 (Den juridiske vejledning C.A.10.2.5.4.1). Plan-researchens "rettelse" til § 30 var forkert og er trukket tilbage (T-REG). | Ingen. | JV C.A.10.2.5.4.1 |
| A9 | ⚠️ **Ratepension udbetales som annuitet (flad rate).** Loven: årsraten = ordningens værdi ved årets begyndelse / antal resterende år. Med positivt afkast stiger raten over tid. (Fundet i plan-research 2026-10-24.) | Forkert fordeling over årene: for høj tidligt og for lav sent. Det påvirker skat og modregning i de enkelte år. Ved afkast 0 er metoderne ens. | PBL § 11 A, stk. 2, nr. 1; JV C.A.10.2.2.4.1 |
| A10 | ⚠️ **Folkepensionsalder 67 for alle født før 1963.** Lov om social pension § 1 a: født 1.1.–30.6.1955 → 66½ år (og tidligere årgange lavere). Fundet i T-REG. | Forkert fp-alder for årgang 1955, 1. halvår. Den nye kerne understøtter født 1.7.1955 og senere og afviser tidligere. | LBK 1123/2024 § 1 a |
| A11 | ⚠️ **Indtægtsgrundlaget afrundes ikke.** § 29, stk. 6: den opgjorte indtægt afrundes nedad til nærmeste 100 kr. Fundet i T-REG. | Op til ~30 kr./år i pensionstillæg og ét procentpoint i tillægsprocenten ved grænserne. | LBK 1123/2024 § 29, stk. 6 |
| A12 | ⚠️ **Fradragsbeløbene satsreguleres som faste beløb.** 9.800 kr. (enlig) / 19.700 kr. (gift) af fradragene for pensionstillæg og tillægsprocent er en midlertidig forhøjelse (§ 49 c), der aftrappes lineært og er 0 i 2034. Fundet i T-REG. | Pensionstillæg op til ~3.000 kr./år (enlig) og ~6.300 kr./år (gift, 32 %) for højt fra 2034 og frem, gradvist fra 2027. Tillægsprocent og ældrecheck tilsvarende for høje. | LBK 1123/2024 § 49 c; VEJ 10077/2025 tabel 15 |

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
| Middellevetider 2026 | Officiel tabel: VEJ nr. 10077/2025, tabel 16 (alder 65–80). Reproducerer tabellen nedenfor eksakt | ✅ | Beskæftigelsesministeriet |
| Tabel fra 67 år (2026) | 1: 5,71 · 2: 11,94 · 3: 18,75 · 4: 26,23 · 5: 34,48 · 6: 43,37 · 7: 53,50 · 8: 64,43 · 9: 76,60 · 10: 90,23 % | ✅ (primærkilde: restlevetidstabel i Udbetaling Danmarks satsvejledning ❓) | Ældre Sagen |
| Betingelse | ≥ 750 arbejdstimer pr. år i opsættelsesperioden; maks. 10 år; højst 2 perioder | ✅ — legacy tjekker ikke kravet | Ældre Sagen |
| Udbetalingsformer (optjent fra 1/7-2018) | Livsvarigt tillæg (default) · forhøjet tillæg i 10 år · engangsbeløb for grundbeløb + 10-årigt forhøjet tillæg | 🟡 legacy modellerer kun livsvarigt | Ældre Sagen |
| Andre opsættelsesaldre end 67 | Kræver restlevetidstabel | 🟡 legacy bruger flad 5,71 %/år (ikke verificeret) | — |

### 2.5 Private pensionsordninger

| Regel | 2026-værdi | Status | Kilde |
|---|---|---|---|
| Ratepension — fradragsloft for indbetaling | 68.700 kr./år; overskydende → livsvarig | ✅ | skat.dk |
| Ratepension — udbetalingsperiode | Mindst 10 år. Sidste rate senest i kalenderåret 30 år efter pensionsudbetalingsalderen. Årsrate = værdi primo / resterende år | ✅ / ⚠️ A9 | PBL § 11 A; JV C.A.10.2.2.4.1 |
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

> **Forenklingsregistret** (`src/pensionskerne/register/forenklinger.toml`, feature 020) er den
> gældende liste over forenklinger med begrundelse og betydning. Borgeren ser den under "Sådan har
> vi regnet". Listerne over forenklinger i dette dokument er historik pr. feature. En test kræver,
> at hver markering i kernen (`o.marker("forenkling:…")`) står i registret.

Disse er ikke regler, der kan "valideres mod loven". Det er antagelser, som spec'en skal
nævne og brugeren skal kunne se:

1. **Afkast er efter PAL-skat** (brugerens input). PAL indgår derfor ikke selv i beregningen.
2. **Satsregulering af skattegrænser, folkepension og ATP i fremtidige år** — legacy bruger
   inflationsantagelsen som proxy. Reelt følger satsreguleringen lønudviklingen (2027: 2,6 %).
   Forslag: separat parameter "satsreguleringsprocent" med inflation som default.
3. **Fremskrivning af saldo**: FV med indbetalinger, der følger satsreguleringen (017b) plus evt.
   realvækst (`loenvaekst`), frem til start.
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

## 6. Åbne spørgsmål

*Status 2026-10-24: Spørgsmål 1, 2, 4, 6, 8 og 9 er afklaret. Se
[specs/001-beregningskerne/spec.md](../../specs/001-beregningskerne/spec.md) (Clarifications) og
[research.md](../../specs/001-beregningskerne/research.md) R1–R6. Spørgsmål 3 er besluttet
(afvis født før 1955). Spørgsmål 5 er delvist afklaret (fallback markeres). Spørgsmål 7: et
satsår ad gangen pr. beregning, men flere satsår i registret.*

1. ✅ Der ses bort fra 54 % af en ikke-pensionist-partners øvrige indkomst. AM-pligtig
   arbejdsindkomst indgår ikke (R1).
2. ✅ Aftaler oprettet fra 2018: fp-alder − 3 (R2).
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

## 7. Legacy-afvigelser i PDF-indlæsningen (rettet i feature 003)

- **PDF-cache:** Legacy gemte udtrukne profiler med persondata permanent i `.pdf_cache/`. Den
  nye løsning skriver intet til disk (testet).
- **CPR til AI-tjenesten:** Legacy sendte rapportens CPR-nummer til AI-tjenesten. Nu fjernes
  CPR lokalt, og fødselsdatoen udledes lokalt.
- **Århundrede i CPR:** Legacy antog 1900-tallet. Nu bruges 7.-ciffer-reglen.
- **Persondata til AI (A13):** Legacy sendte rapportteksten (navn, CPR, aftaler, saldi) og
  brugerens profil og beregning til Claude, både ved PDF-udtræk og i chatten. Det strider mod
  NFR'en "ingen persondata til AI/LLM" (Princip XI). Den nye løsning sender intet til AI.
  PDF-aflæsningen skal ske lokalt, og en kommende forklaringsfunktion må kun bruge generisk indhold.

## 7b. Fund fra en rigtig PensionsInfo-rapport (2026-10-25)

- **A14 (register):** Aftaler oprettet før 1.5.2007 kan udbetales fra 60 år. Det gælder også for en
  person født 1971 ("Pensionen kan tidligst udbetales fra 60 år"). Registrets tidligere
  overgangstabel efter fødselsdato gav fp-alder − 3 = 67 og ville have afvist rigtige aftaler.
  Rettet til 60 år (`sekundaer`). Selskabets oplyste alder overstyrer nu altid reglen.

## 7c. Optimeringen i forhold til legacy (feature 007)

`pensionskerne/optimering.py` porterer `legacy/sekventering.py`. Afvigelser:

| # | Legacy | Ny | Hvorfor |
|---|---|---|---|
| O1 | Mål: legacys ene jævne niveau | Det laveste jævne beløb fra første udbetaling ("fast beløb hele perioden") | Kernens jævne model stiger ved senere engangsbeløb. Hovedtallet alene belønnede at skubbe engangsbeløb sent (fundet i T003) |
| O2 | Engangsbeløb kunne spredes ("kapital_rate") | Ikke med | Kernen har ikke den udbetalingsform |
| O3 | Opsættelse {0, 1, 2, 3, 5} | 0 til registrets maksimum (10) | Grænsen fra registret (Princip II) |
| O4 | Startalder til pensionsalder + 10 | Til folkepensionsalder + registrets maksimale opsættelse | Kernen har ingen pensionsalder |
| O5 | Værn på legacys tabel | Samme fem værn på kernens jævne model, med "under 1 kr." som nul for bufferen | Regnestøj ved bufferens nulpunkt gav forskellige planer i CPython og WebAssembly (T006) |
| O6 | Top 5 og følsomhed | Kun bedste forslag | Princip X (klarhed før fuldstændighed) |

## 7d. Kapitalpension og bufferen (feature 009)

**Nye regler** (alle i registret med kilde, se `specs/009-kapitalpension/research.md`):
- Kapitalpension kan udbetales delvist (PBL § 26), senest 20 år efter pensionsudbetalingsalderen
  (§ 25, stk. 1, nr. 7). Den kan overføres til en rate- eller livrenteordning (§ 41, stk. 1, nr. 4
  og 6), og afgift, der allerede er betalt, gør udbetalingen skattefri.
- Bufferen er opsparing uden for pension:
  - Afkastet før skat er afkastet efter PAL / (1 − 15,3 %).
  - Afkastet er positiv kapitalindkomst, beskattet efter PSL §§ 6, 7, stk. 1, og 19, stk. 2, og
    indgår i indtægtsgrundlaget (§ 29).
  - Bufferen pr. 1. januar er likvid formue (§ 72 d).
  - Fastpunktet løses deterministisk.

**Afvigelser fra legacy og fra 001:**

| # | Før | Nu | Hvorfor |
|---|---|---|---|
| B1 | Bufferen gav afkast med en fast skat på 27 % og påvirkede ikke ydelser (kun en advarsel) | Kapitalindkomst efter PSL, nedsætter pensionstillægget, formue i ældrechecken | Princip III. Det var præcis den forskel, der gør portioner mod engangsbeløb til et reelt valg |
| B2 | PDF: kapitalpension med betalt afgift blev stille lavet om til aldersopsparing | Typen bevares, og `afgift_betalt` sættes | Ærlig visning. Omlægning er ikke mulig med betalt afgift |
| B3 | Legacys "kapital_rate" som annuitet ("ikke en generel ret") | Portioner efter § 11 A-formlen af restværdien, med hjemmel i PBL § 26 | Lovhjemlen er nu verificeret |

**Forenklinger, der står tilbage** (markeret eller advaret):
- Bufferen beskattes som kapitalindkomst (bank og obligationer), ikke som aktieindkomst.
- Negativ buffer (lån af senere udbetalinger) giver intet renteudgiftsfradrag. Det advares der om.
- Ægtepars overførsel af uudnyttet bundfradrag for kapitalindkomst er ikke modelleret.
- Borgerens egen "anden kapitalindkomst" indgår i indtægtsgrundlaget, men beskattes ikke
  (markeret `kapitalindkomst_ikke_beskattet`, som før).
- Kapitalpension oprettet før 1980 (lavere afgift, PBL §§ 26 A og 27) er ikke modelleret.

## 7e. Udjævning uden lån (feature 010)

| # | Før (001 US7) | Nu | Hvorfor |
|---|---|---|---|
| J1 | Grundniveauet blev finansieret af nutidsværdien af *alle* løbende udbetalinger, så de første år kunne låne af senere udbetalinger (negativ buffer, advarsel `JAEVN_FORUDSAETTER_SENERE_UDBETALINGER`) | Det højeste forløb, der er konstant i dagens kroner og kun stiger, når flere penge kommer. Bufferen er aldrig negativ. Det beregnes som forbrugsudjævning med likviditetsbegrænsning, segment for segment | Produktejeren: "Bufferen går i minus over lange stræk." Et beløb, der kun kan nås ved at låne, er ikke et beløb, man kan leve af. For engangsbeløb gjaldt det allerede |

Hovedtallet er det første (laveste) niveau. Teksten nævner, hvornår og til hvad det stiger. Alle
beløb vises i dagens kroner (inflationskorrigeret med antagelsens inflation, som i legacy).

## 7f. Partner og husstand (feature 012)

**Koblinger efter loven:**
- Pensionstillæg og tillægsprocent beregnes af parrets samlede indtægtsgrundlag (§ 29).
- Ældrechecken ser på husstandens samlede likvide formue, inklusive begges buffer (§ 72 d,
  stk. 2).
- For ægtefæller nedsætter uudnyttet personfradrag den andens skat (PSL § 10, stk. 3), og et
  uudnyttet bundfradrag for kapitalindkomst lægges til den andens (§ 7, stk. 5).
- Gifte og samlevende behandles ens af ydelserne. Kun gifte får skatteoverførslerne.
  "gift_samlevende" (før 012) læses som samlevende.

**Afvigelser og forenklinger** i forhold til legacy (`husstand.py`):

| # | Legacy | Nu | Hvorfor |
|---|---|---|---|
| H1 | To solo-kørsler og én koblet kørsel | Fastpunkt mellem begge personer, højst 6 runder, advarsel `HUSSTAND_IKKE_KONVERGERET` | Bufferens kapitalindkomst kobler også (009) |
| H2 | Ingen skatteoverførsler | Personfradrag og bundfradrag for kapitalindkomst for gifte | PSL § 10, stk. 3, og § 7, stk. 5 |
| H3 | Partner i separat vindue | Fanerne Dig/Partner/Samlet | Princip X |

**Forenklinger, der står tilbage:**
- Partnerens indkomst før vedkommendes første udbetaling (fx løn) kendes ikke. Den regnes som 0,
  og personfradrag overføres kun fra år, hvor partneren har en række.
- Udjævning og buffer er hver for sig (valgt). Den fælles tidslinje er kun til visning.
- Optimeringen tager én person ad gangen (valgt), mens den anden er fast.

## 7g. Opsparing uden for pension (feature 013)

**Model:** Hver person har en liste af aktiver (`Aktiv`). I 013 er der kun typen `bank`
(skattekassen kapitalindkomst). Frit depot og aktiesparekonto kommer i 013b.

**Koblinger efter loven:**
- Afkastet er positiv kapitalindkomst (PSL § 4). Det beskattes sammen med bufferens afkast med
  bundfradrag og skatteloft (PSL § 7, stk. 1, og § 19, stk. 2).
- Afkastet indgår i pensionstillæggets indtægtsgrundlag (LSP § 29).
- Saldoen pr. 1. januar tæller i husstandens likvide formue (LSP § 72 d, stk. 2), også
  partnerens.

**Modelvalg (antagelser, ikke lov):**
- Renten er 009-bufferens: pensionens afkast før PAL-skat. Der er ingen særskilt sats pr. aktivtype.
- Opsparing i planen indsættes i bufferen primo første udbetalingsår og bruges af udjævningen uden
  lån (010). Den er derfor brugt op ved planens slutning.
- Urørt opsparing vokser brutto. Skatten af afkastet betales af den løbende udbetaling.
- Banken står der den 1. januar og tæller i formuen allerede i første udbetalingsår.
  Engangsbeløb udbetales i løbet af året og tæller først året efter (som i 009).
- `likvid_formue` beholder sin betydning: en fast formue, der kun tæller i ældrechecken. Gamle
  input giver samme resultat. Brugerfladen bruger feltet til partnerens opsparing ved et overslag.

**Forenklinger, der står tilbage:**
- Før første udbetalingsår vokser opsparingen med renten før skat. Skatten betales af lønnen, som
  kernen ikke kender (advarsel `OPSPARING_FOER_UDBETALING`).
- Ingen løbende indskud på opsparingen frem til pension.
- Ingen trækrækkefølge, fordi der kun er én skattekasse. Den kommer i 013b.

## 7h. Usikkerhed og levetid (feature 018 og 019)

- **Scenarier (018):** afkast ±1 procentpoint og inflation ±0,5 procentpoint omkring borgerens valg,
  hver for sig og sammen. Legacy havde afkast ±1 og ±2 og fast inflation. Ingen sats sættes under 0
  (som legacy). Hvert scenarie er en almindelig beregning i kernen. Spændene er antagelser.
- **Levetid (019):** `Antagelser.plan_slut_alder` er planens sidste år. Den er adskilt fra
  `livsvarig_horisont_alder`, som kun beregner livrentens ydelse. Selskabet fastsætter livrenten,
  og den betales livet ud, så den ændres ikke af et levetidsscenarie. Planen til 95 år viser også
  indkomsten i året efter den normale plans slutning (folkepension, ATP og livrente).
- **Ikke modelleret:** afkast, der svinger fra år til år (sekvensrisiko), og sandsynligheder. Se
  roadmappen.

## 7i. Arbejdsår og løn (feature 017)

**Koblinger efter loven:**
- AM-bidrag af lønnen (AMBL § 1). Lønnen efter AM-bidrag er personlig indkomst.
- Pensionsindbetaling til ratepension og livsvarig pension fradrages i den personlige indkomst.
  Den regnes som arbejdsgiverordning (forenkling i registret).
- Beskæftigelsesfradrag (LL § 9 J, stk. 1), jobfradrag (§ 9 K) og seniorfradrag (§ 9 J, stk. 5–6,
  gældende lov: 1,4 % i de to sidste år før folkepensionsalderen) er ligningsmæssige fradrag.
  De nedsætter kun grundlaget for kommune- og kirkeskat. Personfradraget regnes pr. grundlag.
- Egen løn indgår ikke i pensionstillæggets indtægtsgrundlag (L 117, 2023). Over bundfradraget
  (122.004 kr. i 2026) indgår den i den personlige tillægsprocent.

**Modelvalg:**
- Lønnen er i dagens kroner og reguleres med satsreguleringen, ikke med `loenvaekst`.
- Pensionsindbetalingen er også i dagens kroner og reguleres med satsreguleringen (017b), så den
  følger lønnen. `loenvaekst` er realvækst oven i (standard 0). Afkastet er det samme som for
  ordningen. Legacy holdt indbetalingen fast i kroner, så den tabte købekraft hvert år.
- Visningen viser lønnen efter skat og pensionsindbetaling pr. måned i dagens kroner (gennemsnit
  af årene før stopalderen) ved hovedtallet, og hvor mange procent det faste beløb er af den.
- Med løn begynder tabellen i dag. Udjævningen begynder ved stopalderen
  (`Fremskrivning.jaevn_fra_alder`). Årene før udjævnes ikke.
- Opsparing i planen og engangsbeløb før stopalderen samles i bufferen og indsættes ved
  stopalderen. Afkastet beskattes i arbejdsåret sammen med lønnen.
- Pensionsindbetalingerne stopper ved stopalderen.
- Hovedtallet og "Find bedste plan" bruger årene fra stopalderen.
- År uden indkomst efter stop giver advarslen `INDKOMSTHUL`.
- "Hvornår kan jeg stoppe?" afprøver alle stopaldre fra i dag til folkepensionsalderen med den
  nuværende plan.

## 8. Uden for denne feature (kommer i senere features)

PDF-import fra PensionsInfo · AI-forklaring/chat · Optimering af udbetalingsrækkefølge
(sekventering) · Fuld husstandsmodel med to profiler · Forsikringsanalyse · UI.

## Kilder

- **Primærkilde for sociale satser 2026**: [VEJ nr. 10077 af 10/11/2025 — regulering pr. 1.1.2026 af satser på Beskæftigelsesministeriets område](https://www.retsinformation.dk/eli/retsinfo/2025/10077) (tabel 12, 15, 16)

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
