# Feature Specification: Hvor skal næste krone hen?

**Feature Branch**: `021-naeste-krone`

**Created**: 2026-10-27

**Status**: Implementeret 2026-10-27; se [plan.md](plan.md)

**Input**: Idéliste punkt 2: "Sammenlign ratepension, aldersopsparing, aktiesparekonto og afdrag på
lån for én ekstra indbetaling. Vis fradrag nu mod skat og modregning senere. Afslør
ratepensionsfælden for folk med lav pension. Husk det højere loft for aldersopsparing de sidste
fem år før folkepensionsalderen."

**Grundlag**:
- 017: løn og arbejdsår. Fradragsværdien kræver skatten i arbejdsårene.
- 013b: aktiesparekonto og frit depot som alternativer.
- 014: afdrag på lån (først når boliglån findes).
- Kernen: indbetalingslofter for ratepension og aldersopsparing (inkl. forhøjet loft) ligger i
  registret.

## Problem

Borgeren kan ikke se, om en ekstra krone gør mest gavn i pensionen eller uden for den. For folk med
lav pension kan fradraget for ratepension nu blive spist af modregning i pensionstillægget senere
("ratepensionsfælden").

## Forslag til metode

Én ekstra indbetaling afprøves pr. alternativ, med samme beløb før skat fra lønnen:
- ratepension: fradrag nu, beskattet og modregnet ved udbetaling
- aldersopsparing: ingen fradrag, skattefri, ingen modregning
- aktiesparekonto: beskattet løn, lagerskat, ingen modregning
- bank: beskattet løn, kapitalindkomst
- afdrag på lån: renteudgift sparet (kræver 014)

Målet er det faste beløb (kr./md., dagens kroner). Forskellen fra i dag vises pr. alternativ med
"fradrag nu" og "skat og modregning senere" side om side (Princip V).

## Clarifications

- **Besluttet 2026-10-27 (som foreslået):** Én gang eller årligt? → et årligt beløb fra i dag til stopalderen
  (017). En engangsindbetaling kommer som variant.
- **Besluttet 2026-10-27 (som foreslået):** Arbejdsgiverordning eller privat indbetaling? → privat, så
  sammenligningen er fair (samme løn før skat). ~~Topskattegrundlaget lægges til for privat
  ratepension (PSL § 7, stk. 1).~~ Holder ikke; se clarify nedenfor.
- **Besluttet 2026-10-27 (som foreslået):** Hvordan måles gevinsten for et par? → husstandens samlede faste
  beløb (012).
- **Besluttet 2026-10-27 (som foreslået):** Afdrag på lån før 014? → udelad, og vis en tekst om, at det kommer.

### Clarify 2026-10-27 (primærkilder)

- **Privat ratepension og topskattegrundlaget:** Antagelsen holder ikke. PSL § 7, stk. 1, lagde
  før beløb under PBL § 16, stk. 1, til grundlaget. Det gjaldt kapitalpension og står ikke i den
  gældende tekst for mellem-, top- og toptopskat (lov nr. 482 af 22/05/2024). Private indbetalinger
  til ratepension fradrages i den personlige indkomst (PSL § 3, stk. 2, nr. 3; skat.dk: "fradrag i
  den personlige indkomst", rubrik 416). Loftet er 68.700 kr. i 2026 (PBL § 18, i registret).
  - Kernen regner allerede indbetalingen som fradrag i den personlige indkomst med AM-bidrag af
    hele lønnen. Det svarer til privat indbetaling. Der er derfor ingen ny regel, og forenklingen
    `pensionsindbetaling_som_arbejdsgiverordning` dækker forskellen.
- **Samme beløb før skat:** Ratepensionen får beløbet før skat. Alternativerne uden fradrag får
  det, ratepensionen koster efter skat: lønnen efter skat falder lige meget i alle alternativer. Så
  er det faste beløb fra stopalderen et fair mål. Beløbet er gennemsnittet over arbejdsårene i
  dagens kroner, og kernen regulerer det.
- **Aldersopsparing med løn:** Indbetalingen betales af beskattet løn. Den trækkes derfor fra årets
  rådighedsbeløb (`Aarsresultat.indskud_opsparing`), som løbende indskud på opsparing. Det retter
  også 017's arbejdsår, som før ikke trak indbetalingen fra.

## Lovgrundlag

| Kobling | Kilde | Status |
|---|---|---|
| Fradrag for ratepension med årligt loft | PBL § 18 | verificeret (registret) |
| Aldersopsparing: lille loft, forhøjet de sidste år før folkepensionsalderen | PBL § 16 | verificeret (registret) |
| Privat ratepension fradrages i den personlige indkomst; intet tillæg til mellem-/topskattegrundlaget | PSL § 3, stk. 2, nr. 3, og § 7 (gældende tekst); skat.dk | verificeret 2026-10-27 |
| Ratepension modregnes i pensionstillægget; aldersopsparing og ASK ikke | LSP § 29 | verificeret |
| ASK: lagerskat og loft | Aktiesparekontoloven | verificeret (013) |

## User Scenarios (kort)

- **US1 (P1)**: "Hvor skal 10.000 kr. om året hen?" giver en tabel med alternativerne og ændringen
  i det faste beløb. Det bedste står øverst, med forbehold.
- **US2 (P1)**: Ratepensionsfælden forklares med borgerens tal, når aldersopsparing slår
  ratepension.
- **US3 (P2)**: Loftet for aldersopsparing og ASK respekteres. Alternativet vises som "fuldt
  udnyttet", når loftet er nået.

## Requirements (udvalg)

- **FR-001**: Hvert alternativ er en fuld beregning i kernen med ændret indbetaling (ingen
  genveje).
- **FR-002**: Beløbet er det samme før skat for alle alternativer.
- **FR-003**: Søgningens omfang og antagelserne vises.
- **SC**: Under 3 s for fem alternativer i browseren (målt som 018).

## Afhængigheder og størrelse

- Forudsætter 017 (bygget) og 013b. Lille til mellem, når 013b findes, fordi beregningen genbruger
  scenariemønstret fra 018.
