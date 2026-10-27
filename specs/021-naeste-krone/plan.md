# Implementation Plan: 021 Hvor skal næste krone hen?

**Branch**: `021-naeste-krone` | **Spec**: [spec.md](spec.md) | **Dato**: 2026-10-27

## Metode

`app.naeste_krone(guide, idag, beloeb)` regner en fuld beregning pr. alternativ (FR-001). Den
ændrer kun borgerens svar og bruger ingen genveje. Det kræver løn (017), fordi indbetalingen
kommer af lønnen frem til stopalderen.

1. **Ratepension**: Beløbet før skat indbetales hvert år på en ny ratepension (oprettet i dag, 10
   år). Den starter, når borgerens første ratepension starter, ellers ved folkepensionsalderen.
   - Kernen fradrager indbetalingen i den personlige indkomst og respekterer loftet. Det
     overskydende regnes som livsvarig pension.
   - **Prisen** er gennemsnittet af faldet i nettoindkomsten i arbejdsårene, i dagens kroner.
2. **Aldersopsparing, aktiesparekonto og bank** får prisen som årligt indskud. Lønnen efter skat
   falder lige meget i alle alternativer, og det svarer til samme beløb før skat (FR-002).
   - Aldersopsparing er en ny ordning med samme start. Kernen respekterer loftet, også det
     forhøjede.
   - Aktiesparekonto og bank er løbende indskud på opsparing (013b), som bruges i planen.
3. **Målet** er det faste beløb i gennemsnit fra stopalderen (kr./md., dagens kroner). For et par
   er det husstandens samlede beløb (012).
   - Hovedtallet er det laveste niveau og kan ikke bruges. Udjævningen låner aldrig (010), så
     penge, der først kommer ved folkepensionsalderen, løfter ikke årene før.
   - Hovedtallet ville derfor favorisere bank og ASK, som kan bruges fra stopalderen.
     Gennemsnittet tæller alle pengene med.

   Ud over forskellen fra i dag vises:
   - **Fradrag nu**: ratepensionens skattebesparelse pr. år. Det er beløbet minus prisen.
   - **Skat og modregning senere** (kr./md., dagens kroner, gennemsnit fra stopalderen): mer-skat
     plus tabt pensionstillæg, ældrecheck og mediecheck i forhold til i dag.
   - **Loft nået**: når indbetalingen rammer loftet for aldersopsparing eller ASK.
4. **Ratepensionsfælden** (US2): Den vises, når aldersopsparingen giver mere end ratepensionen,
   og ratepensionen giver modregning senere. Teksten bruger borgerens tal.
5. **Afdrag på lån**: Det vises som en tekst om, at det kommer med bolig (014).

## Kerneændringer

- `Aktiv.aarligt_indskud` gælder nu bank og frit depot (uden loft) ud over ASK. Indskuddet kræver
  stadig løn.
- **Aldersopsparing med løn**: Indbetalingen betales af beskattet løn og trækkes fra årets
  rådighedsbeløb (`indskud_opsparing`). Det retter 017's arbejdsår. Hovedtallet fra stopalderen er
  uændret.

## Brugerflade

- Sektionen "Hvor skal næste krone hen?" står ved "Hvornår kan jeg stoppe?" og har et felt for
  beløbet (standard 10.000 kr. om året) og knappen "Sammenlign".
- Resultatet vises som en tabel, sorteret efter det faste beløb. Under tabellen står fælden,
  forbeholdene og omfanget (Princip V).
- Beregningen kører i worker'en. SC: under 3 s for alternativerne, målt i browseren.

## Constitution check

- **Princip III**: ingen nye satser. Lofter og skatter kommer fra registret.
- **Princip V**: alle alternativer, antagelser og forbehold vises.
- **Princip VII og XI**: uændret.
