# Roadmap

Rækkefølgen er besluttet 2026-10-26. Hver feature får sin egen spec under `specs/NNN-*/`.
Numrene følger, hvornår en spec blev oprettet, ikke rækkefølgen herunder.

## Rækkefølge

| # | Feature | Status | Forudsætter | Hvorfor her |
|---|---|---|---|---|
| 013 | Husstandsbalance: opsparing uden for pension (bank) | Færdig, ikke merget | 009, 010, 012 | Fundamentet for frie midler |
| 017 | Arbejdsår og løn før pension | Spec (draft) | 013 | Uden løn kender kernen ikke skatten i arbejdsårene. Giver "Hvornår kan jeg stoppe?" og arbejde ved siden af pensionen |
| 013b | Frit depot og aktiesparekonto | Godkendt i 013's opdeling | 013 | Aktieindkomst, ASK og trækrækkefølge |
| – | "Hvor skal næste krone hen?" | Idé | 017, 013b (014 for afdrag på lån) | Kræver skatten i arbejdsårene (fradragsværdi) og ASK at sammenligne med |
| – | "Hvad hvis min partner dør?" | Idé | 012 | Efterladtescenarie |
| – | Optimér trækrækkefølge (013 US3) | Idé | 017, 013b | Valg af hvornår frie midler bruges |
| 014 | Bolig og friværdi | Idé (fra 013) | 013 | |
| 015 | Arv | Idé (fra 013) | 013 | |
| 016 | Usikkerhed og Monte Carlo | Idé (fra 013) | 013 | |

## Små gevinster, der kan lægges ind imellem

- **Skift mellem nominelle beløb og dagens kroner.** Kernen leverer allerede `realfaktor`, så
  det er ren visning.
- **Rapport til rådgiveren.** Start med en udskriftsvenlig side med forudsætninger og satser
  (Princip V). Det kræver ingen ny afhængighed.
- **Gem og genindlæs lokalt.** En fil krypteret med browserens Web Crypto. Ingen server og ingen
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
