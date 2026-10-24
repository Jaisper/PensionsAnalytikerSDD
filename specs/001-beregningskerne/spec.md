# Feature Specification: Beregningskerne og regelregister

**Feature Branch**: `001-beregningskerne`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "Deterministisk beregningskerne og regelregister: fremskriv
pensionsudbetalinger år for år efter dansk skatte- og pensionslovgivning 2026. Valider den mod
lovgivningen."

**Domænegrundlag**: [docs/domaene/beregningskerne.md](../../docs/domaene/beregningskerne.md).
Det indeholder regler, 2026-satser, kilder, legacy-afvigelser (A1–A8) og golden cases.
Henvisninger som "(jf. A1)" og "G-02" peger dertil.

## Overblik

Kernen tager en **pensionsprofil** (person, ordninger og saldi), **antagelser** (afkast,
inflation m.m.) og et **satsår**. Den returnerer en **fremskrivning**: brutto, skat og netto år
for år for hver indkomstkilde. Til hvert tal hører sporing af de regler og antagelser, der
blev brugt, samt advarsler.

Kernen har ingen brugerflade. Dens "brugere" er:
- **Borgeren**, indirekte gennem senere features (import, forklaring, UI)
- **Udvikleren og revisoren**, der skal kunne efterprøve hvert tal mod lovgivningen

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Nettoudbetaling år for år for en enlig (Priority: P1)

En enlig borger, der nærmer sig pension, har ratepension, livrente, aldersopsparing og ATP. Hun
vil vide, hvad hun får udbetalt efter skat hvert år fra pensionsstart og til udbetalingerne
slutter, inklusive folkepensionens grundbeløb fra folkepensionsalderen.

**Why this priority**: Det er kernens grundydelse. Alle andre features bygger på et korrekt
år-for-år-netto.

**Independent Test**: Kør en profil med kendte saldi og antagelser. Sammenlign hvert års
brutto, skat og netto med et håndberegnet facit. Facit følger lovens skattetrin, personfradrag
og skatteloft, og der trækkes **ikke** AM-bidrag af pensionsudbetalinger.

**Acceptance Scenarios**:

1. **Given** en ratepension på 1.000.000 kr. med start ved 65 år, udbetalt over 10 år, afkast
   0 % og ingen anden indkomst, **When** fremskrivningen beregnes, **Then** udgør
   bruttoudbetalingen 100.000 kr. i hvert af årene 65–74. Nettoudbetalingen er brutto fratrukket
   bundskat og kommune-/kirkeskat efter personfradrag, uden AM-bidrag.
2. **Given** en personlig indkomst på 900.000 kr. og kommuneskat 25 %, **When** den progressive
   skat beregnes, **Then** er mellemskat + topskat 28.567,50 kr. og skatteloftsnedslaget 0
   (G-03).
3. **Given** samme indkomst og kommuneskat 25,71 %, **When** skatten beregnes, **Then**
   reduceres den progressive skat med skatteloftsnedslaget (G-03b).
4. **Given** en person født 1963, **When** folkepensionsalderen bestemmes, **Then** er den 68
   år. For fødselsårene 1962, 1967 og 1971 er den 67, 69 og 70 år (FP-1).
5. **Given** en aldersopsparing, **When** den udbetales, **Then** er udbetalingen skattefri og
   indgår hverken i personlig indkomst eller i indtægtsgrundlaget for pensionstillæg.
6. **Given** en kapitalpension (afgiftspligtig), **When** den udbetales, **Then** fratrækkes
   40 % afgift, og beløbet indgår ikke i personlig indkomst.
7. **Given** at ATP-beløbet ikke er oplyst, **When** fremskrivningen beregnes, **Then** bruges
   registrets fallback-sats, og resultatet markerer, at ATP er skønnet.

---

### User Story 2 - Folkepensionens indtægtsregulering (Priority: P1)

Borgeren vil se, hvordan hendes private pensioner påvirker pensionstillæg, den personlige
tillægsprocent, ældrecheck og mediecheck år for år.

**Why this priority**: Modregning i pensionstillægget er ofte den største enkeltfaktor i
beslutninger om udbetalingsform og timing. Den er derfor lige så vigtig som skatten.

