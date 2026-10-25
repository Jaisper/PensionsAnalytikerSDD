# Feature Specification: Husstandsbalance – frie midler i udbetalingsplanen

**Feature Branch**: `013-husstandsbalance`

**Created**: 2026-10-25

**Status**: Draft – clarify gennemført, afventer beslutning om opdeling (se sidst)

**Input**: "Udvid analysen med friværdi i boliger, anden formue, forventet arv osv. Start med en
fælles husstandsbalance, så formuetyperne kan afvejes mod hinanden i optimeringen."

**Grundlag**:
- 009 Kapitalpension: bufferen som kapitalindkomst og likvid formue (`_buffer_ki_og_formue`)
- 010 Udjævning uden lån: det faste beløb låner aldrig af senere udbetalinger
- 007 Optimering og 012 Partner (`beregn_husstand`, fælles formue i ældrechecken)
- Model: `Pensionsprofil.likvid_formue` og `anden_kapitalindkomst` (i dag faste tal uden
  fremskrivning). `likvid_formue` er fælles for husstanden (012 kopierer den til partneren), og
  `anden_kapitalindkomst` indgår i indtægtsgrundlaget, men beskattes ikke (forenkling i 001)
- Legacy har ikke frie midler, bolig eller arv. Der er ingen differentialtest for de nye dele

**Afgrænsning**: 013 lægger fundamentet (husstandsbalancen) og bruger det på **frie midler**.
Bolig og friværdi (014), arv modtaget og givet (015) og usikkerhed/Monte Carlo (016) er
selvstændige features oven på 013. Se også den foreslåede opdeling af 013 sidst i dokumentet.

## Clarifications

### Session 2026-10-25

- **Aktieindkomst i pensionstillægget**: Ja. Indtægtsgrundlaget efter LSP § 29 omfatter
  personlig indkomst, positiv nettokapitalindkomst og aktieindkomst beskattet efter PSL § 8 a,
  stk. 1 og 2, *bortset fra aktieudbytte op til 5.000 kr.* (LBK nr. 1123 af 21/10/2024). Avance
  ved salg tæller altså fuldt, udbytte først over 5.000 kr.
  - Åbent: om 5.000 kr. gælder pr. person (Seniorhåndbogen skriver 10.000 kr. for et par).
    Posten lægges i registret som `uverificeret`, til lovteksten er læst direkte.
  - Afkast på aktiesparekonto beskattes efter aktiesparekontoloven og ikke efter PSL § 8 a. Det
    indgår derfor ikke i § 29.
- **Likvid formue (ældrecheck)**: Ja. Værdien af en aktiesparekonto og af et frit depot (aktier,
  investeringsbeviser, obligationer) tæller med i den likvide formue efter LSP § 72 d, stk. 2.
  Friværdi og pensionsopsparing tæller ikke. Grænsen (108.000 kr. i 2026) gælder parret samlet.
  - **Helbredstillæg** (LSP § 14 a) har sin egen formuegrænse, men kernen modellerer slet ikke
    helbredstillæg i dag. Det bliver en selvstændig, senere feature og er ikke med i 013.
- **Realisationsbeskattede aktier**: Forenkling. Brugeren angiver depotets værdi og kan angive
  *"Heraf urealiseret gevinst"*.
  - Uden svar bruges 50 %, vist som en antagelse, brugeren kan ændre (Princip III og V).
  - Et salg realiserer en forholdsmæssig andel af gevinsten (gennemsnitsmetoden).
  - Lagerbeskattede fonde og aktiesparekontoen behøver ingen anskaffelsessum.
- **Ejerskab**: Hvert aktiv ejes af én person. Skatten er individuel, og ASK-loftet gælder pr.
  ejer. En fælles bankkonto angives som to aktiver (fx halvdelen hver). Fælleseje i procent
  udskydes, til der er et konkret behov (bolig i 014).
- **Trækrækkefølge**: 013 bruger kun en fast rækkefølge, som brugeren kan ændre. At lade "Find
  bedste plan" vælge rækkefølge og tidspunkt (US3) bliver en selvstændig feature med eget
  ydelsesbudget. Optimeringen tager allerede ca. 13 s for fem ordninger (fund G1), og US3
  forudsætter løn og arbejdsår før pension, som kernen ikke kender (se "Huller").

## Lovgrundlag (Princip III)

