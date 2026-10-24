# UX-evaluering: Pensionsoverblik

**Dato**: 2026-10-24 · **Metode**: heuristisk evaluering (Nielsens 10) og automatisk
tilgængelighedstest (axe-core 4.9.1, WCAG 2.0/2.1/2.2 A+AA) · **Testprofil**: født 1.5.1963,
Aarhus, ratepension 1,2 mio., livsvarig 1,5 mio., aldersopsparing 0,3 mio.
**Viewport**: 1440×900 og 360×780 i headless Chrome.

Alvorlighed: 0 = ikke et problem · 1 = kosmetisk · 2 = mindre · 3 = større · 4 = katastrofe.

## Automatiske målinger

| Måling | Resultat |
|---|---|
| axe-core, guide | **0 overtrædelser** |
| axe-core, resultatside | **0 overtrædelser** |
| Vandret scroll ved 360 px | **Ingen** (`scrollWidth` = 360) efter rettelse (se R2) |
| Genberegning ved skyder | Hovedtallet opdateres, og ændringen vises ("↓ 1.200 kr. i forhold til før") |
| Konsolfejl | Kun den forventede 422 fra testen af en ugyldig skydeværdi |

## Fund rettet under evalueringen

| # | Fund | Heuristik | Alv. | Rettelse |
|---|---|---|---|---|
| R1 | "17.800 kr. kr. om måneden": "kr." stod to gange | 8 Æstetik | 1 | Enheden er nu "om måneden efter skat" |
| R2 | "Ny beregning" stak ud af topbjælken ved 360 px → vandret scroll | 8 / WCAG 1.4.10 | 3 | Mindre knap og logo på mobil |
| R3 | Hovedtallet (17.800 kr. "fra 65 år") stemte ikke med de fleste år (19.000 kr.), fordi aldersopsparingen først løfter niveauet som 66-årig | 2 Match med virkeligheden | 3 | Hovedtallet er nu niveauet efter det sidste engangsbeløb. De første år nævnes i teksten. Grafen viser det jævne niveau som en stiplet linje |
| R4 | Aldersopsparingen (engangsbeløb) var usynlig i overblikket | 1 Synlighed | 3 | Nyt kort "Engangsbeløb" med beløb, alder og dagens kroner |
| R5 | To lange forudsætninger i heroen konkurrerede med svaret | 8 Minimalisme / Princip X | 2 | Samlet i "≈ 2 forudsætninger bag tallet →" (fold-ud) |
| R6 | En ugyldig startalder på skyderen blev stående | 9 Fejlhåndtering | 2 | Skyderen vender tilbage til seneste gyldige værdi, og fejlen forklares |
| R7 | Manglende favicon gav en 404 i konsollen | — | 0 | Inline favicon |

## Gennemgang pr. heuristik

| # | Heuristik | Vurdering |
|---|---|---|
| 1 | Synlighed af systemstatus | ✓ Fremdrift i guiden ("1 Om dig – 2 – 3"), "Regner …" på knappen og ændringen efter en skyder. Mangler en indikator under genberegning fra skydere (A1) |
| 2 | Match med virkeligheden | ✓ Klarsprog og du-form. Fagord forklares med (i). "Indkomst, der nedsætter tillæg" og "Tillægsprocent" i årstabellen er ikke forklaret (A2) |
| 3 | Brugerkontrol og frihed | ✓ Tilbage, Nulstil og Ny beregning (svarene bevares). En enkelt ordning kan ikke rettes direkte fra resultatsiden (A3) |
| 4 | Konsistens | ✓ Faste kildefarver i graf, kort og guide. Samme "→"-mønster for alle fold-ud |
| 5 | Fejlforebyggelse | ✓ "Ved ikke" om oprettelsesdato bruger den mest forsigtige regel og advarer. Dato-felter har `min` |
| 6 | Genkendelse frem for erindring | ✓ Søgbar kommuneliste. Oprettelsesperioder som valg i stedet for en dato |
| 7 | Fleksibilitet | ✓ Skydere til følsomhed. Tastaturbetjening og tabelalternativ til grafen |
| 8 | Æstetik og minimalisme | ✓ Svaret først. Detaljer foldet sammen. Kortet "Ældrecheck og mediecheck" kan vise et meget lille beløb langt ude i fremtiden (her 31 kr./md. fra 90 år), hvilket virker forvirrende (A4) |
| 9 | Fejlhåndtering | ✓ Kernens danske fejl vises ved feltet, og guiden hopper til det trin, fejlen hører til |
| 10 | Hjælp og dokumentation | ✓ (i)-forklaringer, "Sådan har vi regnet" med satser, kilde og status samt forudsætninger |

## Åbne fund (til næste iteration)

| # | Fund | Alv. |
|---|---|---|
| A1 | Ingen synlig "regner …"-tilstand ved genberegning fra skydere (typisk < 300 ms, så lav prioritet) | 1 |
| A2 | Kolonnerne "Indkomst, der nedsætter tillæg" og "Tillægsprocent" mangler forklaring | 1 |
| A3 | En ordning kan ikke rettes fra resultatsiden. Man skal via "Ny beregning" (data bevares) | 2 |
| A4 | Kort med meget små beløb (fx checks på 31 kr./md.) bør forklares eller nedtones | 2 |

## Ikke gennemført

- **SC-001/SC-002 (brugertest med mindst 3 personer fra målgruppen)** kræver rigtige
  brugere. FR-054 er opfyldt af den heuristiske evaluering, men brugertesten anbefales før
  offentlig lancering.

## Skærmbilleder

- [Resultat, desktop](billeder/resultat_desktop.png)
- [Resultat, mobil](billeder/resultat_mobil.png)
- [Guide, mobil](billeder/guide_mobil.png)
