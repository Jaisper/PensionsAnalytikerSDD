# Implementation Plan: Kapitalpensionens muligheder og en realistisk buffer

**Branch**: `009-kapitalpension` | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Design

### D1 Registret (2026.toml)

Nye poster med kilde og status:
- `ordning.kapitalpension.seneste_aar_efter_udbetalingsalder` = 20 (PBL § 25, stk. 1, nr. 7, og
  § 12, stk. 1, nr. 3)
- `pal.sats` = 0,153 (PAL § 2)
- `skat.kapitalindkomst.bundfradrag` = 55.000 (PSL § 7, stk. 1; reguleres)
- `skat.skatteloft.kapitalindkomst` = 0,42 (PSL § 19, stk. 2)

### D2 Model

- `Ordning.afgift_betalt: bool = False`
- `Ordning.udbetalingsform: Literal["engangs", "portioner", "ratepension", "livsvarig"] =
  "engangs"`. Den bruges kun for kapitalpension.
- `Aarsresultat.kapitalindkomst` og `skat_kapitalindkomst`, begge nominelle.
- `Antagelser.buffer_kapitalskat` fjernes og erstattes af lovens skat (FR-006).

### D3 Planer (`fremskrivning.py` og `regler/ordninger.py`)

- **Kapitalpension**:
  - `engangs`: som i dag. Afgiften er 0, hvis den er betalt.
  - `portioner`: `rateplan(saldo, N, afkast)` giver bruttoportioner, og hver nettoportion bliver
    et `Engangsbeloeb` i sit år (buffer eller direkte).
  - `ratepension` og `livsvarig`: planen bygges, som om typen var ratepension eller livsvarig
    (rater eller ydelse som personlig indkomst). Kilden får typen "ratepension" eller "livsvarig".
- **Validering**:
  - Portioner: N ≥ 2, og start + N − 1 ≤ tidligste + 20.
  - Ratepension: ratepensionens regler.
  - Omlægning med betalt afgift afvises.
  - Udbetalingsform på andre typer end kapitalpension afvises.

### D4 Bufferen med lovens skat (`jaevn.py` og `fremskrivning.py`)

- `beregn_jaevn(raekker, engangs, rente_brutto, inflation, aar0)`. Normal pr. år er netto −
  skat_kapitalindkomst, så skatten af afkastet betales af bufferen. Bufferen forrentes med
  rente_brutto = afkast_efter_pal / (1 − pal.sats).
- Den år-for-år-beregning, der i dag ligger i `beregn`, flyttes til `_aar_for_aar(kapitalindkomst,
  formue)`.
- **Fastpunkt**:
  1. Start med KI = 0 og F = profilens formue.
  2. Regn årene og den jævne udbetaling.
  3. KI_t = max(0, buffer_rest_t × r/(1+r)), og F_t = profilens formue + max(0,
     buffer_rest_{t−1}).
  4. Stop, når KI ændrer sig mindre end 1 kr. og ældrecheckens formuetest er uændret, eller efter
     8 iterationer. Gives der op, kommer advarslen `BUFFER_IKKE_KONVERGERET`.
- **Skat**: `beregn_skat(pi, ki, ...)`:
  - Bund-, kommune- og kirkeskat af PI + KI, og personfradrag af PI + KI.
  - Progressivt grundlag = PI + max(0, KI − bundfradrag).
  - For den del af hvert bånd, der skyldes KI, bruges skatteloftet for kapitalindkomst (42 %).
  - `skat_kapitalindkomst` = skat(PI, KI) − skat(PI, 0), altså marginalt.
- **Pensionstillæg**: Indtægtsgrundlaget får KI_t oven i profilens kapitalindkomst. **Ældrecheck**:
  F_t.
- **Advarsler**:
  - `BUFFER_YDELSE_FORENKLING` erstattes af `BUFFER_SOM_OPSPARING` (forudsætning ≈): bufferen er
    regnet som opsparing i bank/obligationer.
  - `PORTIONER_KRAEVER_AFTALE` og `OMLAEGNING_KRAEVER_OVERFOERSEL` (≈).

