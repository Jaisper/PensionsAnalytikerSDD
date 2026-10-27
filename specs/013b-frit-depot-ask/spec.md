# Feature Specification: Frit depot og aktiesparekonto

**Feature Branch**: `013b-frit-depot-ask`

**Created**: 2026-10-27

**Status**: Draft – besluttet 2026-10-27 (som foreslået); clarify med primærkilder før plan

**Input**: 013's godkendte opdeling: "013b: frit depot (aktieindkomst, realisation) og ASK, med
registersatser".

**Grundlag**:
- 013 (bank som aktiv, opsparing i planen eller urørt).
- 013's spec, afsnittene Clarifications og Lovgrundlag. Her er satser og kilder for aktieindkomst,
  ASK og § 29 verificeret.
- 017 (løn): borgerens indkomst i arbejdsårene er kendt.
- Forenklingsregistret: `afkast_som_kapitalindkomst` skal kunne bortfalde, når depotet modelleres.

## Problem

Har borgeren aktier eller investeringsfonde, er skatten og pensionstillægget forkerte i dag.
Afkastet beskattes som renter, men aktier beskattes som aktieindkomst, og afkast på
aktiesparekonto tæller slet ikke i pensionstillægget.

## Clarifications

### Besluttet i 013 (2026-10-25)

- Den urealiserede gevinst er 50 % som standard. Den vises som antagelse og kan ændres.
- Hvert aktiv har én ejer.
- Grænsen på 5.000 kr. aktieudbytte i § 29 gælder pr. person (status `sekundaer`).

### Besluttet 2026-10-27

- **Besluttet 2026-10-27 (som foreslået):** Standardrækkefølgen for træk. → bank → frit depot (lagerbeskattede
  fonde først, derefter aktier med mindst gevinst) → aktiesparekonto sidst, fordi den har lavest
  skat og ikke tæller i pensionstillægget.
- **Besluttet 2026-10-27 (som foreslået):** Skal udbytte og kursgevinst have hver sin afkastantagelse? → én
  samlet antagelse pr. aktivtype fra Rådet for Afkastforventninger, opdelt med en fast
  udbytteandel som antagelse.
- **Besluttet 2026-10-27 (som foreslået):** Løbende indskud på aktiesparekontoen frem til stopalderen (017)?
  → ja, et årligt beløb op til loftet. Overskydende indskud går til frit depot med
  advarsel.
- **Besluttet 2026-10-27 (som foreslået):** Tab ved salg (negativ aktieindkomst)? → uden for scope. Det
  registreres som forenkling.

## Lovgrundlag (Princip III)

Se 013, spec.md. Kort:

| Kobling | Kilde | Status |
|---|---|---|
| Aktieindkomst 27 %/42 % med progressionsgrænse 79.400 kr. (2026); overførsel mellem gifte | PSL §§ 4 a, 8 a, stk. 1–4 | verificeret |
| Lagerbeskattede investeringsbeviser (obligationsbaserede) er kapitalindkomst | ABL §§ 19 B–C | verificeret |
| Aktiesparekonto: 17 % lagerskat, loft 174.200 kr. (2026) | Aktiesparekontoloven; skat.dk | verificeret |
| Aktieindkomst i § 29 undtagen udbytte op til 5.000 kr.; ASK-afkast ikke | LSP § 29 | verificeret (pr. person: sekundær) |
| ASK og depot er likvid formue | LSP § 72 d, stk. 2 | verificeret |

## User Scenarios (kort)

- **US1 (P1)**: Trinnet "Din opsparing uden for pension" får frit depot (med "heraf urealiseret
  gevinst") og aktiesparekonto.
- **US2 (P1)**: Salg fra depot beskattes som aktieindkomst i salgsåret, og gevinsten tæller i § 29.
  ASK beskattes med lagerskat hvert år og tæller ikke i § 29.
- **US3 (P1)**: Trækrækkefølgen kan ændres. Grænsefladen kan senere bruges af optimering.
- **US4 (P2)**: Advarsel ved salg over progressionsgrænsen med forslag om at sprede salget.

## Requirements (udvalg)

- **FR-001**: Skattekasserne `aktieindkomst_realisation` og `aktiesparekonto` med registersatser.
- **FR-002**: Trækstrategi med fast rækkefølge og en grænseflade (013 FR-004).
- **FR-003**: Forenklingen `afkast_som_kapitalindkomst` gælder kun aktiver af typen bank.
- **FR-004**: Golden cases for aktieindkomst over og under grænsen, med og uden overførsel
  mellem gifte, og for ASK.

## Afhængigheder og størrelse

- Bygger på 013 og 017. Mellemstor: ny skattekasse, rækkefølge og guidefelter.
- Risiko: fastpunktet kan konvergere langsommere med flere skattekasser. Mål det mod SC fra 013.
