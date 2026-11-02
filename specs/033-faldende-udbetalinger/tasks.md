# Tasks: 033 Faldende udbetalinger

- [x] T001 Spec og afklaring (2026-11-02)
- [x] T002 Plan: profilens form i kernen (`Antagelser` eller `Pensionsprofil`), båndene fra `stopalder`, husstanden
- [x] T003 Test først: golden cases og egenskabstest for vægtet udjævning (røde før kernen)
- [x] T004 `jaevn.py`: vægt pr. år; optimeringens mål og uafgjort-regel i forhold til profilen
- [x] T005 Brugerflade: equalizeren, tekst under hovedtallet, forklaring, gem og udskrift
- [x] T006 Browsertest med tastatur og axe-core
- [x] T007 Hele suiten grøn, også browsertestene

## Fund undervejs

- FR-007 var for stærk: en mindre buffer giver mindre formue og kapitalindkomst og dermed lidt mere
  pensionstillæg og ældrecheck. Rettet i specen og testet i `test_profilen_aendrer_ikke_udbetalingerne_kun_bufferen`
- Bånd på ét år (84–84 ved stop 64): et bånd før 85 kortere end tre år lægges nu sammen med det foregående
- Kommer pengene først senere (fx folkepension), kan et senere bånd give mere end det foregående, fordi
  udjævningen ikke låner. Teksten under hovedtallet er derfor neutral, og en note ved equalizeren
  forklarer det og peger på "Find bedste plan"
- Ændres profilen, søges den bedste plan igen automatisk (007b), fra borgerens egen plan med den nye profil,
  så "Brug min egen plan" stadig er borgerens egen. Først skulle borgeren selv trykke "Find bedste plan",
  men gevinsten ligger netop i at rykke udbetalingerne frem, så de passer til profilen
