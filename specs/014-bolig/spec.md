# Feature Specification: Bolig og friværdi

**Feature Branch**: `014-bolig`

**Created**: 2026-10-27

**Status**: Draft – modnes

**Input**: 013's afgrænsning: "014 Bolig og friværdi: bliv boende, nedskalering i et valgt år,
seniorlån/belåning (negativ kapitalindkomst), ejendomsværdiskat og grundskyld. Friværdi tæller ikke
som likvid formue."

**Grundlag**:
- 013: husstandsbalancen har passiver i modellen, men de bruges ikke endnu.
- 013b: trækrækkefølge, så salgsprovenu kan placeres.
- Kernen modellerer ikke negativ kapitalindkomst i dag (`ingen_renteudgifter` i
  forenklingsregistret).

## Problem

Boligen er for mange den største formue og den største udgift. Boligskatterne, renterne og et
eventuelt salg påvirker både det faste beløb, pensionstillægget og ældrechecken.

## Foreslået opdeling

| Del | Indhold | Prioritet |
|---|---|---|
| 014a | Boligskatter som udgift: ejendomsværdiskat og grundskyld år for år | P1 |
| 014b | Lån og renter: renteudgift som negativ kapitalindkomst med fradrag og skattenedslag | P1 |
| 014c | Nedskalering: salg i et valgt år. Friværdien bliver likvid opsparing (013) | P2 |
| 014d | Seniorlån/belåning af friværdien som indtægtskilde | P3 |

## Lovgrundlag (første research 2026-10-27)

| Kobling | Kilde | Status |
|---|---|---|
| Ejendomsværdiskat 0,51 % af beskatningsgrundlaget op til progressionsgrænsen, 1,4 % over (2026) | Ejendomsskatteloven; Ældre Sagen | sekundær |
| Beskatningsgrundlag = 80 % af den offentlige vurdering; progressionsgrænse 9,2 mio. kr. i grundlag | Samme; FT SAU spm. (2024-25) | sekundær |
| Ekstra nedslag for ejere, der ejede boligen pr. 1. juli 1998 | Samme | sekundær |
| Grundskyld: kommunal promille af grundværdien | Ejendomsskatteloven | uverificeret (kommunale satser skal i registret) |
| Renteudgifter fradrages i kapitalindkomsten | PSL § 4; Den juridiske vejledning C.A.11.2 | sekundær |
| Skattenedslag for negativ nettokapitalindkomst (8 % op til 50.000 kr., 100.000 kr. for gifte) | PSL; skatteguide 2026 | uverificeret |
| Renter på lån efter lov om individuel boligstøtte / pensionisters boligstøtte kan ikke fradrages | Den juridiske vejledning C.A.11.2 | sekundær |
| Friværdi er ikke likvid formue | LSP § 72 d, stk. 2 | verificeret |
| Indefrysning af ejendomsskatter for pensionister | Ejendomsskatteloven | uverificeret |

## Clarifications (forslag i kursiv)

- [NEEDS CLARIFICATION: Grundskyldspromiller for alle kommuner. *Forslag: et kommuneregister som for
  kommuneskat (`kommuner_<år>.toml`), med kilde.*]
- [NEEDS CLARIFICATION: Indefrysning (obligatorisk eller frivillig for pensionister) og
  overgangsregler. *Forslag: slå op før plan; måske først i 014d.*]
- [NEEDS CLARIFICATION: Boligens værdi frem i tiden. *Forslag: følger inflationen (antagelse).
  Vurderingen kan angives.*]
- [NEEDS CLARIFICATION: Afdrag på lån? *Forslag: med i 014b som fast ydelse; det bruges også af 021
  ("afdrag på lån").*]

## Afhængigheder og størrelse

- Bygger på 013 og 013b. Stor, derfor opdelt. 014a er lille, når grundskyldsregistret findes.
- Negativ kapitalindkomst (014b) ændrer skattemotoren og skal have egne golden cases.
