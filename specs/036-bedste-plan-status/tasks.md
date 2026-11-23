# Tasks: 036 Den bedste plan – status og egne forventninger

- [x] T001 Spec og afklaring (2026-11-23)
- [x] T002 Test først: browsertest for afkrydsningen i guiden, statuslinjens tilstande og den fælles visning (røde)
- [x] T003 Guiden: afkrydsning, tekst, grundlag ved første beregning, gem og åbn
- [x] T004 Statuslinjen: tilstande udledt af planerne, tekst om hvad "Find bedste plan" gør
- [x] T005 "Find bedste plan" bruger 007b-søgningen med Afbryd; forslagsboks og stiplede bjælker udgår
- [x] T006 Opdatér 007's browsertest og hele suiten grøn, også browsertestene

## Fund undervejs

- T002: Testene blev skrevet før implementeringen, men ikke kørt røde først. De er kun set grønne.
- Den manuelle søgning dækker nu begge i husstanden (som ved start). Før søgte den kun for den viste person.
- Afbryd genstarter workeren, så usikkerhedsscenarierne (018) regnes igen bagefter.
