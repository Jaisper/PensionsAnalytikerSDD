# Implementation Plan: 018 Usikkerhed om afkast og inflation

**Branch**: `018-usikkerhed` | **Spec**: [spec.md](spec.md) | **Dato**: 2026-10-26

## Tekniske beslutninger

- **Indgangslaget** (`app.py`):
  - `AFKAST_SPAEND = 0.01` og `INFLATION_SPAEND = 0.005` (antagelser).
  - `scenarier(guide_json)` giver de seks scenarier: nøgle, titel, afkast og inflation, udledt af
    borgerens eget valg og sat til mindst 0.
  - `scenarie(guide_json, idag, afkast, inflation)` kalder `beregn` med de ændrede antagelser og
    giver hovedtallet for dig og, for et par, partner og samlet.
  - Kernen ændres ikke.
- **Worker**: to nye operationer, `scenarier` og `scenarie`.
- **Brugerflade**:
  - Når resultatet er vist, henter `app.js` scenarierne og regner dem ét ad gangen.
  - En tæller afbryder løkken, hvis svarene ændres. Højst ét scenarie står derfor foran den næste
    beregning i workerens kø.
  - `#hovedtal-spaend` under hovedtallet viser spændet.
  - `<details id="usikkerhed">` i "Prøv andre forudsætninger" viser tabellen.
  - Spænd og tabel tegnes igen, når fanen skiftes.

## Constitution check

- Princip I: visningen omformaterer kun. Scenarierne regnes af kernen.
- Princip III/V: spændene er antagelser og vises med deres størrelse.
- Princip IV: test først (T001–T002).
- Princip VII/XI: alt i browseren.
