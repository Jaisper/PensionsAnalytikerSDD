# Implementation Plan: Tidslinje og datapanel

**Branch**: `004-tidslinje` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

- **Backend**: `byg_visning` får en ny funktion, `graenser(profil, satsaar)`, som returnerer
  kernens tidligste lovlige alder pr. ordning, ratepensionens periodegrænser og maksimum for
  opsættelse fra registret. `/api/beregn` lægger dem i svaret under `graenser`.
- **Frontend**: Resultatsiden omorganiseres. Guidens formular flyttes ind i datapanelet
  (samme DOM, ét datasæt). Tidslinjen tegnes ud fra brugerens svar og placeres via Chart.js'
  `scales.x`.

## Constitution Check

| # | Princip | Status |
|---|---|---|
| I | Tidslinjen viser kun brugerens valg. Alle tal kommer fra kernen | ✅ |
| II | Grænser (tidligste alder, periode, opsættelse) kommer fra kernen og registret via API | ✅ |
| IV | Test af `graenser` før implementering. Browsergennemgang | ✅ |
| VII | Ingen ændring | ✅ |
| X | Legacy-mønstret med skydere i stedet for kun træk. Tastaturbetjent, mobil-stabling | ✅ |
| XI | Ingen AI | ✅ |

## Structure

```text
src/pensionsoverblik/visning.py   # + graenser()
src/pensionsoverblik/api.py       # svaret får "graenser"
src/pensionsoverblik/static/*     # datapanel, graf-panel, tidslinje
tests/app/test_graenser.py
```
