# Tasks: 031 Dine forsikringer fra PensionsInfo

- [x] T001 Spec og plan. Layoutet aflæst fra PensionsInfos demorapport (fiktive data)
- [x] T002 Test først: syntetiske forsikringssider i `tests/app/pensionsinfo_syntetisk.py` og
  `tests/app/test_pensionsinfo_daekninger.py` (død pr. modtager og kolonne, tab af arbejdsevne, kritisk sygdom,
  sundhed, uændrede ordninger, ukendt layout). Røde før parseren
- [x] T003 Demotest (`PENSIONSINFO_DEMO`), kører kun lokalt
- [x] T004 `daekninger.py` og kontrakten `AflaestDaekning`
- [x] T005 `omsaet.til_guide`: `forsikringer` og afsnittenes bemærkninger (test i `test_pdf_omsaet.py`)
- [x] T006 Browsertest `tests/browser/test_forsikringer.py` og afsnittet "Hvis du bliver syg eller dør"
- [x] T007 Lokal kørsel mod produktejerens egen rapport (kun strukturelle invarianter, ingen tal i output):
  alle tabeller summer til rapportens "I alt", ingen bemærkninger. Fandt kritisk sygdom for børn
  (`kritisk_sygdom_boern`), som nu også er i den syntetiske rapport
- [ ] T008 Hele suiten grøn, også browsertestene