**Independent Test**: Kør tærskelværdierne fra registret (på, under og over hver grænse) og
golden cases G-40 til G-43 og PT-1.

**Acceptance Scenarios**:

1. **Given** en enlig med et indtægtsgrundlag på 99.200 kr., **When** ydelserne beregnes,
   **Then** er pensionstillægget fuldt (104.748 kr./år) og den personlige tillægsprocent 0
   (G-42).
2. **Given** en enlig med et indtægtsgrundlag på 36.335 kr., **When** tillægsprocenten
   beregnes, **Then** er den 99 (G-40).
3. **Given** en tillægsprocent på 100 og en likvid formue på 108.000 kr. henholdsvis 108.001
   kr., **When** ældrechecken beregnes, **Then** er den 26.900 kr. henholdsvis 0 kr.
   Mediechecken er uændret i begge tilfælde (G-43).
4. **Given** ældrecheck og mediecheck, **When** netto beregnes, **Then** beskattes begge som
   personlig indkomst (jf. A3).
5. **Given** en beregnet ældrecheck under 200 kr., **When** ydelserne beregnes, **Then**
   udbetales 0 kr. (jf. A6).
6. **Given** et indtægtsgrundlag, **When** det opgøres, **Then** indgår ATP, skattepligtige
   private pensionsudbetalinger, nettokapitalindkomst og aktieindkomst ud over 5.000 kr.
   udbytte. Aldersopsparing og egen arbejdsindkomst indgår ikke (jf. A5).

---

### User Story 3 - Regelregister med satsår, kilder og status (Priority: P1)

Udvikleren vil vedligeholde alle satser ét sted og kunne se kilde og verifikationsstatus for
hver sats. Revisoren vil kunne afvise en beregning, der bygger på uverificerede satser.

**Why this priority**: Forfatningens Princip II og III kræver det. Uden registret kan ingen af
de andre stories valideres mod loven.

**Independent Test**: Slå hver post op i registret og kontrollér id, værdi, satsår, kilde og
status. Kør en beregning i streng tilstand, og kontrollér, at den afvises med besked om den
præcise post, når en ikke-verificeret sats indgår.

**Acceptance Scenarios**:

1. **Given** registret for 2026, **When** man slår en vilkårlig sats op, **Then** har den værdi,
   satsår, kildehenvisning og status (`verificeret` / `sekundær kilde` / `uverificeret`).
2. **Given** en beregning i streng tilstand, **When** en sats uden status `verificeret` ville
   blive brugt, **Then** afvises beregningen med satsens id og kilde.
3. **Given** et satsår, der ikke findes i registret, **When** der beregnes, **Then** afvises
   beregningen med en tydelig fejl. Der bruges ikke stiltiende et andet år.

---

### User Story 4 - Sporbarhed og advarsler (Priority: P2)

Borgeren (via forklaring) og revisoren vil kunne se, hvilke regler, satser og antagelser der
ligger bag et givet års tal, og få advarsler om forhold, der er vigtige for beslutningen.

**Why this priority**: Forfatningens Princip V. Det er nødvendigt, før tal kan præsenteres for
borgere, men kernens tal kan valideres uden.

**Independent Test**: Kør en profil, der udløser hver advarselstype, og kontrollér, at
advarslen findes, og at hvert års sporing nævner de forventede registerposter.

**Acceptance Scenarios**:

1. **Given** et vilkårligt år i fremskrivningen, **When** sporingen hentes, **Then** angives
   alle registerposter og antagelser, der påvirkede årets tal.
2. **Given** indbetalinger til ratepension over loftet (68.700 kr.), **When** der beregnes,
   **Then** advares der, og det overskydende beløb behandles som indbetaling til livsvarig
   pension.
3. **Given** år, hvor personlig indkomst overstiger mellemskattegrænsen, **When** der
   beregnes, **Then** gives én advarsel pr. sammenhængende aldersinterval, ikke én pr. år.
4. **Given** en ordnings ønskede udbetalingsstart før dens tidligste lovlige udbetalingsalder,
   **When** der beregnes, **Then** afvises eller markeres starten (jf. A2).
5. **Given** en forenkling eller en ikke-verificeret sats i et års beregning, **When**
   resultatet hentes, **Then** er det markeret i netop det år.

