# UX-evaluering: Tidslinje og datapanel

**Dato**: 2026-10-25 · **Metode**: headless Chrome (1366 px og 360 px), axe-core 4.9.1 og
heuristisk gennemgang. Testet med den syntetiske rapport (`tests/app/pensionsinfo_syntetisk.py`)
og lokalt med en rigtig PensionsInfo-rapport. Skærmbilleder af den rigtige rapport er IKKE gemt
i repoet.

## Målinger

| Måling | Syntetisk | Rigtig rapport |
|---|---|---|
| Tidslinjerækker (ordninger + folkepension) | 5 | 6 |
| Afvigelse mellem bjælke og grafens søjle (SC-002, ≤ 2 px) | 0 px | 0 px |
| axe-core | 0 overtrædelser | 0 overtrædelser |
| Vandret scroll ved 360 px | nej | nej |
| Skyder +2 år → nyt hovedtal (SC-001) | ↑ 1.900 kr. | ↑ 1.600 kr. |
| Skyder kan ikke under tidligste alder | min = 60 (oplyst) | min = 60 (oplyst) |
| Datapanel viser samme start som tidslinjen | ja | ja |
| "Opdater beregning" fra panelet | ja | ja |
| "Ny beregning" flytter formularen tilbage til guiden | ja | ja |

## Heuristik (kort)

- **Brugerkontrol (3):** Ordninger flyttes direkte, og "Nulstil" og panelet giver vej tilbage.
  Det åbne fund A3 fra 002 er løst.
- **Synlighed (1):** Bjælken flytter sig straks, mens hovedtallet opdateres efter
  genberegning (debounce 300 ms).
- **Konsistens (4):** Samme kildefarver i graf, bjælker og kort.
- **Fejlforebyggelse (5):** Skydernes minimum er den tidligste lovlige alder.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| B1 | ~~Bjælkerne kan ikke trækkes med musen som i legacy~~ Løst i [006](../006-traek-bjaelker/) | – |
| B2 | Rækkefølgen i tidslinjen følger rapporten, ikke startalderen | 1 |
