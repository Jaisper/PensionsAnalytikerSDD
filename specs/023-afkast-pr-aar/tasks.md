# Tasks: 023a Afkast pr. år og "dårlige år først"

- [x] T001 `tests/golden/test_afkast_pr_aar.py`: håndregnet ratepension efter ét dårligt år, opsparing før start, uændret uden forløb, livrenten uændret, sekvensrisiko, `beregn_jaevn` med rente pr. år
- [x] T002 `model.py` (`Antagelser.afkast_forloeb`, `afkast_i_aar`), `regler/ordninger.py` (`rateplan`/`portioner` med afkast pr. år), `jaevn.py` (rente pr. række)
- [x] T003 `fremskrivning.py`: opsparing, rater, portioner, bufferen, lagene og den urørte opsparing følger årets afkast; forenkling `livsvarig_uden_aarets_afkast`
- [x] T004 `app.py` (`STRESS_*`, `stress_afvigelse`, `scenarier`, `scenarie(stress)`), `oversaet.py`; `tests/app/test_afkast_pr_aar_app.py`
- [x] T005 `app.js` (tabellen, spændet uden forløb), `index.html`, forklaring og forenkling; `tests/browser/test_usikkerhed.py`
- [x] T006 `beregningskerne.md`, roadmap; hele suiten grøn
- [ ] 023b Afkast pr. aktivtype
