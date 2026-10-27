# Roadmap

Rækkefølgen er besluttet 2026-10-26. Hver feature får sin egen spec under `specs/NNN-*/`.
Numrene følger, hvornår en spec blev oprettet, ikke rækkefølgen herunder.

## Rækkefølge

| # | Feature | Status | Forudsætter |
|---|---|---|---|
| 013 | Husstandsbalance: opsparing uden for pension (bank) | I luften (2026-10-26) | 009, 010, 012 |
| 018 | Usikkerhed om afkast (±1 procentpoint) og inflation (±0,5 procentpoint), som legacy | I luften (2026-10-26) | 007 |
| 019 | Levetid som scenarie (planen til 85 og 95 år) | I luften (2026-10-26) | 018 |
| 017 | Arbejdsår og løn før pension | I luften (2026-10-27) | 013 |
| 020 | Forklaring i tre niveauer (020a–d), forenklingsregistret | I luften (2026-10-27); SC-004 brugertest udestår | 017 |
| [024](../specs/024-gem-lokalt/spec.md) | Gem og genindlæs lokalt | Færdig, ikke merget | – |
| [013b](../specs/013b-frit-depot-ask/spec.md) | Frit depot og aktiesparekonto | Spec (modnes) | 013, 017 |
| [021](../specs/021-naeste-krone/spec.md) | "Hvor skal næste krone hen?" | Spec (modnes) | 017, 013b (014 for afdrag) |
| [023](../specs/023-afkast-pr-aar/spec.md) | Afkast pr. år og "dårlige år først" | Spec (modnes) | – |
| [022](../specs/022-efterladte/spec.md) | "Hvad hvis min partner dør?" | Spec (modnes) | 012, 018, 019 |
| – | Optimér trækrækkefølge (013 US3) | Idé | 017, 013b |
| [014](../specs/014-bolig/spec.md) | Bolig og friværdi (014a–d) | Spec (modnes) | 013, 013b |
| [015](../specs/015-arv/spec.md) | Arv modtaget og givet | Spec (modnes) | 013, 022 |
| [016](../specs/016-monte-carlo/spec.md) | Monte Carlo | Spec (modnes) | 023 |

Rækkefølgen er et forslag fra modningen; se [modning.md](modning.md).

## Små gevinster, der kan lægges ind imellem

- ~~**Skift mellem nominelle beløb og dagens kroner.**~~ Lavet i 020b. Kernen leverer allerede `realfaktor`, så
  det er ren visning.
- ~~**Rapport til rådgiveren.**~~ Lavet i 020d (udskrift og eksport). Start med en udskriftsvenlig side med forudsætninger og satser
  (Princip V). Det kræver ingen ny afhængighed.
- ~~**Gem og genindlæs lokalt.**~~ Lavet i 024. En fil krypteret med browserens Web Crypto. Ingen server og ingen
  ny afhængighed (Princip VII).

## Tungere, senere

- **Efterløn, seniorpension og tidlig pension** som udbetalingskilder. Hver ordning er sit eget
  lovområde med egen modregning.
- **Omkostninger (ÅOK)** og **forsikringsoverblik** fra PensionsInfo-rapporten. Afhænger af, hvad
  parseren kan aflæse pålideligt.

## Fravalgt

- **Flytning til udlandet.** Dobbeltbeskatningsoverenskomster sprænger Princip IX.

## Kilde

Idélisten kommer fra en gennemgang 2026-10-26, rangeret efter værdi i forhold til indsats.
Ændringer i forhold til den:
- Punkt 2 ("Hvor skal næste krone hen?") er ikke næsten gratis med 013. Fradragsværdien
  afhænger af skatten i arbejdsårene. Derfor kommer 017 først.
- Punkt 1 og 3 er samlet i 017, fordi de bygger på samme model af løn og arbejdsår.