| Kobling | Kilde | Status |
|---|---|---|
| Renter beskattes som kapitalindkomst | PSL § 4 | verificeret |
| Investeringsbeviser i obligationsbaserede investeringsselskaber lagerbeskattes som kapitalindkomst. Aktiebaserede beskattes som aktieindkomst | ABL §§ 19 B og 19 C (fra 2020, lov nr. 84 af 30/01/2019). Den juridiske vejledning C.B.4.3.1 | verificeret |
| Udbytte og avance på aktier beskattes som aktieindkomst: 27 % op til progressionsgrænsen og 42 % over. Grænsen er 79.400 kr. i 2026 | PSL § 4 a og § 8 a, stk. 1–2. Skatteministeriets satsoversigt 2026 | verificeret |
| Gifte, der er samlevende ved årets udgang: den ene ægtefælles uudnyttede progressionsgrænse forhøjer den andens. Forhøjelsen er højst ét grundbeløb. Negativ aktieindkomst modregnes særskilt efter stk. 6 | PSL § 8 a, stk. 4 (og stk. 6). Den juridiske vejledning C.A.8.2 | verificeret |
| Aktiesparekonto: lagerbeskatning med 17 % af afkastet, som banken afregner. Indskudsloftet er 174.200 kr. i 2026, pr. person | Aktiesparekontoloven. skat.dk | verificeret |
| Aktieindkomst indgår i pensionstillæggets indtægtsgrundlag, undtagen aktieudbytte op til 5.000 kr. | LSP § 29 (LBK nr. 1123 af 21/10/2024) | verificeret. Om grænsen er pr. person, er uverificeret |
| Positiv nettokapitalindkomst indgår i pensionstillæggets indtægtsgrundlag | LSP § 29 (i kernen) | verificeret |
| Ældrecheckens formuegrænse gælder husstandens samlede likvide formue, inkl. aktiesparekonto og frit depot | LSP § 72 d, stk. 2 (i registret). Omfanget er tjekket mod borger.dk og Ældre Sagen | verificeret. Lovteksten citeres i registret |
| Bundfradrag og skatteloft for positiv nettokapitalindkomst | PSL § 7, stk. 1; § 19, stk. 2 (i registret) | verificeret |

Satserne SKAL ind i regelregistret som nye poster for 2026 og verificeres mod kildehierarkiet før
merge (Princip II):
- aktieindkomst: 27 %, 42 % og progressionsgrænsen 79.400 kr.
- ASK: sats 17 % og indskudsloft 174.200 kr.
- udbyttegrænsen i § 29: 5.000 kr.

**Antagelser (ikke lov)**: Forventet afkast pr. aktivtype (kontant, obligationer, aktier), inflation
og den urealiserede gevinstandel (standard 50 %). Afkast og inflation har standard fra Rådet for
Afkastforventninger med kildeangivelse. Brugeren kan ændre alle antagelser, og de vises som
antagelser (Princip III og V).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Angiv din opsparing uden for pension (Priority: P1)

Guiden får trinnet **"Din opsparing uden for pension"** efter "Dine ordninger". Borgeren kan
angive:
- bankindestående
- frit depot, opdelt i aktier (aktieindkomst, med valgfri "heraf urealiseret gevinst") og
  lagerbeskattede fonde (kapitalindkomst)
- aktiesparekonto

Hurtig vej: "Ét samlet beløb" (svarer til dagens likvide formue og beskattes som kapitalindkomst).
Trinnet forklarer, hvorfor der spørges: opsparingen påvirker skat, pensionstillæg og ældrecheck.

**Acceptance Scenarios**:

1. **Given** en profil uden opsparing, **Then** er resultatet det samme som før 013.
2. **Given** et gammelt input med `likvid_formue`, **When** det indlæses, **Then** bliver det til
   ét bankindestående ejet af person A med samme beløb, og resultatet er uændret.
3. **Given** gift med fuld partnerprofil, **Then** angiver hver person sin egen opsparing.

---

### User Story 2 - Opsparingen indgår i det faste beløb (Priority: P1)

Den frie opsparing fremskrives år for år med afkast og skat og kan bruges i udjævningen ligesom
bufferen (009). Hovedtallet bliver det faste beløb efter skat, inkl. træk fra opsparingen.

Standard-trækrækkefølge: bank → frit depot → aktiesparekonto. Borgeren kan ændre den.

**Acceptance Scenarios**:

1. **Given** 500.000 kr. i bank, **Then** stiger det faste beløb, og opsparingen er 0 eller
   positiv i alle år (ingen lån, jf. 010).
2. **Given** at opsparingen krydser ældrecheckens formuegrænse, **Then** falder eller kommer
   ældrechecken i præcis de år, og forklaringen siger hvorfor.
3. **Given** salg fra frit depot med gevinst, **Then** beskattes gevinsten som aktieindkomst i
   salgsåret og ikke som personlig indkomst, og den tæller i pensionstillæggets
   indtægtsgrundlag (§ 29).

---

### User Story 3 - Find bedste plan vælger også, hvornår opsparingen bruges (Priority: P2 → egen feature)

*Flyttes ud af 013 (se Clarifications og "Foreslået opdeling").*

