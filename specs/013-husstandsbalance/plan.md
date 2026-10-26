# Implementation Plan: 013 Husstandsbalance – opsparing uden for pension (bank)

**Branch**: `013-husstandsbalance` | **Spec**: [spec.md](spec.md) | **Dato**: 2026-10-25

## Resumé

Opsparing uden for pension bliver et rigtigt aktiv i kernen. Den forrentes, afkastet beskattes som
kapitalindkomst, og opsparingen tæller i ældrechecks formuegrænse. Borgeren vælger pr. aktiv, om
det bruges i det faste beløb (som 009-bufferen) eller står urørt.

013 leverer kun skattekassen `kapitalindkomst` (bank, obligationer o.l.). Frit depot,
aktiesparekonto og trækrækkefølge kommer i 013b (se den godkendte opdeling i spec'en).

## Tekniske beslutninger

### Model (kerne)

- `Aktiv(id, saldo, type="bank", i_plan=True)`. `Pensionsprofil.opsparing: tuple[Aktiv, ...]`.
  - Ejeren er den profil, aktivet ligger i. Husstanden (012) har to profiler, og balancen er
    summen af begges aktiver.
  - `type` har kun værdien `bank` i 013. Skattekassen og om aktivet er likvidt, udledes af typen
    i kernen. Brugeren angiver dem ikke.
- Afkast: samme rente som 009-bufferen, dvs. pensionens afkast før PAL-skat
  (`afkast_efter_pal / (1 − pal.sats)`). Der indføres ingen ny standardsats. Afkast pr. aktivtype
  kommer i 013b sammen med depot og ASK.
- Output: `Fremskrivning.formue: tuple[FormueAar, ...]` med `FormueAar(alder, i_plan,
  uden_for_plan)` ved årets udgang, fra i dag til beregningens sidste år.
  - `i_plan` er den opsparing, der bruges i det faste beløb: bankaktiver med `i_plan=True` og
    bufferen fra engangsbeløb.
  - `uden_for_plan` er de urørte aktiver.
  - `Fremskrivning.formue_primo()` giver formuen pr. 1. januar pr. alder. Den bruges til
    partnerens formue i husstanden (012) og erstatter `bufferens_ki_og_formue`.

### Fremskrivning

- **Før første udbetalingsår** (`tabel_start`) vokser alle aktiver med renten før skat.
  - Skatten af afkastet i disse år betales af borgerens løn, som kernen ikke kender (hul 1). Den
    regnes derfor ikke med. Det markeres som forenkling og vises i advarslen om opsparing.
- **Aktiver i planen** indsættes i bufferen primo `tabel_start` med deres fremskrevne saldo
  (`engangs_i_buffer`). Derefter er de 009-bufferen: forrentes, beskattes som kapitalindkomst,
  tæller i formuen og bruges af udjævningen uden lån (010).
- **Urørte aktiver** vokser videre med renten.
  - Årets afkast er kapitalindkomst. Det lægges til bufferens kapitalindkomst, så skatten regnes
    progressivt samlet (bundfradrag og skatteloft, PSL § 7 og § 19). Afkastet indgår også i
    indtægtsgrundlaget (LSP § 29).
  - Skatten af afkastet betales af den løbende udbetaling, ligesom bufferens. Saldoen vokser
    derfor brutto.
  - Saldoen pr. 1. januar tæller i husstandens likvide formue (LSP § 72 d, stk. 2).
  - Urørte aktiver afhænger ikke af fastpunktet, så de regnes én gang før iterationen.
- `likvid_formue` beholder sin betydning fra 001: en fast formue, der kun tæller i ældrechecken.
  Gamle input giver derfor samme resultat (FR-006, SC-001).

### Brugerflade

- Nyt guidetrin 4 **"Opsparing uden for pension"**. "Forventninger" bliver trin 5. Partnertrinnet (3)
  vises stadig kun ved en fuld partnerprofil.
  - Dig: beløb (`#bank`) og afkrydsningen "Brug opsparingen i min faste udbetaling" (standard: ja).
  - Fuld partner: de samme to felter for partneren (`#p-bank`, `#p-bank-i-plan`).
  - Overslag over partneren: "Din partners opsparing" (`#partner-formue`) → `likvid_formue`.
    Partnerens beløb kendes kun som et tal, så det tæller kun i ældrechecken (som før).
  - Feltet "Opsparing uden for pension" i trin 1 fjernes. Det flyttes til trin 4.
- Guide-JSON: `person.opsparing` og `person.partner.profil.opsparing` er lister af
  `{id, type, saldo, i_plan}`. `person.likvid_formue` bevares.
- Resultat (US4): en fold-ud **"Din formue over tid"** under grafen. Den viser restformuen ved
  planens sidste år og en tabel pr. år (i planen, urørt, i alt) i dagens kroner. Under "Samlet"
  vises husstandens formue.
- Bufferkurven hedder nu "Opsparing uden for pension, som bruges", fordi den også rummer bankaktiver.

## Afvigelser fra spec'en (besluttet i planen)

| Spec | Beslutning | Begrundelse |
|---|---|---|
| US1 scenarie 2: gammel `likvid_formue` bliver bankindestående med uændret resultat | `likvid_formue` beholder sin gamle betydning. Brugerfladen bruger den kun til partnerens opsparing ved overslag | En bankkonto forrentes, beskattes og bruges. Det giver nødvendigvis et andet resultat. Begge dele kan ikke opfyldes |
| FR-004 trækrækkefølge | Flyttes til 013b | Med én skattekasse har rækkefølgen ingen virkning. Grænsefladen designes, når der er to kasser at vælge imellem |
| FR-007 afkast pr. aktivtype | 013 bruger pensionens afkast før PAL-skat (som 009) | Ingen ny standardsats uden kilde. Satser pr. type kommer med depot og ASK i 013b |
| US4 restformue | Aktiver i planen er brugt op ved planens slutning (udjævning uden lån). Restformuen er de urørte aktiver | Det følger af 010. "Bevar X til arvinger" hører til 015 |

## Constitution check

- **Princip II/III**: ingen nye satser. Bundfradrag, skatteloft, PAL-sats og formuegrænse findes
  i registret. Afkastet er en vist antagelse.
- **Princip IV**: test først (tasks T001–T004 før implementering).
- **Princip VII/XI**: alt regnes i browseren. Ingen nye afhængigheder.
- **Princip X**: ét spørgsmål pr. felt, forklaring i konteksten, axe 0 fejl, 360 px uden vandret scroll.
- **SC-001**: ingen golden case ændres. Uden opsparing er beregningen identisk.

## Risici

- Ydelse: urørte aktiver regnes én gang og påvirker ikke antallet af iterationer.
- Det nye trin forlænger guiden med ét klik. Trinnet kan springes over (alle felter er valgfrie).
