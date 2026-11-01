# Feature Specification: Stopalderen følger første udbetaling

**Feature Branch**: `030-stopalder-foelger`

**Created**: 2026-10-31

**Status**: Draft

**Input**: "Der er bøvl, hvis man ikke initielt vælger år for pensionering – så hænger man efterfølgende
fast i pensionsalder som startår, også selvom udbetaling af pensioner rykkes frem i tid. Pensionsalder
skal følge det år, man vælger første udbetaling (hvis som buffer)."

**Grundlag**:
- Feature 017 (løn og stopalder): `Loen.stop_alder`, "None = folkepensionsalderen"
- Feature 007b (den bedste plan): ingen ordning starter før pensionsalderen
- Princip III: stopalderen er en modelantagelse, ikke lovgivning. Den skal være synlig og kunne ændres.

## Problem

Uden en valgt stopalder regnede kernen med løn til folkepensionsalderen. Rykkede borgeren sine
udbetalinger frem, fik hun løn og pension samtidig, og det faste beløb begyndte først ved
folkepensionsalderen. Den bedste plan brugte også folkepensionsalderen som nedre grænse og skubbede
udbetalingerne tilbage dertil.

## Clarifications

### Session 2026-10-31

- Q: Hvilke udbetalinger tæller som første udbetaling? → A: Alle, der bruges i det faste beløb:
  ratepension, livrente og engangsbeløb i bufferen (også portioner og omlagt kapitalpension).
  Engangsbeløb, der udbetales direkte, tæller ikke.
- Q: Må den bedste plan flytte stopalderen, når den ikke er valgt? → A: Nej. Den udledes af borgerens
  egen plan, før der søges, og ligger fast. Et forslag skal have sin første udbetaling netop dér, så
  stopalderen er den samme, når forslaget bruges.
- Q: Hvad hvis alle ordninger starter efter folkepensionsalderen? → A: Stopalderen er højst
  folkepensionsalderen. Folkepensionen er også en udbetaling.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stopalderen følger, når den ikke er valgt (Priority: P1)

Borgeren har en løn, men har ikke skrevet en stopalder. Lønnen stopper det år, den første udbetaling
begynder. Rykkes udbetalingen frem eller tilbage, følger stopalderen med.

**Acceptance Scenarios**:

1. **Given** løn, ingen stopalder, ratepension fra 65 og livrente fra 67 (folkepension 69), **Then**
   stopper lønnen ved 65, og det faste beløb gælder fra 65.
2. **Given** samme, **When** ratepensionen rykkes til 63, **Then** stopper lønnen ved 63.
3. **Given** en kapitalpension, der udbetales direkte ved 62, **Then** er stopalderen stadig 65.
4. **Given** en kapitalpension i bufferen ved 62, **Then** er stopalderen 62.
5. **Given** alle ordninger fra 70 og folkepension fra 69, **Then** er stopalderen 69.
6. **Given** en valgt stopalder, **Then** gælder den, uanset udbetalingerne.

### User Story 2 - Den bedste plan holder stopalderen fast (Priority: P1)

**Acceptance Scenarios**:

1. **Given** ingen valgt stopalder og første udbetaling ved 64, **Then** starter ingen ordning i
   forslaget før 64, og mindst én starter ved 64.
2. **Given** forslaget bruges, **Then** er hovedtallet forslagets beløb (som 008 SC-001).

## Requirements *(mandatory)*

- **FR-001**: Kernen MUST have én funktion, `stopalder(profil, fp_alder)`: den valgte stopalder,
  ellers den tidligste start blandt ordningerne, der bruges i det faste beløb, højst
  folkepensionsalderen.
- **FR-002**: Fremskrivningen, valideringen, optimeringen og "Næste krone" MUST bruge den.
- **FR-003**: Optimeringen MUST regne alle kandidater med den udledte stopalder og afvise
  kandidater, hvis første udbetaling ikke er netop dér.
- **FR-004**: Feltet i guiden MUST forklare reglen: "Lader du feltet stå tomt, stopper du, når din
  første udbetaling begynder (højst ved folkepensionsalderen)."

## Success Criteria *(mandatory)*

- **SC-001**: `tests/golden/test_stopalder_foelger.py` og `tests/optimering/` er grønne.
- **SC-002**: Ændrede golden cases i `tests/optimering/test_pensionsalder.py` er begrundet (Princip IV).
