# Feature Specification: Den bedste plan – hvornår, med hvilke forventninger, og hvad den giver

**Feature Branch**: `036-bedste-plan-status`

**Created**: 2026-11-23

**Status**: Draft – afklaret 2026-11-23, klar til implementering

**Input**: "Næste issue går på 'Find bedste plan' – og hvornår den skal bruges og ikke bruges. Tænker vi
fortsat skal køre aut fra start, og hvis bruger selv har tastet afkastforv så vis med brugers egen
forventninger. Man skal også kunne køre videre bare med std forv fra afkastrådet (skriv det tydeligt der
hvor man selv kan taste forventninger – det behøver man så ikke). Nede på siden skal det fremgå mere
tydeligt hvornår man skal genberegne; lige nu rykker grafer rundt og det er uklart hvad Find bedste så
giver."

**Grundlag**:
- 007 (Find bedste plan), 007b (den bedste plan med det samme), 032 ("Finder bedste plan …"),
  033/033b (equalizeren og én knap), 035/035b (altid branchestandard; egne estimater skiftes ved
  resultatet).
- Princip X: svaret først, højst én primær handling, og brugeren skal kunne se, hvad der er sket.

## Problem

1. **To fremstillinger af det samme.** Søgningen ved start anvender den bedste plan og viser den ved
   hovedtallet med "Brug min egen plan". Knappen under grafen viser et forslag med stiplede bjælker og
   "Anvend"/"Behold min plan".
2. **Status forsvinder stille.** Flyttes en bjælke, ændres fordelingen eller afkastet, regnes alt
   forfra med det samme, og linjen "Det er den bedste plan" forsvinder uden forklaring. Borgeren kan
   ikke se, om det viste stadig er den bedste plan, eller hvad "Find bedste plan" vil give.
3. **Egne forventninger i guiden er tvetydige.** Skyderne har altid en værdi (4 % og 2 %), så guiden
   kan ikke se, om borgeren har valgt egne forventninger. Efter 035b regnes der altid med
   branchestandarden fra start, også når borgeren har sat sine egne.
4. Det står ikke tydeligt i guiden, at man ikke behøver udfylde forventningerne.

## Clarifications

### Session 2026-11-23

- Q: Skal ændringer stadig regnes med det samme? → A: **Ja (produktejer).** Graf og tal opdateres med
  det samme, men en fast statuslinje siger altid, om det viste er den bedste plan, og tilbyder "Find
  bedste plan igen", når det ikke er.
- Q: Hvordan vises resultatet af "Find bedste plan", når borgeren trykker? → A: **Som ved start
  (produktejer).** Den bedste plan bruges med det samme, og "Brug min egen plan" fortryder. Forslaget
  med stiplede bjælker og "Anvend"/"Behold min plan" (007) udgår.
- Q: Skal den bedste plan søges igen, når borgeren skifter mellem branchestandarden og egne
  estimater? → A: **Nej (produktejer).** Planen beholdes, og statuslinjen siger, at den er fundet med
  de andre forventninger, og tilbyder "Find bedste plan igen".
- Q: Hvordan ved guiden, at borgeren har valgt egne forventninger? → A: En afkrydsning "Jeg vil bruge
  mine egne forventninger". Skyderne vises først, når den er sat. Gemte filer uden afkrydsningen åbnes
  med branchestandarden som efter 035b.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Forventningerne i guiden (Priority: P1)

**Acceptance Scenarios**:

1. **Given** trin 5 i guiden, **Then** står der tydeligt, at man ikke behøver udfylde noget, og at vi
   så regner med Rådet for Afkastforventningers forudsætninger, som pensionsselskaberne bruger.
   Skyderne for afkast og inflation er skjult.
2. **When** borgeren sætter "Jeg vil bruge mine egne forventninger", **Then** vises skyderne.
3. **Given** afkrydsningen ikke er sat, **When** der regnes, **Then** er grundlaget branchestandard,
   og den bedste plan søges med det.
4. **Given** afkrydsningen er sat, **When** der regnes, **Then** er grundlaget egne estimater, og den
   bedste plan søges med borgerens afkast og inflation. Hovedtallet siger det.
5. **Given** en gemt fil med afkrydsningen, **Then** åbnes den med egne estimater. Uden (fx gemt før
   036) åbnes den med branchestandarden.

