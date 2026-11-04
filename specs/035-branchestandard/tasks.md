# Tasks: 035 Branchestandard

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Research**: [research.md](research.md)

Test først (Princip IV): hver opgave skriver testen, før koden.

## Fase 1: Trin 1–2 i kernen

- [x] T001 Rådets forudsætninger for 1. halvår 2027 i `register/2026.toml` (`raadet.*`) med kilde,
      udgivelsesdato og status, og fraktilerne fra henstillingen (`branchestandard.fraktiler`).
      Test: `tests/register/test_raadet.py` (10 klasser, symmetrisk korrelation, perioder, inflation).
- [x] T002 Golden case for bilag 2, "Fraktilafkast Udledning årlige": M, V, 5 %-/95 %-depot og de
      tre stier for t = 1…19 (SC-002). `tests/golden/test_branchestandard_bilag2.py`.
- [x] T003 `pensionskerne/prognose.py`: `trin1`, `fraktil` og `trin2`, inkl. reglen for, når
      depotet løber tør (R1).
- [x] T004 `mu_sigma` og `periode_forudsaetninger` (år 1–5, 6–10 og 11+, investeringsomkostninger
      for år 1–10) med test af blandingsporteføljen mod håndregning.

## Fase 2: Trin 3 og tre forløb

- [x] T005 `Ordning.afkast_forloeb` og `gebyr_pr_aar` i fremskrivningen. `egne` er uændret (SC-001).
- [x] T006 `Antagelser.beregningsgrundlag` og `Fremskrivning.prognose` (høj, forventet, lav).
- [ ] T007 Standardprofilen ✅, blandingen ✅ og forenklingerne ✅ i registret. Åbent: gebyrets størrelse
      (kræver en kilde) og Finanstilsynets levetidsbenchmark (data skal hentes). Forenklingerne i
      `forenklinger.toml`.
- [ ] T008 Golden cases for rate, livsvarig og aldersopsparing (SC-003).

## Fase 3: PDF-import og kalibrering

- [ ] T009 FR-015: selskabets prognose og investeringsform i importen og den syntetiske rapport.
- [ ] T010 `kalibrering.py` med rundturstest (SC-007) og gennemsnitsrente som fladt afkast (FR-014).

## Fase 4: Brugerflade

- [ ] T011 Indgangslaget: `beregningsgrundlag`, gamle input → `egne` (US1-3), aktieandel pr. ordning.
- [ ] T012 Skifter, tre niveauer i hovedtal og graf (FR-007, FR-010), porteføljeskøn (US3) og
      sammenligning (US4).
- [ ] T013 Forklaringer (FR-008) og advarsler.

## Fase 5: Afslutning

- [ ] T014 Browsertests, Pyodide = CPython (SC-006), ydelse under 2 s (SC-005).
- [ ] T015 016 markeres som erstattet. Hele suiten grøn.
