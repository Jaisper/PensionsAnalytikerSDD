# Implementation Plan: 019 Levetid som scenarie

**Branch**: `019-levetid` | **Spec**: [spec.md](spec.md) | **Dato**: 2026-10-26

## Tekniske beslutninger

- **Kerne**: `Antagelser.plan_slut_alder: int | None = None`.
  - Tabellens sidste år er `plan_slut_alder` eller, uden den, `livsvarig_horisont_alder`.
    Ratepensionens sidste rate og folkepensionsstarten kan forlænge tabellen som i dag.
  - Livrentens ydelse beregnes stadig med `livsvarig_horisont_alder`.
  - Validering: planen skal slutte efter i dag.
- **Indgangslaget**: `scenarier` får to levetidsscenarier (`levetid_85`, `levetid_95`) med feltet
  `plan_slut_alder`. `scenarie(..., plan_slut_alder=None)` sender det videre som antagelse.
  - For planen til 95 år giver svaret også `efter_plan`: indkomsten efter skat pr. måned i dagens
    kroner i året efter den normale plans slutning, for dig og partneren.
  - `efter_plan` beregnes af kernen. Indgangslaget slår kun rækken op og deler med 12.
- **Brugerflade**:
  - Tabellen får kolonnen "Planen rækker til" og to rækker mere.
  - Sætningen om indkomsten efter planen vises under tabellen (ikke under "Samlet").
  - Spændet under hovedtallet gælder fortsat kun afkast og inflation. Levetid er et andet
    spørgsmål, og et samlet spænd ville blande dem.
