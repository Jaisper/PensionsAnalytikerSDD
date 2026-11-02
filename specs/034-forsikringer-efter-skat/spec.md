# Feature Specification: Dine forsikringer – kort med beløb efter skat

**Feature Branch**: `034-forsikringer-efter-skat`

**Created**: 2026-11-02

**Status**: Draft – afklaret 2026-11-02. Afgiften ved død skal verificeres mod lovteksten før plan.

**Input**: "Kan vi ikke lave en mere grafisk lækker præsentation af risikoprodukter? Det er lidt
fesent lige nu. Og måske vise f.eks. livsforsikringselementer også efter est. skat?"

**Grundlag**:
- Feature 031: forsikringerne aflæses fra PensionsInfo-rapporten med skattekode (A, F eller S),
  modtager, form, beløb og ophørsalder (`AflaestDaekning`)
- Princip III: skatten følger loven, og en sats kræver en kilde i registret. Princip X: klarhed før
  fuldstændighed
- Lovgrundlag (første research, sekundær kilde): udbetaling ved død fra kapitalpension og
  kapitalforsikring er afgiftspligtig med 40 % (pensionsbeskatningsloven § 25, stk. 1, nr. 1 og 6;
  Den juridiske vejledning C.A.10.2.5.4.5). Rateordninger ved død omregnet til engangsbeløb: 40 %
  (PBL § 29, stk. 1). Lavere satser gælder for visse ordninger med indbetalinger før 1980 (PBL § 14 A)

## Problem

Afsnittet "Hvis du bliver syg eller dør" er lange punktlister med beløb før skat. Det er svært at se,
hvad familien faktisk får, og hvornår dækningerne ophører.

## Clarifications

### Session 2026-11-02

- Q: Skattepligtig (S) til efterladte, hvis indkomst er ukendt? → A: **Før skat med forklaring**:
  "beskattes som indkomst hos modtageren". Intet skøn.
- Q: Tab af arbejdsevne (løbende, skattepligtig til borgeren selv)? → A: **Efter skat med kernen**:
  skatten af dækningen regnes oven i borgerens øvrige indkomst det år, som resten af værktøjet.
- Q: Visningen? → A: **Kort med stort tal**: ét kort pr. situation med ikon, det samlede beløb efter
  skat stort og før skat småt, en bjælke pr. selskab, "dækker til 70 år" som mærke og detaljerne
  foldet ud.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hvad familien får, hvis du dør (Priority: P1)

**Acceptance Scenarios**:

1. **Given** dækninger ved død med skattekode A, F og S, **Then** viser kortet "Hvis du dør" det
   samlede beløb efter skat for A (60 %) og F (100 %), og S lagt til før skat med teksten "heraf X kr.
   beskattes som indkomst hos modtageren".
2. **Given** dækninger fra flere selskaber, **Then** er der en bjælke pr. selskab med beløbet efter
   skat, og bjælkernes længde svarer til beløbene.
3. **Given** en dækning, der ophører ved 70, **Then** står der "dækker til 70 år" på kortet. Ophører de
   ved forskellige aldre, står den tidligste med "nogle dækninger ophører fra 65".
4. **Given** en løbende dækning ved død (årrække eller livsvarig), **Then** vises den særskilt som
   "X kr. om året" og indgår ikke i engangsbeløbet.

### User Story 2 - Hvis du mister arbejdsevnen (Priority: P1)

1. **Given** en løbende, skattepligtig dækning ved tab af arbejdsevne, **Then** viser kortet beløbet
   pr. måned efter skat, regnet af kernen for borgerens første år med dækningen, og før skat småt.
2. **Given** at borgeren har løn, **Then** regnes skatten som ved tab af lønnen (dækningen erstatter
   lønnen), ikke oven i den.

### User Story 3 - Kritisk sygdom og sundhed (Priority: P2)

1. **Given** dækninger ved kritisk sygdom (typisk skattefri), **Then** viser kortet det samlede beløb,
   og børnenes dækninger særskilt.
2. **Given** en sundhedsforsikring, **Then** viser kortet, hvem der er dækket, hos hvem, og til hvornår.

### Edge Cases

- Ukendt skattekode: beløbet vises før skat med "skatten kendes ikke".
- Beløb 0 eller ukendt: dækningen vises i detaljerne, ikke i summen.
- Ingen dækninger: afsnittet er skjult som i dag.

## Requirements *(mandatory)*

- **FR-001**: Afgiften ved død MUST komme fra registret (`forsikring.doed.afgift`, 40 %) med kilde.
  Posten har status "sekundær", indtil den er verificeret mod lovteksten (Princip III).
- **FR-002**: Skatten af tab af arbejdsevne MUST regnes af kernen med borgerens kommune, kirke og
  fradrag, som ved løn. Visningslaget må kun omformatere.
- **FR-003**: Hvert kort MUST vise beløbet efter skat stort og før skat småt, med skatteformen i ord
  (afgift 40 %, skattefri, beskattes som indkomst).
- **FR-004**: Bjælkerne MUST have en tekst med selskab og beløb (ikke kun længde) og kunne læses af
  skærmlæsere (WCAG 2.2 AA). Kortene har samme skriftstørrelse som resten af siden.
- **FR-005**: Forudsætningen "Beløbene er det, der ville blive udbetalt i dag" MUST stå på afsnittet.
- **FR-006**: Kortene MUST tilpasse sig skærmbredden: tre ved siden af hinanden på en computer, ét pr.
  linje på en mobil.

## Success Criteria *(mandatory)*

- **SC-001**: Golden cases for afgiften (A, F, S) og for tab af arbejdsevne efter skat med og uden løn.
- **SC-002**: Browsertest af kortene med den syntetiske rapport og axe-core uden fejl.
- **SC-003**: Hele suiten grøn.
