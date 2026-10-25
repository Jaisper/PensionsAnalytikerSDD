# Implementation Plan: Find bedste plan og engangsbeløb som buffer

**Branch**: `007-optimering` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

Et nyt kernemodul, `pensionskerne/optimering.py`, porterer legacy-sekventeringen til den nye
kerne. Målet er det samme, værnene er tilpasset kernens jævne model, og søgningen er den samme
(udtømmende eller multi-start koordinatsøgning). Indgangen får `app.optimer`, workeren får
fremdrift, og resultatsiden får "Find bedste plan" med forslag, spøgelsesbjælker og "Anvend".
Guiden får "Brug som buffer" pr. engangsbeløb (kernen understøtter det allerede).

## Design

### D1 `pensionskerne/optimering.py`

```python
@dataclass(frozen=True)
class Plan:
    starter: dict[str, int]          # ordnings-id → startalder
    varighed: dict[str, int]         # ratepension-id → år
    opsaettelse: int

@dataclass(frozen=True)
class Optimering:
    udgangspunkt: Plan
    udgangspunkt_maaned: float       # hovedtal (kr./md., dagens kroner)
    bedste: Plan | None              # None = ingen bedre gennemførlig plan
    bedste_maaned: float | None
    evalueret: int
    mulige: int
    udtoemmende: bool

def optimer(profil, antagelser, satsaar, beregningsdato, *, maks_evalueringer=1500,
            fremdrift: Callable[[int, int], None] | None = None) -> Optimering
```

- **Mål**: `maaned(res)` = det jævne niveau efter det sidste spring, gange realfaktor og
  divideret med 12. Det er samme regel som visningens hovedtal, og testen sammenligner med
  `byg_visning`. Uden jævn udbetaling bruges det første hele folkepensionsår, som i
  visningen.
- **Værn** (FR-003) regnes på årene fra udgangspunktets første udbetaling til 90:
  - rå = netto_real plus direkte engangsbeløb (real)
  - buffer_real = buffer_rest × realfaktor
  - Mangler et år i kandidaten (senere start), tæller det som 0.
- **Rangering**: månedsbeløb, derefter samlet real nettoudbetaling (uafgjort), og til sidst
  vektoren (deterministisk).
- `UgyldigtInput` fra `beregn` betyder, at kandidaten ikke er gennemførlig.
- **Grænser**:
  - tidligste alder via `tidligste_udbetalingsalder` eller den oplyste alder (samme som
    `graenser`)
  - øvre grænse = folkepensionsalder + `opsat.maks_aar`
  - ratepension `min_aar` … `maks_aar_efter_udbetalingsalder`
- Konstanterne for værnene (0,70, 0,97, 0,85, 1 måned) er modelvalg fra legacy og ikke
  lovsatser. De står i modulet med begrundelse, ligesom jævn-modellens parametre.

### D2 Indgang og worker

- `app.optimer(guide_json, idag, fremdrift=None)` returnerer `{ok, data: {forbedret, foer,
  efter, aendringer[], plan, evalueret, mulige, udtoemmende}}`. Månedsbeløbene afrundes til
  100 kr. som hovedtallet.
- Hver ændring er `{id, titel, felt: "start" | "varighed" | "opsaettelse", fra, til}`.
- Workeren videresender fremdrift som `{id, fremdrift: andel}`. `kald` får en valgfri
  `vedFremdrift`.

### D3 Brugerflade

- Knappen "Find bedste plan" står over tidslinjen i panelet "Udbetaling over tid".
- Forslagsboksen (`role="status"`) viser:
  - forskellen og de to beløb
  - en liste over ændringer
  - "Anvend" og "Behold min plan"
  - eventuelt "afprøvet X af Y"
- Spøgelsesbjælker: en stiplet kontur på forslagets placering i hver række, der ændres.
- "Anvend" skriver planen ind i `aktuelleSvar` og regner igen. Bagefter skal hovedtallet
  være lig forslagets beløb.
- En ny ændring i tidslinjen eller panelet fjerner forslaget. Et svar fra en gammel plan
  ignoreres (planens nøgle sammenlignes).

### D4 Buffer-valg

- Guidens kort for aldersopsparing og kapitalpension får en afkrydsning, "Brug som buffer",
  med hjælpetekst. `guideSvar` sender `i_buffer`.
- Tidslinjen viser et udfyldt punkt (buffer) eller en ring (direkte) og teksten "til buffer"
  eller "udbetales direkte".

## Tests (test først)

- `tests/optimering/test_optimering.py`:
  - forslaget er mindst lige så godt som udgangspunktet
  - grænserne overholdes, også for hver evalueret kandidat (via en spion)
  - et engangsbeløb, der ikke er buffer, flyttes ikke
  - deterministisk
  - udtømmende ved et lille søgerum, og budgettet overholdes
  - "ingen bedre", når udgangspunktet er optimalt
  - et kendt hul forkastes (værn)
  - `maaned` er lig visningens hovedtal
- Egenskabstest (hypothesis, få eksempler): for tilfældige gyldige profiler er bedste ≥
  udgangspunkt, og grænserne overholdes.
- `tests/app/test_app.py`: optimer-format. Når planen anvendes, giver `beregn` et hovedtal lig
  `efter`.
- `tests/browser/test_optimering.py`:
  - knap, fremdrift og forslag, og "Anvend" giver hovedtal lig `efter`
  - "Behold" ændrer intet
  - Pyodide giver samme plan som CPython
  - buffer-afkrydsningen virker
  - axe og 360 px

## Constitution Check

| # | Princip | Gate | Status |
|---|---|---|---|
| I | Deterministisk beregning | Søgning over `beregn`. Ingen tilfældighed og ingen AI | [x] |
| II | Regelregister | Søgerummets grænser fra registret. Værnenes konstanter er modelvalg (dokumenteret, ikke satser) | [x] |
| III | Lovgivningen er facit | Ingen nye regler. Hver kandidat er en lovlig beregning | [x] |
| IV | Test først | Kernetests og browsertests før kode | [x] |
| V | Sporbarhed | Forslaget oplyser ændringer, antal afprøvede og om søgningen var udtømmende | [x] |
| VI | Isoleret kerne | Ren funktion, dato som argument, fremdrift som valgfrit callback | [x] |
| VII | Persondata | Alt i browseren | [x] |
| IX | Simpelhed | Ingen top 5 eller følsomhed og ingen kapital_rate. Ingen nye afhængigheder | [x] |
| X | Brugeroplevelse | Ét forslag med "Anvend". Fremdrift. Ingen frysning | [x] |
| XI | Ingen persondata til AI | Uændret | [x] |