---

### User Story 5 - Opsat folkepension (Priority: P2)

Borgeren vil se effekten af at udskyde folkepensionen 1–10 år mod et ventetillæg.

**Why this priority**: Det er en vigtig beslutningsparameter, men kræver US1 og US2 først.

**Independent Test**: Opsættelse fra 67 år i 1–10 år giver grundbeløb og pensionstillæg ganget
med tabellens venteprocent. ATP påvirkes ikke.

**Acceptance Scenarios**:

1. **Given** opsættelse fra 67 år i 3 år, **When** der beregnes, **Then** udbetales grundbeløb
   og pensionstillæg fra 70 år ganget med 1,1875 (VT-1). ATP udbetales fortsat fra 67 år.
2. **Given** opsættelse fra en anden alder end 67, **When** der beregnes, **Then** bruges lovens
   formel (opsatte måneder / restlevetid i måneder). Hvis restlevetiden ikke findes i en
   verificeret kilde, markeres resultatet.
3. **Given** opsættelse, **When** der beregnes, **Then** gøres brugeren opmærksom på kravet om
   750 arbejdstimer pr. år. Kravet håndhæves ikke, fordi kernen ikke kender arbejdstimer.
4. **Given** opsættelse på mere end 10 år, **When** der beregnes, **Then** afvises inputtet.

---

### User Story 6 - Gift/samlevende (Priority: P2)

En gift borger vil have pensionstillæg og tillægsprocent beregnet efter reglerne for
gifte/samlevende, også i overgangsåret, hvor partneren selv bliver folkepensionist.

**Why this priority**: Omkring halvdelen af målgruppen er gift eller samlevende, og reglerne
giver markant andre tal. Kernen tager partnerens forhold som input; en fuld husstandsmodel med
to profiler er en senere feature.

**Independent Test**: Med partnerens fødselsår og partnerens indkomst pr. år som input skifter
aftrapningsreglen (32 % → 16 %) i det år, partneren når folkepensionsalderen (PT-1).

**Acceptance Scenarios**:

1. **Given** en gift person, hvis partner endnu ikke er folkepensionist, **When**
   pensionstillægget beregnes, **Then** bruges fradragsbeløb 198.800 kr. og aftrapning 32 %.
   Når begge er pensionister, er aftrapningen 16 %.
2. **Given** en partner, der ikke er pensionist og har private pensionsudbetalinger, **When**
   indtægtsgrundlaget opgøres, **Then** indgår partnerens indkomst efter lovens regel for
   ikke-pensionist-ægtefæller (jf. A4). AM-bidragspligtig arbejdsindkomst indgår ikke.
3. **Given** en gift person, **When** tillægsprocenten beregnes, **Then** bruges grænserne for
   gifte (70.600 / 198.800 kr., trin på 1.282 kr.) (G-41).

---

### User Story 7 - Jævn månedlig udbetaling (Priority: P3)

Borgeren vil se ét forudsigeligt månedligt beløb (konstant i dagens købekraft) i stedet for en
udbetaling, der svinger, når ordninger starter og stopper. Engangsbeløb bruges som buffer.

**Why this priority**: Det har værdi som præsentation, men er en model og ikke lovgivning
(jf. domænegrundlagets afsnit 3.6). Den bygger oven på US1–US6.

**Independent Test**: Nutidsværdien af den jævne udbetaling svarer til nutidsværdien af den
almindelige udbetaling plus bufferen, diskonteret med bufferens rente efter skat. Niveauet
falder aldrig, når et nyt engangsbeløb lander.

**Acceptance Scenarios**:

1. **Given** en profil med et engangsbeløb før pensionsstart, **When** jævn udbetaling
   beregnes, **Then** er niveauet i nutidskroner konstant over hele pensionsperioden.
2. **Given** et engangsbeløb, der først kommer efter pensionsstart, **When** jævn udbetaling
   beregnes, **Then** stiger niveauet fra det år, beløbet kommer. Der lånes ikke mod beløbet,
   før det er modtaget.
3. **Given** et engangsbeløb, som brugeren har fravalgt som buffer, **When** der beregnes,
   **Then** udbetales det i sit år og indgår ikke i udjævningen.

