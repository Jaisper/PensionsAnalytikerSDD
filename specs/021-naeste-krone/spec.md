# Feature Specification: Hvor skal næste krone hen?

**Feature Branch**: `021-naeste-krone`

**Created**: 2026-10-27

**Status**: Draft – modnes

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

## Clarifications (forslag i kursiv)

- [NEEDS CLARIFICATION: Én gang eller årligt? *Forslag: et årligt beløb fra i dag til stopalderen
  (017). En engangsindbetaling kommer som variant.*]
- [NEEDS CLARIFICATION: Arbejdsgiverordning eller privat indbetaling? *Forslag: privat, så
  sammenligningen er fair (samme løn før skat). Topskattegrundlaget lægges til for privat
  ratepension (PSL § 7, stk. 1).*]
- [NEEDS CLARIFICATION: Hvordan måles gevinsten for et par? *Forslag: husstandens samlede faste
  beløb (012).*]
- [NEEDS CLARIFICATION: Afdrag på lån før 014? *Forslag: udelad, og vis en tekst om, at det kommer.*]

## Lovgrundlag

| Kobling | Kilde | Status |
|---|---|---|
| Fradrag for ratepension med årligt loft | PBL § 18 | verificeret (registret) |
| Aldersopsparing: lille loft, forhøjet de sidste år før folkepensionsalderen | PBL § 16 | verificeret (registret) |
| Privat ratepension lægges til topskattegrundlaget | PSL § 7, stk. 1 | uverificeret |
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
