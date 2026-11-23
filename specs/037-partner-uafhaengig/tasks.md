# Tasks: 037 Partnerne hver for sig

- [x] T001 Spec og afklaring (2026-11-23)
- [x] T002 Test først: oversættelse, golden cases for egen stopalder, scenarier og browsertest for fanerne (røde)
- [x] T003 Oversættelse: `person.partner.antagelser` (afkast, grundlag, fordeling); inflationen fælles
- [x] T004 Kernen: `faelles_forbrug` udgår; hver persons bånd fra egen stopalder
- [x] T005 Scenarierne flytter partnerens afkast med samme forskel (også stresstestens år)
- [x] T006 Brugerfladen: equalizer, afkastskyder og grundlag pr. fane; note ved forskellige grundlag
- [x] T007 Gem og åbn; "Opdater" i datapanelet bevarer fordelingen og partnerens valg
- [x] T008 Hele suiten grøn, også browsertestene

## Fund undervejs

- Din egen fordeling (033) blev ikke gemt, og "Opdater" i datapanelet nulstillede den. Rettet med samme mekanisme.
- Scenarietesten (FR-004) var grøn før implementeringen, fordi begge havde samme afkast; den er først meningsfuld efter.
- Branchestandarden har sin egen inflation. Ved forskellige grundlag er inflationen derfor ikke den samme; en note
  ved hovedtallet siger det (oplyst produktejer).