---

### Edge Cases

- **Allerede startede udbetalinger**: Profil, hvor personen allerede er over pensionsalderen
  eller har påbegyndt udbetalinger.
- **Manglende data**: Ordning uden oplyst saldo, men med oplyst forventet udbetaling.
  Afkast 0 %.
- **Ugyldigt input**: Pensionsalder før tidligste udbetalingsalder, negative beløb eller
  fødselsår før 1955 (uden for scope, se Assumptions). Skal give en tydelig fejl, ikke et
  stille resultat.
- **Indkomst præcis på en tærskel**: Mellemskattegrænse, fradragsbeløb, formuegrænse og
  tillægsprocentens trin.
- **Indkomst over top-topskattegrænsen**: Skatteloftet på 57,07 % skal gælde.
- **Mange år frem**: Skattegrænser og ydelser skal satsreguleres i fremtidige år, så nominel
  vækst alene ikke flytter folk op i højere skattetrin.
- **Kun folkepension og ATP**: Ingen private ordninger.
- **Partneren bliver folkepensionist** midt i borgerens udbetalingsperiode.

## Requirements *(mandatory)*

### Functional Requirements

**Input og determinisme**

- **FR-001**: Kernen MUST tage en pensionsprofil, et sæt antagelser, et satsår og en
  beregningsdato som eksplicit input. Den MUST NOT læse dags dato, filer, netværk eller anden
  ekstern tilstand.
- **FR-002**: Kernen MUST give identisk output for identisk input.
- **FR-003**: Kernen MUST validere input og afvise ugyldigt input med en entydig fejl, der
  angiver feltet. Det gælder fx manglende alder, negative beløb, opsættelse over 10 år og
  ukendt satsår.

**Regelregister**

- **FR-010**: Alle lovbestemte satser, grænser, procenter og aldersregler MUST komme fra et
  regelregister. Hver post har id, værdi, satsår, kildehenvisning og status (`verificeret`,
  `sekundær kilde`, `uverificeret`).
- **FR-011**: Registret MUST kunne rumme flere satsår. Der MUST NOT faldes tilbage til et
  andet satsår, end der er bedt om.
- **FR-012**: Kernen MUST understøtte en streng tilstand, der afviser beregninger, som bruger
  poster uden status `verificeret`.
- **FR-013**: Registret MUST mindst indeholde 2026-posterne i domænegrundlagets afsnit 2. Hver
  post skal være verificeret mod kildehierarkiet i forfatningen.

**Skat**

- **FR-020**: Personlig indkomst fra pensionsudbetalinger og offentlige ydelser MUST beskattes
  med bundskat, kommuneskat og kirkeskat efter personfradrag, samt mellemskat, topskat og
  top-topskat med skrå skatteloft (PSL §§ 6, 7, 7 a, 8, 10, 19).
- **FR-021**: Der MUST NOT beregnes AM-bidrag af udbetalinger fra pensionsordninger (jf. A1).
- **FR-022**: Kommuneskat og kirkeskat MUST være input pr. person. Registret MUST indeholde
  2026-satserne for alle kommuner.
- **FR-023**: Aldersopsparing MUST udbetales skattefrit. Kapitalpension MUST pålægges 40 %
  afgift. Ingen af dem MUST indgå i personlig indkomst.
- **FR-024**: Skatten MUST beregnes samlet pr. år på personens samlede personlige indkomst.
  Kernen MUST desuden kunne vise netto pr. indkomstkilde ved en dokumenteret fordelingsregel,
  hvor summen af fordelingerne er lig den samlede skat.

**Folkepension, ATP og tillægsstyrede ydelser**

- **FR-030**: Folkepensionsalderen MUST bestemmes af fødselsdatoen efter Lov om social
  pension § 1a (67 / 68 / 69 / 70 år).
- **FR-031**: Grundbeløbet MUST udbetales fra folkepensionsalderen (eller fra opsættelsens
  ophør) uden indtægtsregulering. Det forudsætter, at der ikke er arbejdsindkomst.
- **FR-032**: Pensionstillægget MUST aftrappes efter den af de tre regler, der gælder for det
  enkelte år: enlig 30,9 % / gift med pensionist 16 % / gift med ikke-pensionist 32 %.
  Fradragsbeløb og indtægtsgrundlag MUST følge borger.dk og loven (jf. A4, A5).
