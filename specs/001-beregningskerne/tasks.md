---

description: "Opgaveliste for feature 001: beregningskerne og regelregister"
---

# Tasks: Beregningskerne og regelregister

**Input**: Design documents from `/specs/001-beregningskerne/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/kerne-api.md

**Tests**: Påkrævet. Forfatningens Princip IV (NON-NEGOTIABLE) kræver test først. I hver story
skrives testene først, og de SKAL fejle, før implementeringen starter.

**Organization**: Opgaverne er grupperet efter user story. Registret og sporingen ligger i
Foundational, fordi alle stories læser satser gennem dem.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Kan køres parallelt (forskellige filer, ingen afhængigheder)
- **[Story]**: US1–US7 fra spec.md
- Stier er relative til repo-roden (single project, src-layout)

---

## Phase 1: Setup

- [x] T001 Opret `pyproject.toml` (uv, pakke `pensionskerne`, Python ≥ 3.11, src-layout, pakkedata `register/*.toml`, dev: pytest, hypothesis) og kør `uv sync`
- [x] T002 [P] Opret pakkeskelet `src/pensionskerne/{__init__,model,validering,fremskrivning,jaevn}.py`, `src/pensionskerne/register/{__init__,opslag}.py` og `src/pensionskerne/regler/{skat,folkepension,ydelser,opsat,udbetalingsalder,ordninger}.py` med docstrings, der henviser til lovgrundlaget
- [x] T003 [P] Opret testmapper `tests/{golden,regler,egenskaber,kontrakt,register,differential,ydeevne}/` og `tests/conftest.py` med fælles fixtures (beregningsdato 2026-10-24, standardantagelser)
- [x] T004 [P] Tilføj `CLAUDE.md` i roden med kommandoer (`uv run pytest`), struktur og henvisning til forfatningen og `docs/domaene/`

---

## Phase 2: Foundational (blokerer alle stories)

### Tests først

- [x] T005 [P] Test i `tests/register/test_indlaesning.py`: alle poster i 2026 har id, værdi, enhed, kilde, status ∈ {verificeret, sekundaer, uverificeret} og reguleres; kommuner = 98 unikke + aliaser; ukendt satsår kaster fejl (FR-010, FR-011)
- [x] T006 [P] Test i `tests/register/test_opslag.py`: `Regelopslag` registrerer brugte id'er; streng tilstand kaster `UverificeretRegel` med id og kilde; satsregulering af poster med `reguleres = true` er `vaerdi × (1+s)^(k−satsaar)`, og procenter reguleres ikke (FR-012, FR-060)
- [x] T007 [P] Test i `tests/kontrakt/test_validering.py` for hver valideringsregel i data-model (fødselsdato < 1955, negative beløb, dublerede id'er, ratepension uden for 10–30 år, opsættelse > 10, ukendt kommune, gift uden partner) → `UgyldigtInput` med korrekt `felt` (FR-003)
- [x] T008 [P] Test i `tests/register/test_ingen_litteraler.py` (T-LINT): ingen numeriske litteraler i `src/pensionskerne/regler/` og `fremskrivning.py` ud over 0, 1, 12 og 100 (Princip II)

### Implementering

- [x] T009 Implementér input- og output-dataklasser og undtagelser i `src/pensionskerne/model.py` efter data-model.md
- [x] T010 Implementér indlæsning af registret og `Registerpost` i `src/pensionskerne/register/__init__.py` (tomllib, cache pr. satsår, satsregulering)
- [x] T011 Implementér `Regelopslag` i `src/pensionskerne/register/opslag.py` (sporing, flag, streng tilstand) (research T5)
- [x] T012 Skriv `src/pensionskerne/register/2026.toml` med alle poster fra domænegrundlagets afsnit 2 og research R1–R6, med kilde og status pr. post
- [x] T013 [P] Skriv `src/pensionskerne/register/kommuner_2026.toml` fra legacy-tabellen (`legacy/app.py` KOMMUNESKAT), status `sekundaer` (R7)
- [x] T014 Implementér inputvalidering i `src/pensionskerne/validering.py`
- [ ] T015 **T-REG** — Verificér mod primærkilde og opdatér status i `2026.toml`:
  - [x] Lov om social pension § 32 a (54 %) — bekræftet i VEJ nr. 10077/2025, tabel 15
  - [ ] PBL § 1 A (overgangsregler for udbetalingsalder)
  - [ ] PBL § 30, stk. 1 (40 %)
  - [x] PBL § 11 A — JV C.A.10.2.2.4.1
  - [ ] Tillægsprocent: "pr. fulde" eller "pr. påbegyndte" trin
  - [ ] Krydstjek kommuneskat mod Skatteministeriets regneark 2026 (svmn.dk)

  Dokumentér resultatet i `research.md`.

**Checkpoint**: `uv run pytest tests/register tests/kontrakt/test_validering.py` er grøn.

---

## Phase 3: User Story 1 — Nettoudbetaling år for år, enlig (P1) 🎯 MVP

**Goal**: Korrekt brutto, skat og netto pr. år for private ordninger, grundbeløb og ATP.

**Independent Test**: Golden cases G-02, G-02b, G-03, G-03b og FP-1, samt US1's acceptance
scenarios 1–7.

### Tests først

- [x] T016 [P] [US1] Golden-tests i `tests/golden/test_skat.py`: G-02, G-02b, G-03 (28.567,50), G-03b (loftnedslag > 0), top-topskat-loft 57,07 %, personfradragets værdi
- [x] T017 [P] [US1] Golden-tests i `tests/golden/test_folkepensionsalder.py`: FP-1 (1962→67, 1963→68, 1967→69, 1971→70)
- [x] T018 [P] [US1] Tests i `tests/regler/test_ordninger.py`:
  - FV med og uden lønvækst
  - § 11 A-rate (1.000.000/10 = 100.000 ved 0 % afkast; stigende rate ved positivt afkast) (A9)
  - livsvarig horisont (max(18, 90 − start))
  - ratepensionsloft 68.700 → overskud til livsvarig
  - aldersopsparingsloft 9.900/64.200 og 7-årsgrænsen
  - kapitalpension −40 %
  - aldersopsparing skattefri
- [x] T019 [P] [US1] Tests i `tests/regler/test_udbetalingsalder.py` (R2): før 2007 (inkl. overgang 1959–1960), 2007–2017 = fp−5, 2018+ = fp−3, ukendt = fp−3 + flag
- [x] T020 [P] [US1] Test i `tests/golden/test_us1_netto.py`: US1-scenarie 1. Ratepension 1 mio./10 år, 0 % afkast, Aarhus-skat: håndberegnet netto pr. år uden AM-bidrag (A1). Grundbeløb fra 68 år, ATP-fallback og flaget `skoennet_atp`
- [x] T021 [P] [US1] Property-tests i `tests/egenskaber/test_skat_invarianter.py`: K5 (Σ kilder = total), K7 (skat ≤ PI, netto ≥ 0), monoton skat i PI, marginalskat ≤ skatteloft + kirkeskat

### Implementering

- [x] T022 [P] [US1] Implementér `src/pensionskerne/regler/skat.py`: bund/kommune/kirke, personfradrag, progression med skatteloft og forholdsmæssig fordeling (FR-020–024)
- [x] T023 [P] [US1] Implementér `src/pensionskerne/regler/udbetalingsalder.py` (FR-043)
- [x] T024 [P] [US1] Implementér `src/pensionskerne/regler/ordninger.py`: FV, § 11 A, livsvarig, engangsbeløb, lofter (FR-040–042)
- [x] T025 [US1] Implementér fp-alder og grundbeløb i `src/pensionskerne/regler/folkepension.py` (FR-030, FR-031)
- [x] T026 [US1] Implementér `beregn` og år-for-år-løkken i `src/pensionskerne/fremskrivning.py` (trin 1, 5 og 6 i "Rækkefølge i et år"), ATP (FR-036), realværdi (FR-061) og offentlig API i `__init__.py`

**Checkpoint**: US1-tests er grønne. Kernen giver korrekt netto for en enlig uden
pensionstillæg.

---

## Phase 4: User Story 2 — Folkepensionens indtægtsregulering (P1)

**Goal**: Pensionstillæg, tillægsprocent, ældrecheck og mediecheck år for år.

**Independent Test**: G-40, G-41, G-42, G-43 og US2-scenarierne 1–6.

### Tests først

- [x] T027 [P] [US2] Golden-tests i `tests/golden/test_ydelser.py`: G-40, G-41, G-42, G-43; ældrecheck < 200 kr. → 0 (A6)
- [x] T028 [P] [US2] Grænsetests i `tests/regler/test_pensionstillaeg.py`: enlig (99.200 / bortfald ≈ 438.190), gift begge (198.800 / ≈ 533.825), gift ikke-pensionist (198.800 / ≈ 366.312); hver ± 1 kr.
- [x] T029 [P] [US2] Test i `tests/regler/test_indtaegtsgrundlag.py`: ATP, private S-udbetalinger og anden kapitalindkomst indgår; aldersopsparing og kapitalpension indgår ikke (A5)
- [x] T030 [P] [US2] Test i `tests/golden/test_us2_skat_af_checks.py`: ældrecheck og mediecheck indgår i PI og beskattes (A3, research T8)
- [x] T031 [P] [US2] Property-test i `tests/egenskaber/test_ydelser_invarianter.py`: pensionstillæg og tillægsprocent er monotont faldende i indtægtsgrundlaget; tillægsprocent ∈ [0, 100] i hele tal

### Implementering

- [x] T032 [US2] Implementér indtægtsgrundlag og pensionstillæg (enlig-reglen) i `src/pensionskerne/regler/folkepension.py` (FR-032)
- [x] T033 [P] [US2] Implementér tillægsprocent, ældrecheck og mediecheck i `src/pensionskerne/regler/ydelser.py` (FR-033–035)
- [x] T034 [US2] Integrér trin 2–4 i `src/pensionskerne/fremskrivning.py` (research T8-rækkefølge)

**Checkpoint**: US1 og US2 er grønne. MVP for enlige er komplet.

---

## Phase 5: User Story 3 — Regelregister: satsår, kilder og status (P1)

**Goal**: Registret kan inspiceres via API'et, streng tilstand virker ende-til-ende, og et
ukendt satsår afvises.

### Tests først

- [x] T035 [P] [US3] Kontrakttest i `tests/kontrakt/test_register_api.py`: `register.satsaar()`, `post()`, `poster()`, `kommuner()` (kontrakt)
- [x] T036 [P] [US3] Kontrakttest i `tests/kontrakt/test_streng.py`: `beregn(..., streng=True)` med en profil, der bruger en uverificeret post (fx livsvarig fallback-venteprocent) → `UverificeretRegel`; ukendt satsår → fejl og ingen fallback (US3-scenarie 2–3)
- [x] T037 [P] [US3] Test i `tests/register/test_daekning.py`: ≥ 90 % af 2026-posterne har status `verificeret` (SC-002)

### Implementering

- [x] T038 [US3] Eksponér `register`-API'et i `src/pensionskerne/__init__.py`, og før `streng` igennem `beregn`

---

## Phase 6: User Story 4 — Sporbarhed og advarsler (P2)

### Tests først

- [x] T039 [P] [US4] Kontrakttest i `tests/kontrakt/test_sporing.py`: K6 (hver række har ikke-tom sporing med gyldige id'er); `sporing_samlet` dækker alle rækker
- [x] T040 [P] [US4] Tests i `tests/golden/test_advarsler.py`: `RATEPENSION_LOFT`, `MELLEMSKAT_INTERVAL` (ét pr. sammenhængende interval), `UDBETALING_FOER_LOVLIG_ALDER`, `ATP_SKOENNET`; flag pr. år for forenkling og uverificeret

### Implementering

- [x] T041 [US4] Implementér opsamling af advarsler og intervalsammenlægning i `src/pensionskerne/fremskrivning.py` (FR-072)
- [x] T042 [US4] Sikr, at alle regelmoduler kun læser satser via `Regelopslag`, og at flag føres til `Aarsresultat.flag` (FR-071)

---

## Phase 7: User Story 5 — Opsat folkepension (P2)

### Tests først

- [x] T043 [P] [US5] Golden-tests i `tests/golden/test_opsat.py`: VT-1 (3 år fra 67 → × 1,1875 fra 70, ATP uændret fra 67); hele 67-tabellen 1–10 år; anden opsættelsesalder → fallback + `VENTEPROCENT_USIKKER`; advarslerne `750_TIMER` og `OPSAT_ANDRE_FORMER`

### Implementering

- [x] T044 [US5] Implementér `src/pensionskerne/regler/opsat.py`, og integrér ventefaktoren på grundbeløb og pensionstillæg i `fremskrivning.py` (FR-050, FR-051)

---

## Phase 8: User Story 6 — Gift/samlevende (P2)

### Tests først

- [x] T045 [P] [US6] Golden-tests i `tests/golden/test_partner.py`:
  - PT-1
  - Skift fra 32 % til 16 % i det kalenderår, partneren når fp-alder
  - Partner ikke pensionist med 100.000 kr. pension → 46.000 kr. i indtægtsgrundlaget (R1, A4)
  - AM-pligtig arbejdsindkomst ignoreres
  - Manglende år → seneste kendte + flag
  - Tillægsprocent for gifte (G-41) med samlet grundlag

### Implementering

- [x] T046 [US6] Implementér valg af partnerstatus pr. kalenderår, de tre tillægsregler og partnerandelen i `src/pensionskerne/regler/folkepension.py`, og integrér i `fremskrivning.py`

---

## Phase 9: User Story 7 — Jævn månedlig udbetaling (P3)

### Tests først

- [x] T047 [P] [US7] Tests i `tests/golden/test_jaevn.py`:
  - Nutidsværdi-ligevægt (jævn = normal + buffer)
  - Konstant realniveau
  - Niveauet stiger, når et senere engangsbeløb lander, og falder aldrig
  - Fravalgt engangsbeløb holdes uden for
  - Advarslen `BUFFER_YDELSE_FORENKLING` (FR-081)

### Implementering

- [x] T048 [US7] Implementér `src/pensionskerne/jaevn.py` (FR-080, FR-081), og knyt det til `Fremskrivning.jaevn`

---

## Phase 10: Polish og tværgående

- [x] T049 [P] Differentialtest i `tests/differential/test_mod_legacy.py` efter research T7:
  - Lag 1: regelfunktioner ±0,01
  - Lag 2: afkast 0, forskel = A1 + A3 ± 1 kr.
  - Lag 3: 10 profiler med en forventningsfil, hvor hver forskel har et A-nummer (SC-003)
  - Skip, hvis `legacy/` mangler
- [x] T050 [P] Ydeevnetest i `tests/ydeevne/test_ydeevne.py`: 40 år og 10 ordninger < 100 ms (SC-005)
- [x] T051 [P] Kontrakttest K1/K2 i `tests/kontrakt/test_determinisme.py`: identisk output ved gentagne kald; ingen brug af `date.today` (monkeypatch kaster)
- [x] T052 Opdatér README.md (status, kør tests) og `docs/domaene/beregningskerne.md` med resultatet af T-REG
- [x] T053 Kør quickstart.md's eksempel som test i `tests/kontrakt/test_quickstart.py`

---

## Dependencies & Execution Order

- **Setup (T001–T004)** → **Foundational (T005–T015)** → user stories
- **US1** → **US2** (bygger på løkken og skatten) → **US3–US7**. US3, US4 og US5 kan køre
  parallelt efter US2. US6 kræver US2. US7 kræver US1 (engangsbeløb) og helst US2.
- **Polish** efter de stories, testene dækker. T049 lag 1 kan starte allerede efter US2.
- I hver story skrives testene først og skal fejle. Derefter implementeres
  regelmodulerne ([P]) og til sidst integrationen i `fremskrivning.py`.

## Parallel Example: User Story 1

```text
Tests:          T016, T017, T018, T019, T020, T021  (alle [P])
Regelmoduler:   T022, T023, T024                    (alle [P])
Integration:    T025 → T026
```

## Implementation Strategy

1. **MVP** = Setup + Foundational + US1 + US2: korrekt netto og ydelser for enlige. Stop her,
   og kør differentialtestens lag 1–2 for at validere mod legacy.
2. **Inkrement 2**: US3 + US4 (revisionsklar: streng tilstand og sporing).
3. **Inkrement 3**: US5 + US6 (beslutningsparametre: opsættelse og par).
4. **Inkrement 4**: US7 + Polish.

## Notes

- Commit efter hver opgave eller logisk gruppe.
- En ændring af en golden case kræver en begrundelse i commit-beskeden (Princip IV).
- Et tal i `regler/` uden for registret får T008 til at fejle. Det er tilsigtet.
