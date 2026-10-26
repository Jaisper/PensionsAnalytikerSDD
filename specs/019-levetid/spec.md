# Feature Specification: Levetid som scenarie

**Feature Branch**: `019-levetid`

**Created**: 2026-10-26

**Status**: Draft

**Input**: Besluttet 2026-10-26 som et billigere alternativ til Monte Carlo (016): "Levetid som
scenarie (85/90/95 år), som 018". For danske pensioner er levetiden ofte en større risiko end
afkastet: ratepension og opsparing slipper op, men livrenten og folkepensionen gør ikke.

**Grundlag**:
- 018: scenarier i baggrunden og tabellen "Hvad hvis …".
- `Antagelser.livsvarig_horisont_alder` (90) styrer i dag både livrentens størrelse og, hvornår
  planen slutter (tabellen og udjævningen).

## Problem

Planen bruger opsparingen op til 90 år (udjævning uden lån, 010). Borgeren kan ikke se, hvad der
sker ved et længere liv. Borgeren kan heller ikke se, hvor meget mere der kunne
bruges om måneden, hvis planen kun skulle række til 85 år.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fast beløb ved kortere eller længere plan (Priority: P1)

Tabellen "Hvad hvis …" (018) får to rækker mere: "Planen rækker til 85 år" og "Planen rækker til
95 år", hver med det faste beløb.

**Acceptance Scenarios**:

1. **Given** en plan til 95 år, **Then** er det faste beløb lavere end eller lig planen til 90 år.
   Ved 85 år er det højere end eller lig.
2. **Given** en livrente, **Then** er livrentens årlige ydelse den samme i alle tre planer.
   Selskabet fastsætter den, og den betales, så længe borgeren lever.

### User Story 2 - Hvis du lever længere end planen (Priority: P1)

Under tabellen står: "Planen bruger din opsparing op til 90 år. Lever du længere, har du derefter
ca. Z kr. om måneden fra folkepension, ATP og livrente (i dagens kroner)."

**Acceptance Scenarios**:

1. **Given** en profil med ratepension og opsparing, **Then** er Z indkomsten efter skat i året
   efter planens slutning, uden ratepension og opsparing.
2. **Given** fanen "Samlet" (012), **Then** vises sætningen ikke, fordi parret når planens
   slutning i forskellige år.

### Edge Cases

- **En ratepension, der løber efter 85 år**: Planen til 85 år forlænges til ratepensionens sidste
  år (som i dag med 90).
- **Opsat folkepension**: Ventetillægget beregnes stadig efter registrets middellevetid. Det
  ændres ikke af scenariet.

## Requirements *(mandatory)*

- **FR-001**: Kernen MUST have en planhorisont (`Antagelser.plan_slut_alder`), der er adskilt fra
  livrentens beregningshorisont. Uden den bruges `livsvarig_horisont_alder` (uændret resultat).
- **FR-002**: Scenarierne MUST være 85 og 95 år, defineret ét sted (indgangslaget) som antagelser.
- **FR-003**: Indkomsten efter planens slutning MUST komme fra kernens beregning med planen til
  95 år (året efter den normale plans slutning). Den udjævnes ikke.
- **FR-004**: Visningen omformaterer kun (Princip I).

## Success Criteria *(mandatory)*

- **SC-001**: Uden planhorisont er alle tests og golden cases uændrede.
- **SC-002**: Golden case: livrenten er ens i de tre planer, og det faste beløb falder med planens
  længde.
- **SC-003**: Samme resultat i Pyodide og CPython.
- **SC-004**: Alle otte scenarier (018 og 019) er regnet på under 3 s for et par i browseren.