### User Story 2 - Status for planen (Priority: P1)

Under equalizeren og over tidslinjen står altid én statuslinje for planen.

**Acceptance Scenarios**:

1. **While** den bedste plan søges, **Then** står der "Finder bedste plan …" med fremdrift og
   "Afbryd".
2. **Given** den viste plan er den bedste, **Then** står der det, og "Find bedste plan" er sekundær.
3. **Given** borgeren har valgt sin egen plan ("Brug min egen plan"), **Then** står der, hvor meget
   mere den bedste plan giver.
4. **Given** planen allerede var den bedste, **Then** står der "Din plan er allerede den bedste, vi kan
   finde."
5. **When** borgeren flytter en bjælke, ændrer fordelingen, retter i data eller ændrer afkast eller
   inflation, **Then** regnes tallene med det samme, og statuslinjen siger, at planen er ændret og ikke
   længere er den bedste, vi har fundet. "Find bedste plan igen" er primær. Linjen ved hovedtallet
   siger det samme kort.
6. **When** borgeren skifter grundlag ved hovedtallet, **Then** søges der ikke igen. Statuslinjen
   siger, at planen er fundet med de andre forventninger, og "Find bedste plan igen" er primær.
7. **When** borgeren skifter mellem egen og bedste plan, **Then** er det ikke en ændring (5).
8. Statuslinjen siger kort, hvad "Find bedste plan" gør: flytter, hvornår og hvor længe ordningerne
   udbetales, så det faste beløb bliver højest. Forventninger og fordeling ændres ikke.

### User Story 3 - Én fremstilling af resultatet (Priority: P1)

**Acceptance Scenarios**:

1. **When** borgeren trykker "Find bedste plan", **Then** søges der for begge i husstanden fra den
   viste plan, som ved start. Den viste plan bliver "din egen plan".
2. **Given** en bedre plan, **Then** bruges den med det samme. Hovedtallet viser den, linjen ved
   hovedtallet viser beløbet med den egne plan, ændringerne og "Brug min egen plan".
3. **When** borgeren trykker "Afbryd", **Then** er planen og tallene uændrede.
4. **Given** ændret fordeling (033b), **Then** søges der fra borgerens egen plan med den nye
   fordeling som i dag.

## Requirements *(mandatory)*

- **FR-001**: Trin 5 MUST have en afkrydsning "Jeg vil bruge mine egne forventninger", som er fra som
  udgangspunkt og viser skyderne for afkast og inflation. En tekst MUST sige, at feltet kan springes
  over, og at der så regnes med Rådet for Afkastforventningers forudsætninger.
- **FR-002**: Grundlaget ved første beregning MUST være `egne`, når afkrydsningen er sat, ellers
  `branchestandard`. Afkrydsningen gemmes (024). Ny beregning nulstiller ikke afkrydsningen.
- **FR-003**: Statuslinjen MUST have én af tilstandene: søger, bedste, egen, allerede bedste, ændret
  og andet grundlag. Tilstanden udledes af den viste plan sammenlignet med planerne fra seneste
  søgning, så den er korrekt efter enhver ændring.
- **FR-004**: "Find bedste plan" MUST bruge samme søgning og visning som ved start (007b) og kunne
  afbrydes. Forslagsboksen og de stiplede bjælker (007) udgår.
- **FR-005**: Skift af grundlag MUST NOT starte en søgning.
- **FR-006**: Kun visning. Kernen og optimeringen er uændrede (Princip I).
- **FR-007**: Statuslinjen MUST være en `role="status"`-region, og knappen MUST kunne nås med
  tastatur (WCAG 2.2 AA).

### Uden for denne feature

- At samle flere ændringer før genberegning (fravalgt).
- At søge automatisk efter hver ændring (fravalgt i 033b: uroligt).

## Success Criteria *(mandatory)*

- **SC-001**: Browsertest for hver tilstand i statuslinjen og for afkrydsningen i guiden.
- **SC-002**: Kernens og optimeringens tests er uændrede. Browsertestene for 007's forslagsboks
  erstattes af test for den fælles visning.
- **SC-003**: axe-core uden fejl og ingen vandret rulning ved 360 px.
