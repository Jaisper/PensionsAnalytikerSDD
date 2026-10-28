# Feature Specification: 007b Den bedste plan med det samme

**Feature Branch**: `007b-auto-optimering` | **Oprettet**: 2026-10-28 | **Status**: Implementeret 2026-10-28
**Input**: Brugerønske: "uanset om man har angivet fra hvilken alder man vil pensioneres skal der med det
samme udregnes et optimalt forløb for udbet strømmen. Så hvis ikke noget angivet fra
folkepensionstidspunkt."

## Afklaringer (besluttet af brugeren 2026-10-28)

- Den bedste plan bliver hovedtallet med det samme. Borgerens egen plan står under hovedtallet med
  sit beløb, og borgeren kan skifte mellem dem.
- Pensionsalderen er stopalderen (017), ellers folkepensionsalderen. Ingen ordning starter før
  pensionsalderen i den bedste plan, og målet (det faste beløb hele perioden) regnes fra den.

## Krav

- **FR-001**: `optimering.pensionsalder(profil, fp_alder)`: stopalderen med løn, ellers
  folkepensionsalderen.
- **FR-002**: Søgerummet for startalder er fra max(tidligste lovlige alder, pensionsalderen) til
  folkepensionsalderen plus maksimal opsættelse. En ordning, der allerede udbetaler, flyttes ikke.
- **FR-003**: Målet og værnene regnes over `maalvindue`: fra pensionsalderen, hvis den er senere end
  udjævningens første år.
- **FR-004**: Efter første resultat (guiden og en gemt fil) finder siden den
  bedste plan for dig og en fuld partner, anvender den og viser "Det er den bedste plan, vi har fundet.
  Med din egen plan får du X kr. om måneden", ændringerne og en knap til at skifte plan. Ændrer
  borgeren planen bagefter, forsvinder linjen; "Find bedste plan" virker som før. "Opdater
  beregningen" i datapanelet kører den ikke: der har borgeren selv valgt, og valget må ikke overskrives.
- **FR-005**: Er planen allerede den bedste, står der det.

## Succeskriterier

- **SC-001**: Den bedste plans startaldre er ≥ pensionsalderen (kernetest og browsertest).
- **SC-002**: Hovedtallet med den bedste plan er mindst lige så højt som med borgerens egen (browsertest).
- **SC-003**: Skift til egen plan giver præcis borgerens svar og beløb (browsertest).
