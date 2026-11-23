# Feature Specification: Partnerne hver for sig – fordeling, afkast og grundlag

**Feature Branch**: `037-partner-uafhaengig`

**Created**: 2026-11-23

**Status**: Draft – afklaret 2026-11-23, klar til implementering

**Input**: "equalizer sliders skal være uafhængige mellem partnerne; ligesom afkast forv skal være det – de skal
kunne køre hver for sig"

**Grundlag**:
- 012 (partner som fuld profil): kernen regner hver person med sit eget sæt antagelser
  (`oversaet.til_husstand`). I dag er partnerens sæt en kopi af ens eget, kun opsættelsen er partnerens.
- 033 ("Én profil for husstanden", `husstand.faelles_forbrug`), 035/036 (grundlag og egne forventninger).
- Princip III: fordelingen og forventningerne er borgerens egne valg, ikke lovregler.

## Clarifications

### Session 2026-11-23

- Q: Equalizeren pr. partner? → A: **Egne bånd fra egen stopalder og egne procenter (produktejer).**
  Erstatter 033's "Én profil for husstanden".
- Q: Hvilke forventninger er hver for sig? → A: **Afkastet. Inflationen er husstandens fælles
  (produktejer)**, så "dagens kroner" er det samme for begge, og beløbene kan lægges sammen.
- Q: Grundlaget (pensionsselskabernes eller egne forventninger)? → A: **Pr. partner (produktejer).**
  Skifteren ved hovedtallet gælder den person, hvis fane vises.
- Konsekvens (oplyst produktejer): branchestandarden har sin egen inflation (Rådets langsigtede). Regner
  den ene som pensionsselskaberne og den anden med egne forventninger, er inflationen derfor ikke den
  samme. Husstandens inflation gælder dem med egne forventninger, og en note siger det, når grundlagene
  er forskellige.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fordelingen hver for sig (Priority: P1)

1. **Given** et par, **When** borgeren ændrer equalizeren under sin egen fane, **Then** ændres kun
   egen fordeling. Partnerens er uændret, og omvendt under partnerens fane.
2. **Given** du stopper ved 63 og partneren ved 67, **Then** er dine bånd 63–67, 68–72, … og
   partnerens 67–71, 72–76, … hver i egne aldre.
3. **Given** et input uden partnerens egne felter (gemt før 037), **Then** bruger partneren dine
   værdier som før, men båndene regnes fra partnerens egen stopalder.

### User Story 2 - Afkast og grundlag hver for sig (Priority: P1)

1. **When** borgeren ændrer afkastet under "Prøv andre forudsætninger" på partnerens fane, **Then**
   ændres kun partnerens afkast. Inflationen er fælles og ændres for begge.
2. **When** borgeren skifter grundlag ved hovedtallet på partnerens fane, **Then** skifter kun partneren.
3. **Given** forskellige grundlag, **Then** står der en note om, at inflationen ikke er den samme.
4. Usikkerhedsscenarierne (018) flytter begges afkast med samme antal procentpoint.

### User Story 3 - Gem og åbn (Priority: P2)

1. **Given** et gemt par, **When** filen åbnes, **Then** er begges fordeling, afkast og grundlag som
   før. (Fund: din egen fordeling blev ikke gemt før 037.)

## Requirements *(mandatory)*

- **FR-001**: Input MUST kunne have `person.partner.antagelser` med `afkast_efter_pal`,
  `beregningsgrundlag` og `forbrugsprofil`. Mangler et felt, bruges dit (bagudkompatibelt). En tom
  `forbrugsprofil` er flad. `inflation` er altid husstandens.
- **FR-002**: Hver persons forbrugsprofil MUST regnes fra personens egen stopalder (`faelles_forbrug`
  udgår).
- **FR-003**: Brugerfladen MUST skrive equalizer, afkast og grundlag til den person, hvis fane vises.
  Ved første beregning for et par får partneren en kopi af dine værdier og en flad fordeling.
- **FR-004**: Scenarierne (018) MUST flytte partnerens afkast med samme forskel som dit, også i
  stresstestens år (023a).
- **FR-005**: Gem (024) MUST indeholde begges fordeling og partnerens afkast og grundlag.

## Success Criteria *(mandatory)*

- **SC-001**: Golden cases: partnerens bånd fra egen stopalder; partnerens egen profil og eget afkast
  påvirker kun partneren (og husstandens fælles ydelser).
- **SC-002**: De to golden cases for den fælles profil (033) erstattes med begrundelse: produktejerens
  beslutning 2026-11-23. Øvrige tests uændrede.
- **SC-003**: Browsertest for fanerne, gem og åbn. Hele suiten grøn.
