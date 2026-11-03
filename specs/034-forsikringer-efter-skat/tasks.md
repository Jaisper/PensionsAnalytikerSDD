# Tasks: 034 Dine forsikringer – kort med beløb efter skat

- [x] T001 Spec og afklaring (2026-11-02)
- [x] T002 Registerpost `forsikring.afgift` (40 %, status sekundær) med kilde
- [x] T003 Test først: `tests/golden/test_forsikring_efter_skat.py` (A, F, S, tab af arbejdsevne)
- [x] T004 Kernen: `pensionskerne/forsikring.py`
- [x] T005 Visningslaget: `pensionsoverblik/forsikringer.py` og `app.forsikringer` (test i `tests/app/test_forsikringskort.py`)
- [x] T006 Brugerflade: kort med stort tal, bjælker pr. selskab, ophør og detaljer
- [x] T007 Browsertest med axe-core
- [ ] T008 Hele suiten grøn, også browsertestene
- [ ] T009 Verificér afgiften mod lovteksten (PBL § 25 og § 29) og sæt posten til "verificeret"
