# UX-evaluering: Bjælker, der trækkes

**Dato**: 2026-10-25 · **Metode**: headless Chrome ved 1366 og 360 px, axe-core 4.9.1 og
browsertests (`tests/browser/test_tidslinje.py`). Testet med den syntetiske rapport og lokalt
med en rigtig rapport (ingen skærmbilleder af den rigtige rapport er gemt).

## Målinger

| Måling | Syntetisk (5 rækker) | Rigtig (6 rækker) | Krav |
|---|---|---|---|
| Tidslinjens højde ved 1366 px | 399 px (004: 734 px, −46 %) | 479 px | SC-001: mindst −30 % |
| Tidslinjens højde ved 360 px | 506 px | 586 px | |
| Slip → ny beregning | 0,33 s | 0,33 s | SC-002 < 1 s |
| Bjælke mod søjle | ≤ 2 px (test) | | SC-003 |
| axe (med ‹ › synlige) | 0 overtrædelser | | SC-004 |
| Mål for bjælker, punkter og greb | ≥ 24×24 px (test) | | SC-004 |
| Vandret scroll ved 360 px | nej | nej | FR-010 |

## Heuristik (kort)

- **Direkte manipulation:** Bjælken er både visning og kontrol, ligesom i legacy. Varigheden
  trækkes i grebet i bjælkens ende.
- **Synlighed (1):** Perioden ("67–76 år") følger trækket med det samme. Kernen regner, når
  bjælken slippes.
- **Fleksibilitet (7):** Der er tre veje: træk, klik med ‹ ›, og tastatur (pile, Page Up/Down,
  Home/End). Det opfylder WCAG 2.2 2.5.7.
- **Fejlforebyggelse (5):** Grænserne kommer fra kernen og registret. Knapperne deaktiveres ved
  grænsen.

## Fund undervejs

- Ved skift fra desktop- til mobilbredde blev panelerne stående på 1132 px. Grafens canvas
  holdt grid-sporet bredt (`min-width: auto`), så Chart.js aldrig fik plads til at skrumpe.
  Rettet med `minmax(0, 1fr)`. Fejlen fandtes også i 004.
- At flytte en ratepension ændrer ikke altid hovedtallet. Det jævne niveau kan være uændret.
  Testene venter derfor på en ny beregning og ikke på et nyt hovedtal.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| D1 | Ved 360 px er ét år kun cirka 9 px. Træk virker, men finjustering sker bedst med ‹ › | 1 |
| B2 | (fra 004) Rækkefølgen følger rapporten, ikke startalderen | 1 |
