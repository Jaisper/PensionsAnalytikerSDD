# Feature Specification: Udviklingsmetoden til revisionen

**Feature Branch**: `041-udviklingsmetode`

**Created**: 2026-11-26

**Status**: Klar (produktejer)

**Input**: "der skal tilføjes en 'udviklinsgmetode.md' der i alle detaljer redegør for hvordan udviklingen af
pensionsanalytiker foregår; SDD proces, herunder hvilke og hvor omfattende tests sker. Det vil interessere den
tekniske revision..." og "og mon ikke også der skal linkes til den beskrivelse ligesom der linkes til metode.."

**Grundlag**: 039 (metodebeskrivelsen som side i løsningen, én kilde), forfatningens afsnit "Udviklingsproces og
kvalitetsgates".

## Krav

- **FR-001**: `docs/udviklingsmetode.md` beskriver roller, styrende dokumenter, processen pr. feature, test først,
  testsuiten pr. kategori med antal, testdata og persondata, byg og leverancekæde, CI og udgivelse, review og
  godkendelse, brug af AI i udviklingen, sporbarhed, årlig satsopdatering samt begrænsninger og anbefalinger.
- **FR-002**: Teksten er sand på opgørelsesdatoen. Tallene er talt op i repositoriet.
- **FR-003**: Siden "Sådan udvikles løsningen" laves af samme kilde ved byggeriet, uden det tekniske (som 039), og
  linkes fra bunden af beregningen ved siden af "Sådan fungerer løsningen". Den åbner i en ny fane, og "Tilbage
  til beregningen" lukker den.
- **FR-004**: De to sider henviser til hinanden, og metodebeskrivelsen henviser til udviklingsmetoden.

## Success Criteria

- **SC-001**: Siden har ingen kodenavne, alle ankre findes, ingen tilgængelighedsfejl (WCAG 2.2 AA) og ingen
  vandret rulning ved 360 og 320 px.
