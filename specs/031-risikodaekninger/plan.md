# Plan: 031 Dine forsikringer fra PensionsInfo

## Teknisk tilgang

- **Parser** (`src/pensionsoverblik/pdfimport/daekninger.py`): nyt modul ved siden af `pensionsinfo.py`.
  Indholdsfortegnelsen giver et vindue af sider. Sidehovedet afgør afsnittet, fordi fortegnelsens
  sidetal kan være en side forskudt (demorapporten). Tabelrækker findes ved skattekoden (x ≈ 87–91),
  beløbene tildeles kolonnen med nærmeste højre kant, og detaljesidens blokke matches til rækkerne pr.
  type, selskab og aftalenr. Sundhedsforsikringen har kun detaljer. Bemærkningerne står lodret centreret om
  rækken.
- **Kontrakt** (`aflaeser.py`): `AflaestDaekning`, og `Aflaesning` får `daekninger` og `bemaerkninger`
  med standardværdier (bagudkompatibel).
- **Guidedata** (`omsaet.py`): `forsikringer` ved siden af `ordninger`. Kernen ser dem aldrig
  (`oversaet.til_kerne` læser dem ikke).
- **Brugerflade**: `tilstand.forsikringer` og `tilstand.partnerForsikringer` (følger med gem, 024).
  Afsnittet `#forsikringer` efter "Hvad består beløbet af?" vises for den valgte fane (dig/partner) og
  skjules under "Jer".

## Forfatningstjek

| Princip | Tjek | Status |
|---|---|---|
| I | Ingen ny beregning. Beløbene vises, som de står | [x] |
| III | Ingen nye satser; skattekoderne er rapportens egne | [x] |
| IV | Test først: syntetisk rapport, demotest lokalt, browsertest | [x] |
| X | Svaret først: summen ved død øverst, skat og varighed i ord | [x] |
| XI | Lokal parser. Demorapporten er fiktiv; den rigtige rapport køres kun lokalt, intet committes | [x] |

## Risici

- Andre selskaber kan bruge andre kolonner (fx "Om året, så længe du lever" ved død). Kolonnerne læses
  generisk, og formen tages fra gruppen eller kolonnen.
- Et ukendt layout giver en bemærkning i stedet for forkerte tal (FR-003).
