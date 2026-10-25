# Implementation Plan: Engangsbeløb og buffer i grafen

**Branch**: `008-buffer-i-grafen` | **Spec**: [spec.md](spec.md)

## Design

1. **Kernen** (`model.py` og `fremskrivning.py`): Ny `Engangsbeloeb(ordning_id, type, alder,
   netto, i_buffer)`. `Fremskrivning.engangsbeloeb` bygges af de planer, der allerede findes.
   Det er en tilføjelse, og ingen beregning ændres.
2. **Visningen** (`visning.py`):
   - `_hovedtal`: Det faste beløb er min(jævn × realfaktor) / 12, fra det første år. `senere`
     er niveauet efter det sidste spring, hvis der er et spring. `foer` udgår.
   - `graf.engangs`: én post pr. engangsbeløb med netto i dagens kroner.
   - `graf.buffer`: buffer_rest × realfaktor pr. alder. Bufferen ender i 0. Under 1 kr. vises
     som 0 (samme regnestøj som 007 R002).
   - Engangskortet viser pr. ordning med buffer eller direkte.
3. **Optimeringen**: målet `fast_niveau(res, vindue(res))` er nu det samme som hovedtallet.
   `maaned` omdøbes til `slutniveau` og bruges kun ved uafgjort.
4. **Brugerfladen**:
   - Linjen hedder "Fast beløb, hvis du udjævner".
   - Et inline Chart.js-plugin tegner markører for engangsbeløb (rombe og tekst øverst i
     plotområdet, stablet ved samme alder, højrestillet i højre halvdel).
   - `#buffergraf` er et lille linjeareal (140 px). Begge grafer får fast y-aksebredde
     (`afterFit`), så x-akserne flugter.
   - `#jaevn-forklaring` forklarer linjen. Engangsbeløbene står også i `#graf-markeringer`.
     Tabellen får kolonnerne "Engangsbeløb" og "Buffer".
   - Hovedtallets tekst: "fast beløb … hvis du selv udjævner" og eventuelt "stiger senere".

## Tests (test først)

- Kernen: `Fremskrivning.engangsbeloeb` pr. ordning, summen er lig `engangsbeloeb_netto`, og
  `i_buffer` følger ordningen.
- Visningen:
  - hovedtallet er min af den jævne række, `senere` ved spring
  - `graf.engangs` og `graf.buffer`
  - SC-001: hovedtallet er lig optimeringens faste beløb
- Browser:
  - linjens navn og forklaringen
  - markørlisten med "buffer" eller "udbetales"
  - buffergrafen flugter med hovedgrafen (højst 2 px)
  - hovedtallet efter "Anvend" er lig forslaget
  - axe og 360 px

## Constitution Check

I (ingen ny beregning), V (engangsbeløb og buffer synlige), VI (kernen er uændret i sine
beregninger), VIII og X (klart sprog og ét tal) er alle opfyldt. Der er ingen nye afhængigheder
(IX).