"Find bedste plan" (007) kan også vælge trækrækkefølge og tidspunkt, fx at bruge frie midler
før folkepensionsalderen og udskyde ratepension. Forslaget vises med "Anvend" som i dag.

**Acceptance Scenarios**:

1. **Given** en profil, hvor tidligt forbrug af frie midler øger pensionstillægget senere,
   **When** "Find bedste plan" køres, **Then** foreslås den rækkefølge, og gevinsten vises i
   kr. pr. måned.
2. **Then** oplyses søgningens omfang (evaluerede ud af mulige kombinationer, Princip V).

---

### User Story 4 - Se din formue over tid (Priority: P3)

En fold-ud under grafen viser formuen år for år pr. aktivtype og **restformuen ved 90 år**
(eller sidste år i beregningen). Restformuen er grundlaget for arv (015).

**Acceptance Scenarios**:

1. **Given** opsparing, **Then** er restformuen lig startformue + afkast − skat − træk.
2. **Given** fanen "Samlet" (012), **Then** vises husstandens samlede formue.

### Edge Cases

- **Indskud på aktiesparekonto over loftet**: Advarsel. Overskydende beløb behandles som frit
  depot (forenkling, vist for brugeren).
- **Negativ værdi eller 0 i alle felter**: Trinnet kan springes over.
- **Opsparingen er brugt op før planens slutning**: Det faste beløb falder i trin (som 010), og
  grafen viser det.
- **Aktieindkomst over progressionsgrænsen i ét år** (stort salg): Advarsel om høj marginalskat
  og forslag om at sprede salget over flere år. For gifte tages højde for den overførte grænse
  (PSL § 8 a, stk. 4).
- **Negativ aktieindkomst** (tab ved salg): Ikke med i 013. Tabet kan ikke fremføres eller
  modregnes, og det vises som en forenkling.
- **Fastpunktet konvergerer ikke** (formue ↔ ældrecheck ↔ kapitalindkomst): Advarsel som ved
  bufferen.

## Requirements *(mandatory)*

- **FR-001**: Kernen MUST have en husstandsbalance: en liste af aktiver med type, skattekasse,
  ejer (én person), saldo pr. 1. januar, afkastantagelse og om aktivet er likvid formue.
  Aktier i frit depot har også en urealiseret gevinstandel. Passiver er med i modellen, men
  bruges først i 014.
- **FR-002**: Skattekasserne i 013 er: `kapitalindkomst`, `aktieindkomst_realisation` og
  `aktiesparekonto`. 009-bufferen MUST modelleres som et aktiv i kassen `kapitalindkomst`, uden
  at 009's golden cases ændres.
- **FR-003**: Fremskrivningen MUST beregne afkast, skat pr. kasse og træk pr. år og føre
  kapitalindkomst, aktieindkomst og likvid formue til skat og ydelser gennem de eksisterende
  regler.
  - Årets overskud indsættes i banken (kassen `kapitalindkomst`).
  - Et underskud trækkes efter rækkefølgen.
  - Det hele sker inden for 009's fastpunkt-iteration.
- **FR-004**: Trækrækkefølgen MUST være en udskiftelig strategi med en defineret grænseflade.
  Fast rækkefølge er den eneste strategi i 013. Grænsefladen skal kunne bruges af en senere
  optimering (US3).
- **FR-005**: Husstandens likvide formue til ældrechecken MUST være summen af begge personers
  likvide aktiver pr. 1. januar (erstatter `likvid_formue` + buffer i 012, FR-004).
- **FR-006**: Gamle input MUST stadig kunne indlæses og give samme resultat.
  - `likvid_formue` bliver ét bankaktiv ejet af person A.
  - `anden_kapitalindkomst` bevarer sin nuværende forenkling: den indgår i indtægtsgrundlaget og
    beskattes ikke.
- **FR-007**: Nye satser MUST ligge i regelregistret med kilde og status (Princip II).
  Afkastantagelser og gevinstandelen MUST vises som antagelser, som brugeren kan ændre
  (Princip III).
- **FR-008**: Persondata forlader ikke browseren (Princip VII og XI).
- **FR-009**: Princip X: guidetrinnet har ét spørgsmål pr. aktivtype, forklaring i konteksten,
  axe 0 fejl og ingen vandret scroll ved 360 px.

### Key Entities

- **Husstandsbalance**: aktiver og passiver for én eller to personer.
- **Aktiv**: type, skattekasse, ejer, saldo, afkastantagelse, likvid ja/nej, urealiseret
  gevinstandel (kun aktier i frit depot).
- **Skattekasse**: reglen for, hvordan afkast og træk beskattes, og hvordan de tæller i ydelser.
- **Trækstrategi**: rækkefølge (og senere tidspunkt) for træk fra aktiverne.

