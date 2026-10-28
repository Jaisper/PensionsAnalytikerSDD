# Feature Specification: Afkast pr. år og "dårlige år først"

**Feature Branch**: `023-afkast-pr-aar`

**Created**: 2026-10-27

**Status**: 023a implementeret 2026-10-28 (afkast pr. år og "dårlige år først"). 023b (afkast pr.
aktivtype, flyttet hertil fra 013b) mangler.

**Input**: Besluttet 2026-10-26 som trin før Monte Carlo (016): "Et fast stress-forløb, fx −15 % de
første to år efter pensionsstart og derefter normalt afkast. Viser sekvensrisikoen uden statistik.
Kræver, at kernen kan regne med et afkast pr. år."

**Grundlag**:
- 018: scenarier i baggrunden og tabellen "Hvad hvis …".
- Kernen bruger i dag ét fast afkast: opsparing frem til start, `rateplan`, `livsvarig_ydelse`,
  `portioner` og bufferens rente.
- Forenklingsregistret: `samme_afkast_hvert_aar`.

## Problem

Kommer de dårlige år lige efter pensionsstart, rammer de en stor opsparing, og det faste beløb
bliver lavere, end gennemsnittet lover (sekvensrisiko). Det kan værktøjet ikke vise i dag.

## Forslag til metode

- **Kernen** får `Antagelser.afkast_forloeb: Mapping[int, float] | None`: afkast efter PAL-skat pr.
  kalenderår. Mangler et år, bruges `afkast_efter_pal`. Uden forløb er alt som før (SC-001).
- **Ratepension**: raten genberegnes hvert år som restværdi / resterende år (PBL § 11 A), så et
  dårligt år giver lavere rater bagefter. Med fast afkast er det den samme formel som i dag.
- **Livsvarig pension**: selskaberne udjævner normalt. Besluttet: ydelsen ændres ikke af forløbet
  (forenkling).
- **Bufferen og opsparingen** forrentes med årets afkast.
- **Stress-scenariet** "Dårlige år først" lægges i tabellen "Hvad hvis …" (018) som et scenarie.

## Clarifications

- **Besluttet 2026-10-27 (som foreslået):** Hvor dårlige er "dårlige år"? Et tal kræver en kilde. → to år med
  afkast på forventet afkast minus to standardafvigelser for en blandet pensionsportefølje, ud fra
  Rådet for Afkastforventninger. Med 50 % aktier og 50 % obligationer er standardafvigelsen ca.
  8–9 % (skal regnes og citeres). Alternativt det faktiske 2008-forløb for en typisk
  markedsrentepension (historisk eksempel, ikke prognose).
- **Besluttet 2026-10-27 (som foreslået):** Hvornår rammer de? → de to første år fra første udbetaling (eller
  stopalderen med løn, 017).
- **Besluttet 2026-10-27 (som foreslået):** Kommer "gode år først" også? → ja, symmetrisk, så spændet ikke ser
  ensidigt ud.

- **Afklaret 2026-10-28 (primærkilde):** Rådet for Afkastforventninger, "Afkastforventninger for 2.
  halvår 2026" (afkastforventninger.dk), standardafvigelser for år 1–10: stats- og
  realkreditobligationer 3,9 %, globale aktier (developed markets) 16,2 %, korrelation 0,0. Med 50/50
  er σ = ½·√(16,2² + 3,9²) ≈ 8,33 %. To standardafvigelser efter PAL-skat (15,3 %): ≈ 14,1
  procentpoint. Med 4 % efter PAL er et dårligt år ≈ −10,1 % og et godt ≈ +18,1 %.
- **Afklaret 2026-10-28:** "Gode år først" kan ikke hæve hovedtallet, når det laveste år er det
  første (udjævningen låner aldrig, 010). Det hæver de senere år.
- **Afklaret 2026-10-28:** Stress-scenarierne indgår ikke i spændet ved hovedtallet (som levetid,
  019). De står kun i tabellen.
- **023b (åben):** Afkast pr. aktivtype (bank, depot, aktiesparekonto og pension hver for sig).
  Kræver en kilde pr. type (Rådets tabeller) og et valg af blanding.

## Lovgrundlag

| Kobling | Kilde | Status |
|---|---|---|
| Rate = restværdi / resterende år | PBL § 11 A | verificeret (kernen) |
| Afkastforventninger og standardafvigelser pr. aktivklasse | Rådet for Afkastforventninger (2. halvår 2026) | primær (afkastforventninger.dk, hentet 2026-10-28) |

## Requirements (udvalg)

- **FR-001**: Afkast pr. år i alle dele af kernen, der i dag bruger `afkast_efter_pal`.
- **FR-002**: Ingen golden case ændres uden forløb.
- **FR-003**: Stress-forløbets størrelse ligger som antagelse med kilde og vises.
- **SC**: Golden case med håndregnet ratepension efter ét dårligt år.

## Afhængigheder og størrelse

- Uafhængig af 013b og 021. Mellemstor: kerneændring i flere funktioner, men mekanisk.
- Forudsætning for Monte Carlo (016).
