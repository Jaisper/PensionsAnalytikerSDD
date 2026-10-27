# Roadmap

Rækkefølgen er besluttet 2026-10-26. Hver feature får sin egen spec under `specs/NNN-*/`.
Numrene følger, hvornår en spec blev oprettet, ikke rækkefølgen herunder.

## Rækkefølge

| # | Feature | Status | Forudsætter | Hvorfor her |
|---|---|---|---|---|
| 013 | Husstandsbalance: opsparing uden for pension (bank) | I luften (2026-10-26) | 009, 010, 012 | Fundamentet for frie midler |
| 018 | Usikkerhed om afkast (±1 procentpoint) og inflation (±0,5 procentpoint), som legacy | I luften (2026-10-26) | 007 | Ønsket 2026-10-26 |
| 019 | Levetid som scenarie (planen til 85 og 95 år) | I luften (2026-10-26) | 018 | Billigere end Monte Carlo. Levetiden er ofte den største risiko |
| 020a¹ | Forenklingsregistret (fra 020) | Færdig, ikke merget | – | Lille. Gør forenklingerne synlige og testede |
| 017 | Arbejdsår og løn før pension | Færdig, ikke merget | 013 | Uden løn kender kernen ikke skatten i arbejdsårene. Giver "Hvornår kan jeg stoppe?" og arbejde ved siden af pensionen |
| 020 | Forklaring i tre niveauer (resten af 020a, derefter 020b–d) | Spec (besluttet) | 017; 020b kræver skifteren nominel/dagens kroner | Efter 017 (besluttet 2026-10-26) |
| 013b | Frit depot og aktiesparekonto | Godkendt i 013's opdeling | 013 | Aktieindkomst, ASK og trækrækkefølge |
| – | "Hvor skal næste krone hen?" | Idé | 017, 013b (014 for afdrag på lån) | Kræver skatten i arbejdsårene (fradragsværdi) og ASK at sammenligne med |
| – | "Hvad hvis min partner dør?" | Idé | 012 | Efterladtescenarie |
| – | Optimér trækrækkefølge (013 US3) | Idé | 017, 013b | Valg af hvornår frie midler bruges |
| 014 | Bolig og friværdi | Idé (fra 013) | 013 | |
| 015 | Arv | Idé (fra 013) | 013 | |
| – | Afkast pr. år i kernen og "dårlige år først" (stress-forløb) | Idé | 017, 013b | Viser sekvensrisikoen uden statistik. Forudsætning for 016 |
| 016 | Monte Carlo | Idé (fra 013) | afkast pr. år | Kræver kilde til udsving (Rådet for Afkastforventninger) og en hurtigere beregning: ca. 200 forløb i baggrunden, vifte med 10/50/90 % |

¹ Kun forenklingsregistret laves før 017.

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