## Success Criteria *(mandatory)*

- **SC-001**: Alle eksisterende tests, inkl. differentialtest mod legacy, er grønne uden
  ændrede facit-tal (ingen opsparing = samme resultat).
- **SC-002**: Golden cases med kildehenvisning for hver skattekasse:
  - kapitalindkomst
  - aktieindkomst over og under progressionsgrænsen, også med overført grænse for gifte
  - aktiesparekonto
- **SC-003**: Golden case for ældrecheck, hvor formuen krydser grænsen i et bestemt år.
- **SC-004**: Regelgrænser for de nye satser (på, under og over).
- **SC-005**: Samme resultat i Pyodide og CPython.
- **SC-006**: En ændring giver nye tal på under 2 s i browseren for to profiler med opsparing.

## Huller i udkastet (fundet under clarify)

1. **Ingen løn eller arbejdsår før første udbetaling.** Kernen kender ikke borgerens eller
   partnerens indkomst før pension. Det er en forudsætning for US3 ("brug frie midler før
   folkepensionsalderen"): uden løn kan det ikke vurderes, hvornår et træk er billigt.
2. **Ingen løbende opsparing frem til pension.** Aktiverne kan kun have en saldo i dag. En årlig
   indbetaling (fx til ASK) er ikke med i 013.
3. **`anden_kapitalindkomst`** beskattes ikke i dag. Den forenkling SKAL bevares for gamle input
   (FR-006), ellers ændres facit-tal (SC-001).
4. **`likvid_formue` er fælles for husstanden** i 012, men aktiver har én ejer i 013. Migrationen
   lægger den hos person A (US1, scenarie 2).
5. **Hvor havner overskud, og hvordan trækkes der?** Dette var ikke defineret. Det er nu
   fastlagt i FR-003: overskud i banken, træk efter rækkefølgen, inden for 009's fastpunkt.

## Foreslået opdeling

013 som beskrevet er for stort til én leverance med samme kvalitet som 009–012. Forslag:

| Feature | Indhold | Prioritet |
|---|---|---|
| **013 Husstandsbalance** | Balancen og aktivmodellen. Bank/kapitalindkomst, hvor bufferen indgår som et aktiv. Migration af `likvid_formue`. Fast trækrækkefølge. US4 (formue over tid). Guidetrinnet med "Ét samlet beløb" og bank | P1 |
| **013b Frit depot og aktiesparekonto** | Aktieindkomst med realisation og gevinstandel, progressionsgrænse med overførsel for gifte, ASK med lagerskat og loft, § 29-udbyttegrænse. Nye registerposter | P1, efter 013 |
| **Ny: Arbejdsår og løn før pension** | Pensioneringsalder, løn og løbende indbetalinger for begge personer | forudsætning for US3 |
| **US3 Optimér trækrækkefølge** | "Find bedste plan" vælger rækkefølge og tidspunkt, med eget ydelsesbudget | P2 |
| **014, 015, 016** | Bolig og friværdi, arv, usikkerhed (uændret) | senere |
| **Helbredstillæg** | LSP § 14 a med egen formuegrænse | senere |

**Beslutning ønskes** (fra projektejeren og fætteren), før der planlægges:
- Opdelingen ovenfor.
- Standard for den urealiserede gevinstandel (50 %).
- Om 5.000 kr.-grænsen i § 29 skal afklares hos Udbetaling Danmark, før 013b merges.

## Uden for scope (næste features)

- **014 Bolig og friværdi**: bliv boende, nedskalering i et valgt år, seniorlån/belåning
  (negativ kapitalindkomst), ejendomsværdiskat og grundskyld. Friværdi tæller ikke som likvid
  formue.
- **015 Arv**: forventet arv modtaget (tidspunkt og interval, vist med og uden), boafgift og
  tillægsboafgift, pensioner til begunstigede og "bevar X til arvinger" som begrænsning i
  optimeringen.
- **016 Usikkerhed**: scenarier og Monte Carlo for afkastsekvens og levetid.
- **Import af årsopgørelse**: lokal, regelbaseret aflæsning af frie midler (Princip XI).

## Kilder (clarify 2026-10-25)

- Lov om social pension § 29: LBK nr. 1123 af 21/10/2024 (lovguiden.dk/danskelove.dk);
  borger.dk, "Grundbeløb og pensionstillæg"
- Likvid formue: borger.dk og Ældre Sagen om ældrecheck
- PSL § 8 a: Skatteministeriets satsoversigt 2026; Den juridiske vejledning C.A.8.2 (tax.dk)
- ABL §§ 19 B–C: Den juridiske vejledning C.B.4.3.1; LBK nr. 1098 af 27/08/2025
- Aktiesparekonto: skat.dk, "Aktiesparekonto" (17 %, 174.200 kr. i 2026)