### D5 Visning og indgang

- `oversaet.py`: `afgift_betalt`, `udbetalingsform` og `udbetaling_aar` for kapitalpension.
- `graenser`: pr. kapitalpension `seneste_portion` (tidligste + 20) og om omlægning er tilladt.
- `visning`:
  - Engangsbeløb pr. portion (UI'et grupperer pr. ordning).
  - Kort for kapitalindkomst? Nej. Skatten af bufferen vises i tabellen og hører under bufferen.
  - Tabellen får kolonnen "Skat af buffer".
- `omsaet.py` (PDF): `afgift_betalt` sættes, og typen bevares.

### D6 Optimeringen

Dimensionen ("form", id, (form, n)) bruges for kapitalpensioner i søgerummet. Værdierne er
engangs, portioner 2…N_maks, ratepension 10…30 og livsvarig. Omlægning afprøves kun uden betalt
afgift. `Plan.form` og `anvend` sætter udbetalingsform og antal år. `app.optimer` giver
ændringen `felt = "form"`.

### D7 Brugerflade

- **Kapitalpensionens kort**:
  - Rullelisten "Hvordan vil du have den udbetalt?" med fire valg, plus "over N år", når valget
    kræver det.
  - Afkrydsningen "Afgiften er allerede betalt".
  - Hjælpetekster under felterne.
- **Tidslinjen**: Portioner og ratepension vises som bjælke med greb (varighed). Grænserne er
  2…seneste portion for portioner og 10…30 for ratepension. Livrente vises som bjælke til
  slutningen, og engangsbeløb som punkt.
- **Grafens markører og listen** grupperer portioner: "Kapitalpension: 8 portioner, 65–72 år, i
  alt ca. X kr. → buffer".
- **Forslagstekst** for felt "form".

## Tests (test først)

- `tests/regler/test_skat_kapitalindkomst.py` (golden, regnet i hånden fra PSL):
  - KI under bundfradraget
  - KI over bundfradraget med skatteloft
  - personfradrag af PI + KI
- `tests/golden/test_kapitalpension_former.py`:
  - portioner (§ 11 A-formlen, 40 % pr. portion, betalt afgift = 0)
  - 20-årsfristen
  - omlægning som rate og livrente (personlig indkomst, indtægtsgrundlag)
  - omlægning afvist ved betalt afgift
- `tests/golden/test_buffer_realistisk.py`:
  - KI = buffer × r/(1+r)
  - pensionstillæg lavere med buffer
  - ældrecheck væk over formuegrænsen
  - konvergens på 3 eller færre iterationer
  - portioner giver mindre formue end engangsbeløb
- Optimering: formdimensionen, ingen omlægning ved betalt afgift, og grænser.
- App og PDF: `oversaet` og `omsaet` med de nye felter.
- Browser: kortets felter, tidslinjens bjælker for portioner og rate, forslag med form,
  Pyodide = CPython, axe og 360 px.

## Constitution Check

| # | Princip | Gate | Status |
|---|---|---|---|
| I | Deterministisk beregning | Fastpunkt med fast loft og deterministisk stop | [x] |
| II | Regelregister | 4 nye poster med kilde. Ingen tal i `regler/` | [x] |
| III | Lovgivningen er facit | Hver regel er verificeret i lovtekst eller Skatteministeriets satser (research). Én er sekundær (2013-omlægning) | [x] |
| IV | Test først | Golden cases regnet i hånden før kode | [x] |
| V | Sporbarhed | Nye advarsler, sporing af nye poster og kolonnen "Skat af buffer" | [x] |
| VI | Isoleret kerne | Ren funktion. Iterationen er intern | [x] |
| IX | Simpelhed | Ingen nye afhængigheder. Forenklinger dokumenteret (aktieindkomst, par-bundfradrag) | [x] |
| X | Brugeroplevelse | Ét valg pr. kapitalpension med forklaring. Optimeringen viser valget | [x] |