- **FR-033**: Den personlige tillægsprocent MUST beregnes som en selvstændig regel med hele
  procentpoint pr. påbegyndt trin. Den MUST NOT afledes af pensionstillæggets aftrapning.
- **FR-034**: Ældrechecken MUST være lig satsen ganget med tillægsprocenten, kun ved en likvid
  formue på højst grænsen. Den er skattepligtig, og beløb under 200 kr. udbetales ikke.
- **FR-035**: Mediechecken MUST kun udbetales ved en tillægsprocent på 100. Den er
  skattepligtig og afhænger ikke af formue.
- **FR-036**: ATP MUST udbetales fra folkepensionsalderen og påvirkes ikke af opsat
  folkepension. Uden oplyst beløb bruges registrets fallback, og det markeres.

**Private ordninger**

- **FR-040**: Saldoen MUST fremskrives til udbetalingsstart med afkast efter PAL-skat og evt.
  løbende indbetalinger (med lønvækst).
- **FR-041**: Ratepension MUST udbetales som annuitet over den oplyste eller valgte periode.
  Livsvarig pension MUST udbetales livsvarigt over en udbetalingshorisont, som er en eksplicit
  antagelse.
- **FR-042**: Indbetalinger til ratepension over loftet MUST behandles som indbetaling til
  livsvarig pension og udløse en advarsel. Indbetalinger til aldersopsparing MUST begrænses af
  det relevante loft (9.900 kr. eller 64.200 kr. inden for 7 år før folkepensionsalderen).
- **FR-043**: Kernen MUST bestemme hver ordnings tidligste lovlige udbetalingsalder ud fra
  fødselsdato og oprettelsesdato, og MUST håndhæve den (jf. A2). Er oprettelsesdatoen ukendt,
  bruges den mest restriktive regel, og det markeres.

**Opsat folkepension**

- **FR-050**: Opsættelse i 0–10 år MUST forhøje grundbeløb og pensionstillæg med
  venteprocenten efter lovens formel. Tabellen for opsættelse fra 67 år (2026) bruges, hvor
  den gælder.
- **FR-051**: Ventetillægget udbetales som livsvarigt tillæg. [NEEDS CLARIFICATION: Skal
  kernen også understøtte de to andre udbetalingsformer for tillæg optjent efter 1/7-2018
  (forhøjet tillæg i 10 år / engangsbeløb + 10 år)?]

**Fremtidige år og antagelser**

- **FR-060**: Lovbestemte beløb (skattegrænser, personfradrag, folkepension, ATP og ydelser)
  MUST satsreguleres i fremtidige år. [NEEDS CLARIFICATION: Skal satsreguleringen være en
  selvstændig antagelse (fx 2,6 %/år som for 2027) eller fortsat kobles til
  inflationsantagelsen, som i legacy?]
- **FR-061**: Kernen MUST beregne realværdi (dagens købekraft) ud fra inflationsantagelsen.
- **FR-062**: Alle antagelser (afkast, inflation, lønvækst, satsregulering,
  udbetalingshorisont for livsvarig, skat på fri formue) MUST fremgå af resultatet som
  antagelser og holdes adskilt fra lovregler.

**Output, sporing og advarsler**

- **FR-070**: Output MUST indeholde én række pr. alder med brutto, skat og netto pr.
  indkomstkilde (private ordninger, grundbeløb, pensionstillæg, ATP, ældrecheck, mediecheck,
  engangsbeløb) og i alt, samt indtægtsgrundlag og tillægsprocent.
- **FR-071**: Hver række MUST have sporing af de registerposter og antagelser, der påvirkede
  den, samt markering af forenklinger og ikke-verificerede satser.
- **FR-072**: Resultatet MUST indeholde advarsler: ratepensionsloft, mellemskat pr.
  aldersinterval, udbetalingsstart før lovlig alder, skønnet ATP, usikker venteprocent og
  750-timers-kravet.

**Jævn udbetaling**

