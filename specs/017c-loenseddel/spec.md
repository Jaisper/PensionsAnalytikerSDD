# Feature Specification: 017c Løn som på lønsedlen

**Feature Branch**: `017c-loenseddel` | **Oprettet**: 2026-10-28 | **Status**: Implementeret 2026-10-28
**Input**: Brugerønske: "i stedet for årsløn kan månedsløn brutto angives samt eget og firmabidrag i %
(og her kan i parentes angives hvor meget pensionsrapport antyder bliver indbetalt pr. måned). Giver det
ikke et bedre billede – og noget der kan ses på lønseddel?!"

## Brugerhistorier

- **US1 (P1)**: Som lønmodtager skriver jeg min bruttoløn pr. måned og min egen og firmaets
  pensionsprocent, som de står på lønsedlen. Siden regner selv indbetalingen og min nettoløn ud.
- **US2 (P2)**: Har jeg indlæst min PensionsInfo-rapport, ser jeg ved procenterne, hvor meget rapporten
  viser bliver indbetalt om måneden, så jeg kan tjekke mine procenter.
- **US3 (P2)**: Har jeg flere ordninger, vælger jeg, hvilke der får pensionen fra lønnen. Beløbet
  fordeles som i min rapport.

## Krav

- **FR-001**: `Loen` får `pension_eget` og `pension_firma` (andele af bruttolønnen). Er mindst én af dem
  over 0, er `Loen.aarlig` bruttolønnen før pension, som på lønsedlen (månedsløn × 12).
- **FR-002**: Kernen regner med lønnen inklusive firmaets pension, `aarlig × (1 + firma)`, og en samlet
  indbetaling efter AM-bidrag på `aarlig × (eget + firma) × (1 − AM-sats)`. Så bliver
  - AM-bidraget 8 % af løn og hele pensionsbidraget (AMBL § 2, stk. 1, nr. 1 og 4),
  - indbetalingen til rate og livsvarig trukket fra før skat (PSL § 19, stk. 1),
  - indbetalingen til aldersopsparing beskattet som løn (PSL § 19, stk. 1, 3. pkt.) og betalt af
    lønnen efter skat (som i 021),
  - grundlaget for beskæftigelses- og jobfradrag lønnen inklusive pensionsbidraget (LL § 9 J, stk. 1).
- **FR-003**: Indbetalingen går til ordninger med `fra_loen`. Den fordeles efter ordningernes
  `aarlig_indbetaling` (fra rapporten eller indtastet), og ligeligt, hvis de alle er 0. Ordninger, der
  allerede udbetaler, er ikke med. Ordninger uden `fra_loen` beholder deres eget beløb.
- **FR-004**: Procenterne skal være mellem 0 og 100 %. Er der procenter, men ingen ordning med
  `fra_loen`, er det en fejl ved firmaets procent.
- **FR-005**: Guiden spørger om bruttoløn pr. måned og de to procenter, for borgeren og en fuld partner.
  Gemte svar med årsløn (024) åbnes som månedsløn = årsløn / 12.
- **FR-006**: PDF-indlæsningen giver rapportens samlede indbetaling pr. måned før AM-bidrag. Guiden
  viser den ved procenterne: "PensionsInfo viser ca. X kr. om måneden". Indlæste ordninger med en
  indbetaling får `fra_loen`.
- **FR-007**: Forenklingen `pensionsprocent_af_bruttoloen`: procenterne regnes af hele bruttolønnen.
  På lønsedlen er de ofte af den pensionsgivende løn, som kan være lavere.

## Afklaringer (primærkilder)

- AMBL § 2, stk. 1, nr. 4: arbejdsgiverens indbetalinger til pensionsordninger er bidragspligtige "i
  samme omfang som" efter PSL § 19. Egen andel i en arbejdsgiverordning indbetales af arbejdsgiveren.
  Kilde: danskelove.dk/arbejdsmarkedsbidragsloven/2.
- PSL § 19, stk. 1: arbejdsgiverens indbetaling medregnes ikke; "gælder ikke præmier og bidrag til
  aldersopsparing, aldersforsikring". Kilde: danskelove.dk/pensionsbeskatningsloven/19.
- LL § 9 J, stk. 1: grundlaget omfatter AMBL § 2, stk. 1, nr. 1, 2, 4 og 6 (ratepension og ophørende
  livrente kun op til bortseelsesretten). Kilde: danskelove.dk/ligningsloven/9j.

## Succeskriterier

- **SC-001**: Med 40.000 kr./md., 4 % og 8 % er lønkildens personlige indkomst `0,92 × (480.000 − 19.200)`,
  og ordningen får `0,92 × 57.600` (golden test).
- **SC-002**: Fordelingen følger rapportens forhold; ordninger uden `fra_loen` er uændrede (golden test).
- **SC-003**: Guiden sender månedsløn og procenter, og hintet fra rapporten vises (browsertest).
