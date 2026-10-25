# UX-evaluering: Engangsbeløb og buffer i grafen

**Dato**: 2026-10-25 · **Metode**: browsertests (`tests/browser/test_graf_buffer.py`), headless
Chrome ved 1366 og 360 px, axe-core 4.9.1. Spørgsmålet kom fra produktejeren, der så grafen
for en rigtig rapport: "Tæller kapitalpension med som buffer her? Hvordan skal jævnt beløb
fortolkes?"

## Før og efter

| | Før (005–007) | Efter (008) |
|---|---|---|
| Engangsbeløbet | usynligt i grafen | markør ved året: "Kapitalpension ca. 550.000 kr. → buffer" eller "→ udbetales", også i listen og tabellen |
| Linjen | "Jævnt fordelt (beløbet øverst)" | "Fast beløb, hvis du udjævner" med en forklaring under grafen |
| Bufferen | usynlig | lille graf under hovedgrafen, samme aldersakse (højst 2 px, test) |
| Hovedtal | niveauet efter sidste engangsbeløb | fast beløb hele perioden, som er lig optimeringen. Et senere spring nævnes |

## Målinger

| Måling | Resultat |
|---|---|
| Hovedtal er lig optimeringens faste beløb | ja (test SC-001), lukker E1 fra 007 |
| Hovedtal efter "Anvend" er lig forslaget | ja (test) |
| Buffergrafen flugter med hovedgrafen | ≤ 2 px (test) |
| axe | 0 overtrædelser |
| Vandret scroll ved 360 px | nej |

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| F1 | Markørernes tekst kan ved mange engangsbeløb samme år stables over søjlerne. Listen under grafen er altid læsbar | 1 |
| F2 | Bufferens afkast er antaget med skat af kapitalindkomst, og afkastet kan påvirke pensionstillægget. Det står som forudsætning, men ikke ved buffergrafen | 1 |
