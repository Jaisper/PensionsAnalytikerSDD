# Feature Specification: Tidslinje og datapanel

**Feature Branch**: `004-tidslinje`

**Created**: 2026-10-25

**Status**: Draft

**Input**: "Tag funktionelt udgangspunkt i legacy UI. Der skal være en datasektion, der kan åbnes og
lukkes, en grafisk præsentation af udbetalinger over tid og de enkelte ordninger præsenteret
under grafikken med skydere, så de kan rykkes rundt i tid."

**Grundlag**:
- Legacy-UI (`legacy/static/index.html`): `parametre-panel`, `chart-panel` og `renderTimeline`
  med én række pr. produkt, der kan trækkes
- Forfatningens Princip X
- Feature 002

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ryk ordningerne rundt i tid (Priority: P1)

Under grafen ser borgeren én række pr. ordning (fx "Nordea · Ratepension"). Hver række har en
bjælke, der viser, hvornår ordningen udbetaler. Borgeren flytter starten med en skyder og ser
straks graf og hovedtal ændre sig. Ratepensioner har også en skyder til udbetalingsperioden.
Folkepensionen har en række med en skyder til at udskyde den.

**Why this priority**: Det er den beslutning, borgeren skal træffe: hvornår skal hvad udbetales.
Legacy havde funktionen, og den blev brugt.

**Independent Test**: Flyt startalderen på én ordning. Bjælken flytter sig, kernen regner
igen, og graf og hovedtal opdateres. Bjælkerne står på samme aldersakse som grafen.

**Acceptance Scenarios**:

1. **Given** et resultat med 3 ordninger, **When** tidslinjen vises, **Then** er der 3
   ordningsrækker og 1 folkepensionsrække, og hver bjælke starter ved ordningens startalder.
2. **Given** en ratepension, **When** perioden ændres fra 10 til 15 år, **Then** bliver bjælken
   længere, og grafen viser udbetalingen til og med den nye slutalder.
3. **Given** en startalder under ordningens tidligste lovlige alder, **When** skyderen
   flyttes dertil, **Then** er det ikke muligt: skyderens minimum er den tidligste alder
   (oplyst af selskabet eller udledt efter loven).
4. **Given** en ændring, kernen afviser, **When** den sendes, **Then** vises kernens danske
   besked ved rækken, og skyderen vender tilbage.
5. **Given** tastatur eller skærmlæser, **When** tidslinjen bruges, **Then** kan alle skydere
   betjenes med piletaster, og hver skyder har en label med ordningens navn.

### User Story 2 - Datapanel (Priority: P1)

Øverst på resultatsiden ligger et panel, "Dine oplysninger", som er lukket fra start og kan
åbnes og lukkes. Det indeholder alle guidens felter (om dig, ordninger og forventninger) på én
side. Borgeren retter direkte og trykker "Opdater beregning".

**Why this priority**: Fjerner omvejen via "Ny beregning" (åbent fund A3 i
ux-evaluering 002). Svarer til legacy's parameterpanel.

**Acceptance Scenarios**:

1. **Given** resultatsiden, **When** "Dine oplysninger" åbnes, **Then** ses alle felter
   udfyldt med de aktuelle værdier.
2. **Given** en rettet saldo, **When** borgeren trykker "Opdater beregning", **Then**
   regnes der igen, og panelet forbliver åbent.
3. **Given** ændringer fra tidslinjens skydere, **When** panelet åbnes, **Then** viser det
   samme startalder og periode som tidslinjen.

### User Story 3 - Udbetaling over tid som panel (Priority: P2)

Grafen står i fuld bredde i et panel, "Udbetaling over tid", som kan foldes sammen, med
tidslinjen lige under. Hero'en beholder svaret og viser nøgletal i højre side:
- folkepensionsalder
- samlet opsparing i dag
- første private udbetaling
- engangsbeløb

## Requirements *(mandatory)*

- **FR-001**: Tidslinjen MUST bruge samme aldersakse som grafen (samme første og sidste år og
  samme pixel pr. år) og følge med, når grafen ændrer størrelse.
- **FR-002**: Hver privat ordning MUST have en skyder til startalder fra den tidligste lovlige
  alder (fra API'et) til akseslut. Ratepension MUST også have en skyder til periode (10–30
  år; minimum og maksimum fra registret via API).
- **FR-003**: Folkepensionsrækken MUST have en skyder til opsættelse (0 til registrets maksimum).
- **FR-004**: Engangsbeløb (aldersopsparing og kapitalpension) vises som en markør på ét år.
- **FR-005**: Alle ændringer MUST regnes af kernen (Princip I). Tidslinjen viser kun brugerens
  valg (start, periode) og kernens grænser.
- **FR-006**: API'et MUST for hver ordning returnere tidligste lovlige alder og om den er oplyst
  af selskabet. Det MUST også returnere grænserne for ratepensionens periode og
  folkepensionens opsættelse fra regelregistret (Princip II).
- **FR-007**: Datapanelet MUST være lukket fra start, have `aria-expanded` og indeholde alle
  guidens felter. "Opdater beregning" MUST validere og regne.
- **FR-008**: Datapanel og tidslinje MUST holdes synkrone (samme data).
- **FR-009**: Princip X gælder: ingen vandret scroll ved 360 px (tidslinjen stables, så
  skyderne står under bjælken), WCAG 2.2 AA og axe uden fejl.

## Success Criteria

- **SC-001**: En ændring af en skyder viser et nyt hovedtal på under 1 sekund.
- **SC-002**: Bjælkernes startpunkt ligger højst 2 px fra den tilsvarende søjle i grafen.
- **SC-003**: axe-core: 0 overtrædelser. Ingen vandret scroll ved 360 px.

## Assumptions

- Træk med musen direkte på bjælkerne (som i legacy) er ikke med i denne version. Skyderne
  giver samme funktion, og de er tilgængelige for tastatur og skærmlæser.
