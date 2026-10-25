# Implementation Plan: Udjævning uden lån

**Branch**: `010-ingen-laan` | **Spec**: [spec.md](spec.md)

## Design

`jaevn.beregn_jaevn` skrives om til en segmentalgoritme med likviditetsbegrænsning (den klassiske
forbrugsudjævning uden lån). Lad:
- I_t = årets indbetaling til bufferen (normal_t + engangsbeløb_t)
- r = bufferens rente
- g = 1 + inflation

Et segment starter i år i med buffer B. Niveauet c (stigende med g, altså konstant i dagens
kroner) er:

    c = min over k ≥ i af  (B + Σ_{t=i..k} I_t / (1+r)^(t−i)) / Σ_{t=i..k} g^(t−i) / (1+r)^(t−i)

Lad k* være det sidste k, der giver minimum. Segmentet varer fra i til k*. Bufferen er 0 efter
k*, og næste segment starter i k*+1 med B = 0.

Bufferen opdateres som før: (B + I_t − niveau_t) × (1+r), og den er ≥ 0 per konstruktion. Det
sidste segment ender med bufferen = 0.

Kompleksitet O(n²) med n ≤ cirka 35 år. Det er ubetydeligt.

## Konsekvenser

- `JaevnUdbetaling.niveau_foerste_aar` og `niveau_real` er det første segments niveau, altså det
  laveste.
- Hovedtallet (visningen) er min, og `senere` er niveauet efter sidste spring. Det er uændret i
  semantik.
- Optimeringens `fast_niveau` er det første segment. Bufferværnene bliver trivielle, fordi der
  ikke er negative buffere, men de fanger stadig huller via dybde og varighed.
- `JAEVN_FORUDSAETTER_SENERE_UDBETALINGER` fjernes fra kerne og katalog.

## Tests

- `tests/golden/test_jaevn_uden_laan.py`:
  - Regnet i hånden: [0, 100, 200] giver 0, 100, 200. [300, 0, 0] giver 100, 100, 100 (r = 0, g = 1).
  - Med rente og vækst.
  - Engangsbeløb i år 2.
- Egenskab (hypothesis): For tilfældige indbetalinger er bufferen ≥ 0, niveauet er ikke-faldende,
  og bufferen ender i 0.
- Eksisterende golden cases kan ændre sig, hvis de lånte. Hver ændring begrundes.
- Browser: buffergrafen er aldrig under 0 (data), og titel og forklaring er på plads.

## Constitution Check

- **I og VI:** Det er ren og deterministisk.
- **III:** Udjævning er en præsentationsmodel, ikke lov. Det fremgår af modulets docstring.
- **V:** Hovedtallets tekst forklarer springene.
- **X:** Grafen er ærlig og forklaret.