- **FR-080**: Kernen MUST kunne beregne en jævn månedlig udbetaling (US7), hvor engangsbeløb,
  der ikke er fravalgt, bruges som buffer. Bufferen forrentes med afkastet efter en antaget
  skat på fri formue.
- **FR-081**: Afkast af bufferen er kapital- eller aktieindkomst. [NEEDS CLARIFICATION: Skal
  bufferens afkast indgå i indtægtsgrundlaget for pensionstillæg og tillægsprocent (jf. A5)?
  Det er lovmæssigt korrekt, men gør den jævne udbetaling afhængig af ydelsesberegningen og
  omvendt.]

### Key Entities

- **Pensionsprofil**: Person (fødselsdato, civilstand, kommune, kirkemedlem, likvid formue),
  liste af ordninger og evt. partneroplysninger (fødselsdato og skattepligtig indkomst pr. år).
- **Ordning**: Type (ratepension, livsvarig/livrente, aldersopsparing, kapitalpension, ATP),
  skattetype, oprettelsesdato, saldo, løbende indbetaling, ønsket udbetalingsstart og
  -periode, samt om den indgår i bufferen.
- **Antagelser**: Afkast efter PAL, inflation, lønvækst, satsregulering,
  udbetalingshorisont for livsvarig, skat på fri formue og opsættelse af folkepension.
- **Regelregister / registerpost**: id, værdi, satsår, kilde og status.
- **Fremskrivning**: Rækker pr. alder, jævn udbetaling, advarsler, brugte antagelser og samlet
  sporing.
- **Sporing**: Pr. række listen over registerposter og antagelser samt flag for forenkling og
  uverificeret.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % af golden cases i domænegrundlaget (G-02 … VT-1) og alle acceptance
  scenarios ovenfor består.
- **SC-002**: Hver post i 2026-registret har en kildehenvisning. Mindst 90 % har status
  `verificeret` (niveau 1–3), og resten er eksplicit markeret.
- **SC-003**: For et sæt på mindst 10 repræsentative testprofiler afviger nettoudbetalingen
  pr. år fra legacy med 0 kr. eller med en forskel, der fuldt ud forklares af A1–A6 eller af
  en dokumenteret ændret antagelse.
- **SC-004**: Hvert tal i output kan spores til mindst én registerpost eller antagelse. Der er
  ingen "anonyme" tal.
- **SC-005**: En fuld fremskrivning (40 år, 10 ordninger) beregnes på under 100 ms, så
  optimering kan køre tusindvis af beregninger senere.
- **SC-006**: Satsopdateringen til et nyt satsår kræver kun ændringer i registret og i golden
  cases, ikke i beregningslogikken (bortset fra reelle lovændringer).

## Assumptions

- Målgruppen er personer født 1955 eller senere (folkepensionsalder 67 år eller højere).
  Tidligere fødselsår afvises.
- Der er ingen arbejdsindkomst i fremskrivningsårene. Grundbeløbets modregning i
  arbejdsindkomst og 750-timers-kravet håndhæves derfor ikke.
- Afkastantagelsen er efter PAL-skat. PAL beregnes ikke særskilt.
- Udbetalingsbeløb fra pensionsselskabet (fx livrente påbegyndt før folkepensionsalderen)
  antages at afspejle selskabets egne reduktioner.
- Restlevetid til ventetillæg ved andre opsættelsesaldre end 67 og udbetalingshorisonten for
  livsvarig pension skal fastlægges i plan-fasens research. Indtil da markeres de som
  forenklinger.
- **Lovspørgsmål, der skal afklares i plan-fasens research** (Princip III). Det er faktuelle
  spørgsmål, ikke designvalg:
  - Reglen for at se bort fra en ikke-pensionist-partners indkomst (A4)
  - Udbetalingsalder for ordninger oprettet fra 2018 (A2)
  - Ratepensionens tilladte periode
  - Kapitalpensionsafgiftens paragraf (A8)
  - Grænsen for aktieindkomst i 2026
- Uden for scope:
  - PDF-import
  - AI-forklaring
  - Brugerflade
  - Optimering af udbetalingsrækkefølge
  - Fuld husstandsmodel med to beregnede profiler
  - Forsikringsanalyse
  - Scenarieanalyse (kan bygges som gentagne kald til kernen)
  - Engangschecken 2026
