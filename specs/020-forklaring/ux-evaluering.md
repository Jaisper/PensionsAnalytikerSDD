# UX-evaluering: Forklaring i tre niveauer (020a)

**Dato**: 2026-10-27 · **Metode**: browsertests (`tests/browser/test_forklaring.py`,
`test_forenklinger.py`), headless Chrome.

| Måling | Resultat | Krav |
|---|---|---|
| "Hvordan fremkommer tallet?" på tre niveauer, med de største kilder på niveau 1 | ja (test) | US1 |
| Niveauet vælges ét sted og huskes i browseren. Det gælder også "Dit år" | ja (test) | FR-008 |
| "Dit år" åbnes fra grafen og fra år-for-år-tabellen | ja (test) | US2 |
| Regnestykket for et år summerer til årets netto ("I alt") | ja (test og golden) | FR-004, SC-002 |
| Skat pr. type afstemmer med årets skat for enlig, opsparing, løn og par | ja (golden) | SC-002 |
| Kataloget dækker alle inventarpunkter, registerposter og advarsler på tre niveauer | ja (test) | FR-006, SC-001 |
| Niveau 1 har LIX under 35 | ja (test, højeste er ca. 33) | SC-005 |
| En forklaring åbner uden kald til motoren | under 300 ms (test) | SC-007 |
| Samme katalog og tal i Pyodide og CPython | ja (test) | SC-006 |
| axe (begge forklaringer åbne, niveau 3) og 360 px | 0 fejl, ingen scroll | FR-010 |
| Forenklingerne vises med begrundelse. Dem, der påvirker beregningen, står først | ja (test) | FR-005 |

### 020b–d

| Måling | Resultat | Krav |
|---|---|---|
| Skifter mellem dagens og årets kroner i graf, tabel, opsparingsgraf, formue og kort. Hovedtallet er altid i dagens kroner. Valget huskes | ja (test) | US3 |
| "Sådan læser du …" ved hovedtal, graf, tidslinje, opsparingsgraf, faner, ikoner, usikkerhed og beløb. Grafens nævner kun de viste serier | ja (test) | US3, AS1 |
| Kortenes "i" og ordlisten følger det valgte niveau | ja (test) | FR-002, FR-009 |
| "Sådan har vi fundet forslaget" med søgningens omfang og forbehold | ja (test) | US5 |
| Metodesiden uden data: alle emner, alle forenklinger, alle satser med kilde og status | ja (test) | US4 |
| Eksport som JSON (hele beregningen) og CSV (år for år) uden CPR, navne eller aftalenumre | ja (test) | US6 |
| Udskrift åbner alle fold-ud'er og skjuler knapper | ja (test) | US4 |
| Rulbare tabeller kan nås med tastaturet; link i bunden har nok kontrast | rettet (axe) | FR-010 |

## Heuristik (kort)

- **Svaret først:** Hovedtallet står uændret. Forklaringen er en fold-ud lige under det.
- **Progressiv afsløring:** Niveau 1 er tre til fem korte sætninger. Regnestykket og lovhenvisningerne
  kommer kun, når borgeren beder om dem.
- **Ærlighed:** Niveau 2 siger, at skatten pr. indkomst er en fordeling, og at beløbene i
  regnestykket er i årets kroner.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| F1 | SC-004 (brugertest med tre personer pr. målgruppe) er ikke udført. Det er et manuelt krav | 2 |
| F2 | ~~Kortene, tidslinjen og fanerne har endnu ikke tre niveauer~~ Løst i 020b | – |
| F3 | Under "Samlet" forklares hovedtallet kun med husstandsemnet, ikke med parrets egne tal | 1 |
