# Implementation Plan: Partner – to profiler og en samlet oversigt

**Branch**: `012-partner` | **Spec**: [spec.md](spec.md)

## D1 Kernen

**Model**:
- `Civilstand` = enlig | gift | samlevende | gift_samlevende. Det sidste er alias for samlevende.
- `Partner` får nye felter, nøglet på kalenderår:
  - `formue_pr_aar` (partnerens buffer pr. 1. januar)
  - `kapitalindkomst_pr_aar`
  - `uudnyttet_personfradrag_pr_aar` (skatteværdi, kr.)
  - `pensionist_fra_aar` (kalenderår, None = som i dag ud fra folkepensionsalderen)
- `Aarsresultat.uudnyttet_personfradrag` (skatteværdi i kr.)

**Skat** (`beregn_skat`):
- `overfoert_personfradrag`: Nedsætter flad skat med højst den flade skat (PSL § 10, stk. 3 / § 9).
- `ekstra_ki_bundfradrag`: Lægges til kapitalindkomstens bundfradrag (§ 7, stk. 5).
- Begge er 0 for andre end gifte.
- Egen uudnyttet skatteværdi = max(0, personfradrag − (PI + KI)) × flad sats.

**År for år**:
- Partnerens pensionist-status kommer fra `pensionist_fra_aar`, hvis den er sat.
- Ældrecheckens formue = profilens formue + egen buffer + partnerens formue[kalenderår].
- For gifte:
  - ekstra bundfradrag = max(0, bundfradrag − partnerens KI[kalenderår])
  - overført personfradrag = partnerens uudnyttede[kalenderår]

**`husstand.py`**:

```python
@dataclass(frozen=True)
class Husstand:
    a: Fremskrivning
    b: Fremskrivning
    iterationer: int
    konvergeret: bool

def beregn_husstand(profil_a, antagelser_a, profil_b, antagelser_b, satsaar, dato) -> Husstand
def partner_fra(res: Fremskrivning, profil: Pensionsprofil, antagelser) -> Partner
```

`partner_fra` udleder pr. kalenderår:
- `oevrig_indkomst` = privat pension (ratepension og livsvarig, brutto) + ATP + bufferens KI
- formue, KI og uudnyttet personfradrag
- `pensionist_fra_aar` = fødselsår + folkepensionsalder + opsættelse

**Fastpunkt**:
1. B regnes uden partnerdata (overslag 0).
2. A regnes med partner fra B.
3. B regnes med partner fra A.
4. Gentag, indtil begges jævne beløb ændrer sig mindre end 1 kr./md. i alle år, højst 6 gange.
   Når det ikke lykkes, gives advarslen `HUSSTAND_IKKE_KONVERGERET`.

**Optimering**: `optimer(profil_a med partner fra B, ...)` optimerer A, mens B er fast. Kernen
er uændret, fordi partnerdata allerede ligger i profilen.

## D2 Indgang (`app.py`) og oversættelse

- `guide.person.partner` er enten et overslag, `{foedselsdato, oevrig_indkomst_aar}`, eller en fuld
  profil med `"profil": {ordninger, atp_aarlig, folkekirkemedlem, antagelser:
  {folkepension_opsaettelse_aar}}`. Kommune, likvid formue (husstandens) og afkast/inflation er
  fælles.
- `beregn`: Er partneren en fuld profil, returneres `{...visning_a, "husstand": {"partner":
  visning_b, "samlet": samlet}}`. Ellers som i dag.
- `samlet`:
  - `maaned` = a + b, og hver for sig
  - `kalenderaar[]`
  - `dig[]` og `partner[]`: real netto pr. måned pr. kalenderår
  - `jaevn[]`: summen
  - `aldre_dig[]` og `aldre_partner[]`
  - `tidslinje`: begges ordninger og folkepension på kalenderår
- `optimer(guide, idag, fremdrift, hvem="dig"|"partner")`. For "partner" bytter indgangen
  rollerne.

## D3 Brugerflade

- **Guide**:
  - Civilstand får tre radioknapper.
  - For par: partnerens fødselsdato og "Hvor meget ved du om din partners pension?" ("Et overslag"
    | "Hele din partners pension").
  - Ved "hele": trin 3 "Din partners ordninger" med PDF-upload, ordninger, ATP og folkekirke. Trin
    4 er Forventninger, med opsættelse for begge.
  - Fremdriften viser 3 eller 4 trin.
- **Tilstand**:
  - `tilstand.partner = { ordninger, ... }` med ordnings-id'er "p1", "p2", … (unikke på tværs af
    personer).
  - `tilstand.hvem = "dig" | "partner" | "samlet"`.
  - Visningen for den aktive person er `tilstand.v`. Begge gemmes i `tilstand.vPr`.
- **Faner** (`role="tablist"`, piletaster) over resultatet. Den aktive person vises med de samme
  komponenter som i dag. Ændringer i tidslinje eller panel opdaterer `aktuelleSvar` for den
  aktive person, og alt regnes igen.
- **Samlet**: hero med parrets faste beløb og hvert beløb for sig, Chart.js stablet pr.
  kalenderår (dig/partner) med samlet linje, og en tidslinje til visning med begges rækker.

## Tests (test først)

- **Kerne**: `tests/golden/test_husstand.py`:
  - koblingen (tillæg med partnerens pension og ATP, fælles formue i ældrecheck)
  - gift og samlevende (personfradrag, KI-bundfradrag)
  - konvergens, symmetri (A og B byttet giver byttede resultater) og determinisme
- **Skat**: `tests/regler/test_skat_aegtefaeller.py` med golden cases i hånden.
- **App**: `beregn` med fuld partner (format, samlet = sum) og `optimer` med `hvem="partner"`
  (dig uændret).
- **Browser**: `tests/browser/test_partner.py`:
  - guidens 4 trin og partnerens PDF
  - fanerne med tastatur
  - et træk under Partner ændrer partnerens tal
  - samlet = sum
  - Pyodide = CPython
  - axe og 360 px

## Constitution Check

| # | Princip | Status |
|---|---|---|
| I og VI | Kernen er ren og deterministisk. Fastpunktet har loft | [x] |
| II og III | Nye regler (PSL § 10, stk. 3, og § 7, stk. 5) har kilde. Ingen nye satser (bundfradrag og personfradrag findes) | [x] |
| IV | Test først, golden cases i hånden | [x] |
| V | Advarsler for konvergens og forenkling | [x] |
| VII og XI | Partnerens rapport aflæses også lokalt | [x] |
| IX | Ingen nye afhængigheder. Samlet tidslinje kun til visning | [x] |
| X | Faner med tydelig mærkning. Samlet først det vigtigste tal | [x] |
