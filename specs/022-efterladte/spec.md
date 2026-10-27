# Feature Specification: Hvad hvis min partner dør?

**Feature Branch**: `022-efterladte`

**Created**: 2026-10-27

**Status**: Draft – modnes

**Input**: Idéliste punkt 5: "Et efterladtescenarie bygget på 012: enlig-satser for
pensionstillæg, ophør af livrente uden ægtefælledækning og pensioner til begunstigede."

**Grundlag**:
- 012: husstanden med to fulde profiler, koblet efter loven.
- 018/019: scenarier i baggrunden og tabellen "Hvad hvis …".
- 013: opsparing uden for pension (afdødes del).

## Problem

De fleste beregnere overser, hvad der sker med økonomien, når den ene i et par dør. Pensionstillægget
skifter til enlig-satser, livrenten kan ophøre, og skattefordelene mellem ægtefæller bortfalder.

## Lovgrundlag (første research 2026-10-27)

| Kobling | Kilde | Status |
|---|---|---|
| Efterlevelsespension: lever begge af pension og bor sammen, fortsætter afdødes pension til den efterlevende i op til tre måneder; derefter enlig-sats | Lov om social pension; borger.dk, "Pension ved dødsfald – efterlevelsespension" | sekundær (borger.dk); paragraffen skal citeres |
| Efterlevelseshjælp, hvis efterlevelsespension ikke gives, med indkomstgrænse og ansøgningsfrist | borger.dk, "Efterlevelseshjælp" | sekundær |
| Rater fra en ratepension til efterlevende er skattepligtig personlig indkomst | Den juridiske vejledning C.A.10.2.2.4.3 | sekundær (tax.dk) |
| Konverteres raterne til et engangsbeløb, betales 40 % afgift i stedet for indkomstskat | Samme | sekundær |
| Livrente ophører ved død, medmindre der er valgt ægtefælledækning eller garantiperiode før udbetalingen | Pensionsselskabernes vilkår; Skagen/Velliv FAQ | uverificeret (vilkår, ikke lov) |
| Ægtefæller betaler ikke boafgift | Boafgiftsloven | sekundær (Ældre Sagen) |
| Formuegrænsen og pensionstillægget bliver enlig-satser | LSP § 29, § 72 d | verificeret (kernen) |
| Overførsel af personfradrag mellem ægtefæller bortfalder efter dødsåret | PSL § 10, stk. 3 | uverificeret (dødsåret) |

## Clarifications (forslag i kursiv)

- [NEEDS CLARIFICATION: Hvem dør, og hvornår? *Forslag: borgeren vælger "din partner" eller "dig"
  og en alder. Standard er partnerens forventede levealder (019).*]
- [NEEDS CLARIFICATION: Ægtefælledækning på livrenten. PensionsInfo-rapporten kan indeholde den.
  *Forslag: et felt pr. livrente ("fortsætter til efterlevende: nej / X år / livsvarigt, Y %"),
  standard nej. Det aflæses fra rapporten, hvis det står der.*]
- [NEEDS CLARIFICATION: Afdødes ratepension og kapitalpension. *Forslag: den efterlevende
  ægtefælle fortsætter raterne (personlig indkomst). Kapitalpension og aldersopsparing udbetales
  til den efterlevende; afgiften slås op før plan.*]
- [NEEDS CLARIFICATION: ATP ved død. *Forslag: uden for scope (ATP Livslang Pension ophører;
  eventuelle engangsbeløb er sjældne). Registreres som forenkling.*]
- [NEEDS CLARIFICATION: Samlevende (ikke gift). *Forslag: samme ydelsesregler, men ingen
  skattefordele og arv kun ved testamente. Vis en advarsel.*]

## User Scenarios (kort)

- **US1 (P1)**: I tabellen "Hvad hvis …" står "Hvis din partner dør som X-årig": dit faste beløb
  før og efter, i dagens kroner.
- **US2 (P1)**: Forklaringen (020) siger, hvad der ændrer sig: tre måneders efterlevelsespension,
  enlig-satser, livrenten ophører eller fortsætter, raterne fra afdødes ratepension.
- **US3 (P2)**: Afdødes opsparing uden for pension og udbetalte pensioner indgår i den
  efterlevendes opsparing (ingen boafgift for ægtefæller).

## Requirements (udvalg)

- **FR-001**: Scenariet er en ny beregning af den efterlevende som enlig fra dødsåret, med
  overgangsregler i dødsåret og de tre måneder efter.
- **FR-002**: Livrentens dækning er et input pr. ordning. Uden oplysning ophører den (forsigtigt).
- **FR-003**: Alle nye satser og frister i registret med kilde (Princip II).

## Afhængigheder og størrelse

- Bygger på 012, 018 og 019. Mellemstor. Den største usikkerhed er dækningen på livrenter og
  reglerne for afgift ved død, som skal verificeres før plan.
