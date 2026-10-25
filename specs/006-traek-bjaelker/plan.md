# Implementation Plan: Bjælker, der trækkes

**Branch**: `006-traek-bjaelker` | **Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

Tidslinjens skydere fjernes. Bjælken eller punktet bliver selv kontrollen. Det er ren
frontend: `app.js` og `app.css`. Kernen og API'et er uændrede, fordi grænserne allerede kommer
fra `graenser` (004).

## Design

### Rækkens opbygning

```
.tl-raekke[data-id]
  .tl-hoved            titel · "65–74 år"
  .tl-spor             32 px højt; samme akse som grafen (placerBjaelker)
    .tl-bjaelke        role=slider (start), tabindex=0, pointer-træk
      .tl-greb         kun ratepension: role=slider (varighed), højre ende
  .tl-trin[hidden]     vises, når rækken er valgt: "Start ‹ 65 år ›", "Varighed ‹ 10 år ›"
```

### Model

- Hver kontrol beskrives af `{ felt, min, maks, vaerdi, tekst }`:
  - ordningens start: `udbetaling_start_alder`, fra tidligste lovlige alder til akseslut
  - ratepensionens varighed: `udbetaling_aar`, 10–30
  - folkepensionens opsættelse: 0 til maksimum
- Én funktion, `saetVaerdi(kontrol, ny)`, klemmer værdien inden for grænserne og opdaterer
  `tilstand.aktuelleSvar`, ARIA og tekst. Derefter kaldes `synkroniserFormular()`,
  `placerBjaelker()` og `genberegn()`. Træk, ‹ › og tastatur bruger alle `saetVaerdi`.

### Træk

1. `pointerdown`: gem start-x og startværdi, og kald `setPointerCapture`.
2. `pointermove`: `delta = round((x − x0) / prAar)`. Når delta overstiger 4 px, er det et
   træk, og `saetVaerdi(startværdi + delta)` kaldes uden genberegning undervejs.
3. `pointerup`: ved et træk regnes der igen. Ellers er det et klik, der vælger rækken.
4. `prAar` gemmes af `placerBjaelker`, så samme akse bruges.
5. `touch-action: none` på bjælken, så et træk ikke scroller siden. Sporet scroller normalt.

### Tastatur

`keydown` på kontrollen:
- ← og ↓ giver −1, → og ↑ giver +1
- Page Down giver −5, Page Up giver +5
- Home og End går til min og maks

### Tests (browser, test først)

`tests/browser/test_tidslinje.py`, med en hjælper, der kører guiden med den syntetiske
rapport:
- træk bjælken 2 år, så starten bliver +2 og hovedtallet ændrer sig
- træk under tidligste alder stopper ved minimum
- greb: varighed +5, og ved minimum stopper den ved 10
- folkepension: træk giver udskydelse, og der kan ikke trækkes før folkepensionsalderen
- klik viser ‹ ›, og › giver +1
- tastatur: → → giver +2, og Home giver min
- ARIA: role, valuenow, valuetext og label
- datapanelet er synkront
- bjælken ligger højst 2 px fra søjlen
- mål på mindst 24 px, axe 0 fejl, ingen scroll ved 360 px
- ingen `input[type=range]` i tidslinjen

## Constitution Check

| # | Princip | Gate | Status |
|---|---|---|---|
| I | Deterministisk beregning | Kernen regner efter slip. Bjælken viser kun valget | [x] |
| II | Regelregister | Grænser fra `graenser` (registret) | [x] |
| III–VI | | Uændret | [x] |
| VII | Persondata | Uændret (alt i browseren) | [x] |
| VIII | Dansk brugerflade | Tekster og ARIA på dansk | [x] |
| IX | Simpelhed | Ingen nye afhængigheder. Skyderne fjernes (mindre kode) | [x] |
| X | Brugeroplevelse | Én kontrol pr. ordning. Alternativ uden træk og 24 px-mål (WCAG 2.2) | [x] |
| XI | Ingen persondata til AI | Uændret | [x] |
