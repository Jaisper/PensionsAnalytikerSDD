# Feature Specification: Dine forsikringer fra PensionsInfo

**Feature Branch**: `031-risikodaekninger`

**Created**: 2026-11-01

**Status**: Draft

**Input**: "Det er vigtigt, at der hentes al relevant information fra PensionsInfo-rapporten om
risikoprodukter, så de kan indgå i overblikket."

**Grundlag**:
- Feature 003 (PDF-import): lokal, deterministisk parser (Princip XI)
- PensionsInfos demorapport ("Demo Demosen", fiktive data, udskrevet 15. april 2026) for layoutet.
  Den ligger ikke i repoet; testen mod den kører kun lokalt (`PENSIONSINFO_DEMO`).
- Legacy læste de samme afsnit med AI ("Liv og erstatning", "Tab af erhvervsevne", "Kritisk sygdom",
  "Sundhedsforsikring") og summerede dem til tre tal. Det er ikke genbrugt (A13).

## Problem

Rapporten indeholder også borgerens forsikringer ved død, tab af arbejdsevne, kritisk sygdom og
sundhed. Parseren sprang dem over ("Kun forsikring"), så overblikket viste kun pensionerne. Borgeren
kunne ikke se, hvad familien får, hvis hun dør, eller hvad hun får, hvis hun mister arbejdsevnen.

## Clarifications

### Session 2026-11-01

- Q: Hvilke dækninger? → A: Alle i rapporten: udbetaling ved død (også til børn), tab af
  arbejdsevne, visse kritiske sygdomme og sundhedsforsikring (også for børn).
- Q: Hvordan indgår de? → A: Som oversigt nu, et afsnit på resultatsiden. Scenarierne "Hvis du dør"
  (022) og "Hvis du mister arbejdsevnen" kommer senere og bygger på aflæsningen.
- Q: Hvilket layout bygges parseren efter? → A: Demorapporten og lokale kørsler mod produktejerens
  egen rapport. De rigtige tal forlader ikke maskinen, og intet fra rapporterne committes. Den
  syntetiske rapport i testene efterligner layoutet med opdigtede data.
- Q: Regner kernen med dækningerne? → A: Nej. De vises, som de står i rapporten (Princip I: ingen ny
  beregning). Beløbene er "den udbetaling, der ville være gældende i dag".

## Layout (demorapporten)

Hvert afsnit har en indholdsfortegnelse-post og 3–5 sider:

| Afsnit (sidehoved) | Overblik (tabel) | Detaljer |
|---|---|---|
| Udbetaling ved død | "Modtager" og én kolonne pr. udbetalingsform; grupper pr. modtager | Modtager, leverandør, aftalenr. og bemærkninger |
| Udbetaling ved død - børn | Som ovenfor; gruppen "Børn" | Som ovenfor |
| Udbetaling ved tab af arbejdsevne | "Pensioner" og kolonner pr. periode ("Mistet arbejdsevne", "Indtil 68 år"); grupper pr. form | Som ovenfor |
| Visse kritiske sygdomme | Grupper pr. form, én beløbskolonne | Som ovenfor |
| Sundhedsforsikring (- børn) | (ingen tabel) | Leverandør, bemærkninger og "Dækningsbeløb – op til" |

En række i tabellen har skattekoden (A, F eller S) til venstre for selskabet, derefter aftalenumret
og evt. en bemærkning ("Dækker indtil 80 år", "Dækningsbeløbet nedtrappes"). Detaljesiden har "Dækningen
ophører ved N år" og om dækningen er "tegnet med ret til præmiefritagelse".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Forsikringerne aflæses (Priority: P1)

**Acceptance Scenarios** (demorapporten):

1. **Given** demorapporten, **Then** aflæses fire dækninger ved død: ATP til ægtefælle 75.000 kr.
   (A, nedtrappes), Nykredit Bank til nærmeste pårørende 231.000 kr. (F, til 80 år), PFA Pension til
   begunstiget 2.258.000 kr. (F, til 68 år, procent af lønnen, præmiefritagelse) og PFA Pension til
   begunstiget 1.236.000 kr. (A, indtil pensionen er udbetalt). I alt 3.800.000 kr.
2. **Given** samme, **Then** aflæses ATP til børn 50.000 kr. (A, under 21 år).
3. **Given** samme, **Then** aflæses tab af arbejdsevne: PFA Pension 451.000 kr. om året (S) til 68 år,
   med præmiefritagelse.
4. **Given** samme, **Then** aflæses kritisk sygdom: PFA Pension 500.000 kr. på én gang (F).
5. **Given** samme, **Then** aflæses sundhedsforsikring hos PFA Pension, også for børn.
6. **Given** en rapport uden forsikringsafsnit, **Then** er der ingen dækninger, og ordningerne aflæses
   som før.
7. **Given** et forsikringsafsnit med et ukendt layout, **Then** springes afsnittet over med en
   bemærkning, og ordningerne aflæses som før.

### User Story 2 - Forsikringerne i overblikket (Priority: P1)

Resultatsiden får afsnittet "Hvis du bliver syg eller dør" med en gruppe pr. type: hvem der får hvad,
beløbet, skatten i ord og hvor længe dækningen gælder.

**Acceptance Scenarios**:

1. **Given** en aflæst rapport med forsikringer, **Then** vises afsnittet med grupperne og summen ved
   død som i rapporten.
2. **Given** ingen aflæste forsikringer, **Then** vises afsnittet ikke.
3. **Given** en gemt fil (024), **Then** følger forsikringerne med.

### User Story 3 - Din partners forsikringer (Priority: P2)

Med partnerens rapport (012) vises partnerens forsikringer i samme afsnit under sit eget navn.

## Requirements *(mandatory)*

- **FR-001**: Parseren MUST finde afsnittene via indholdsfortegnelsen og kun læse deres sider.
- **FR-002**: Pr. dækning MUST aflæses: type, selskab, aftalenr., skattekode, modtager, form, beløb pr.
  kolonne, alder dækningen gælder til, præmiefritagelse og bemærkninger.
- **FR-003**: Et afsnit, der ikke kan læses, MUST give en bemærkning og ingen dækninger fra det afsnit.
  Det MUST NOT få importen af ordninger til at fejle.
- **FR-004**: Dækningerne MUST NOT indgå i kernens beregning.
- **FR-005**: Afsnittet på resultatsiden MUST kun omformatere de aflæste tal (Princip X: svaret først).
- **FR-006**: Intet fra rapporten må skrives til disk, logs eller sendes til AI (Princip XI).

## Success Criteria *(mandatory)*

- **SC-001**: `tests/app/test_pensionsinfo_daekninger.py` er grøn mod den syntetiske rapport, og
  `PENSIONSINFO_DEMO=<sti> uv run pytest -k demo` er grøn lokalt.
- **SC-002**: Den eksisterende parsertest og `test_rigtig_rapport_lokalt` er uændret grønne.
