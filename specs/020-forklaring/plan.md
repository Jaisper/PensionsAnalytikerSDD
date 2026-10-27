# Implementation Plan: 020 Forklaring – del 1: forenklingsregistret

**Branch**: `020-forklaring` | **Spec**: [spec.md](spec.md) (FR-005, FR-006 for forenklinger) | **Dato**: 2026-10-26

Besluttet: forenklingsregistret laves før 017. Resten af 020a og 020b–d planlægges efter 017.

## Tekniske beslutninger

- **Fil**: `src/pensionskerne/register/forenklinger.toml`. Én post pr. forenkling:
  - `id`, `titel`
  - `beskrivelse`: hvad vi gør
  - `begrundelse`: hvorfor
  - `betydning`: hvordan det påvirker resultatet og i hvilken retning
  - `omfang`: `markeret` (gælder kun, når kernen markerer den i et år) eller `altid`
  - `kilde`: feature eller dokument
- **Læsning**: `register.forenklinger()` giver en tuple af `Forenkling`. Ingen tal (Princip II),
  men paragrafnumre er tilladt.
- **Kernen**: markeringer har formen `o.marker("forenkling:<id>")`. Ny markering:
  `opsparing_skat_foer_udbetaling` (013). Den findes i dag kun som advarsel.
- **Visning**: `byg_visning` giver `forenklinger` som en liste: først de markerede, der er brugt i
  beregningen (`anvendt: true`), derefter dem, der altid gælder.
- **Brugerflade**: en ny fold-ud i "Sådan har vi regnet", "Se vores forenklinger". Hver post har
  titel, beskrivelse, begrundelse og betydning. De, der påvirker borgerens beregning, står
  øverst og er markeret med tekst (ikke kun farve).

## Indhold ved start

Fra kernens markeringer og domænedokumentet (afsnit 3 og 7d–7h):

- markeret: anden kapitalindkomst beskattes ikke, partnerens indkomst fra nærmeste år, opsparingens
  skat før første udbetaling
- altid:
  - skatten fordelt på kilderne
  - afkast beskattet som kapitalindkomst (ikke aktieindkomst)
  - intet fradrag for renteudgifter
  - samme afkast hvert år
  - ingen løn efter stop eller før pension
  - partnerens løn kendes ikke
  - kapitalpension fra før 1980

## Test (først)

- Hver `o.marker("forenkling:…")` i `src/pensionskerne` findes i registret, og hver markeret post
  bruges af en markering.
- Alle felter er udfyldt, id'erne er unikke, og omfanget er gyldigt.
- Visningen giver de anvendte markerede og alle, der altid gælder, men ikke ubrugte markerede.
- Browser: fold-ud'en viser posterne, axe 0 fejl.
