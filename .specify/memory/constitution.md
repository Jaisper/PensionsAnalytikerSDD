<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0 (MINOR: nyt Princip X — Brugeroplevelse)
Tidligere: [TEMPLATE] → 1.0.0
Rationale: Første ratificering for greenfield-genopbygningen. Erstatter legacy-forfatningen
(legacy/constitution-v1.md), som var udledt bagud fra den eksisterende kode og bundet til
konkrete filer og teknologi. Denne version er teknologiuafhængig; teknologivalg træffes pr.
feature i /speckit-plan.

Principles:
  - I.   Deterministisk Beregning — AI'en Beregner Aldrig (NON-NEGOTIABLE)  [videreført fra v1 I]
  - II.  Regelregister: Ét Kildested med Kildehenvisning                    [videreført/udvidet fra v1 II]
  - III. Lovgivningen er Facit                                              [NY]
  - IV.  Test Først med Facit-tal (NON-NEGOTIABLE)                          [omdefineret fra v1 III]
  - V.   Sporbarhed og Gennemsigtighed                                      [udvidet fra v1 IV]
  - VI.  Isoleret Beregningskerne                                           [omdefineret fra v1 V]
  - VII. Persondata og Privatliv                                            [videreført fra v1 VI, teknologi fjernet]
  - VIII. Dansk Brugerflade                                                 [videreført fra v1 VII]
  - IX.  Simpelhed                                                          [omdefineret fra v1 VIII, teknologi fjernet]
  - X.   Brugeroplevelse: Klarhed før Fuldstændighed                        [NY i 1.1.0 — legacy-UX var svær at bruge]

Added sections: Kildehierarki · Legacy-løsningens rolle · Udviklingsproces og kvalitetsgates · Governance
Removed sections: Teknologibegrænsninger (flyttet til de enkelte features' plan.md)

Templates:
  ✅ .specify/templates/plan-template.md — Constitution Check udfyldt med konkrete gates
  ⚠ .specify/templates/spec-template.md — ingen ændring nødvendig (teknologiuafhængig i forvejen)
  ⚠ .specify/templates/tasks-template.md — ingen ændring; test-først følger allerede af skabelonen

Deferred / TODO: none
-->

# PensionsAnalytiker Constitution

PensionsAnalytiker er et beslutningsstøtteværktøj til dansk pensionsplanlægning. Det
fremskriver en borgers forventede pensionsudbetalinger år for år efter gældende dansk skatte-
og pensionslovgivning og forklarer resultatet. Værktøjet er information, ikke reguleret
rådgivning.

## Core Principles

### I. Deterministisk Beregning — AI'en Beregner Aldrig (NON-NEGOTIABLE)

Alle tal, som brugeren ser (skat, udbetalinger, ydelser, fremskrivninger, scenarier,
optimeringsresultater), SKAL komme fra den deterministiske beregningskerne. Beregningen SKAL
være færdig, før en AI-model formulerer et svar, og AI'en må kun gengive og forklare tal fra
kernen. Den må aldrig selv beregne, afrunde om, interpolere eller estimere tal. Hvis en
undtagelse alligevel er nødvendig, SKAL den være snævert afgrænset, bruge en fast og
dokumenteret formel og være godkendt som en ændring af denne forfatning.

Rationale: Tallenes troværdighed skal kunne efterprøves ved at læse og teste kernen. Det må
ikke afhænge af en sprogmodels regnefærdigheder.

### II. Regelregister: Ét Kildested med Kildehenvisning

Alle satser, beløbsgrænser, procenter og aldersregler fra lovgivningen SKAL ligge i ét
regelregister som data og ikke som tal i koden. Hver post SKAL have:
- en entydig id
- en værdi
- et gyldighedsår (satsår)
- en kildehenvisning (lov og paragraf og/eller officiel URL)
- en verifikationsstatus: `verificeret`, `sekundær kilde` eller `uverificeret`

Ingen anden del af løsningen (beregning, AI-tekst, brugerflade) må indeholde en kopi af en
sats. Den SKAL læses fra registret. Regelregistret SKAL kunne indeholde flere satsår side om
side, og en beregning SKAL angive, hvilket satsår den bruger.

Rationale: Legacy-løsningen havde flere indbyrdes modstridende kopier af de samme satser, og
det gav forkerte tal hos brugeren. Når der kun er ét kildested, bliver den årlige
satsopdatering og en revision overskuelig.

### III. Lovgivningen er Facit

Beregningsreglerne SKAL følge gældende dansk lovgivning. Den eksisterende løsning,
pensionsselskabernes beregnere og sekundære vejledninger er ikke facit. Hver regel i
specifikationen SKAL henvise til sit lovgrundlag. Når der er afvigelse fra loven, skal den
enten:
1. rettes, eller
2. beskrives eksplicit som en **forenkling** med begrundelse, betydning for resultatet og
   synlighed for brugeren (jf. Princip V).

Modelleringsantagelser, som ikke er lovgivning (fx afkast, inflation, levetid og
satsregulering i fremtidige år), SKAL holdes adskilt fra lovregler og være synlige som
antagelser, som brugeren kan ændre.

Rationale: Brugeren træffer beslutninger med store økonomiske konsekvenser. Valideringen af
legacy viste fejl som AM-bidrag af pensionsudbetalinger, der ikke var opdaget, fordi den gamle
kode blev behandlet som facit.

### IV. Test Først med Facit-tal (NON-NEGOTIABLE)

Al beregningslogik SKAL udvikles med test først. Testene skrives og godkendes, de fejler, og
først derefter implementeres logikken. Testsuiten SKAL omfatte:
- **Golden cases**: håndberegnede facit-tal, der helst følger lovens eller myndighedernes
  egne eksempler, og med kildehenvisning. De må kun ændres med skriftlig begrundelse.
- **Regelgrænser**: værdier lige på, under og over hver tærskel i regelregistret.
- **Differentialtest mod legacy**: alle afvigelser fra `legacy/` SKAL kunne forklares af en
  dokumenteret lovrettelse eller et bevidst ændret valg.
- **Fejlrettelser**: en test, der fejler før rettelsen.

Hele suiten SKAL kunne køres med én kommando og uden netværk eller kørende server.

Rationale: Testene er det offentlige bevis for, at beregningerne er korrekte.

### V. Sporbarhed og Gennemsigtighed

Hvert beregnet tal SKAL kunne spores til de registerposter og antagelser, der indgik i det.
Resultatet SKAL eksplicit oplyse:
- brug af satser, der ikke er `verificeret`
- forenklinger (jf. Princip III), som påvirker resultatet
- tilnærmelser og ufuldstændige søgninger, fx hvor mange kombinationer der er evalueret ud af
  hvor mange mulige
- advarsler, der er relevante for brugerens beslutning, fx loft overskredet eller høj
  marginalskat

Ved enhver konkret anbefaling SKAL brugeren få at vide, at værktøjet er information og ikke
rådgivning, med henvisning til en certificeret pensionsrådgiver.

Rationale: Brugeren og en revisor skal kunne se, hvor sikkert hvert tal er, og hvorfor det
har den værdi, det har.

### VI. Isoleret Beregningskerne

Beregningskernen SKAL være en selvstændig komponent med et veldefineret input- og
outputformat. Den må ikke indeholde I/O, netværkskald, AI, brugerflade eller lagring. Samme
input og samme satsår SKAL altid give samme output. "Dags dato" er input og må ikke læses
implicit. Alle andre dele (import, AI-forklaring, optimering, husstand, brugerflade) bruger
kernen gennem dens grænseflade og må ikke selv beregne skat eller ydelser.

Rationale: En revisor skal kunne verificere alle tal ved kun at læse kernen og
regelregistret.

### VII. Persondata og Privatliv

Pensionsoplysninger er følsomme personoplysninger. Derfor gælder:
- **Dataminimering**: Der gemmes kun det, som den aktive session har brug for.
- **Uploadede dokumenter**: De SKAL slettes, så snart de er behandlet.
- **Opbevaring**: Persondata må ikke gemmes permanent, i cache eller i logs uden et
  dokumenteret formål og en sletteregel.
- **Eksterne tjenester**: Brugeren SKAL oplyses om, at data sendes til en ekstern tjeneste
  (fx en AI-udbyder), før det sker.
- **Diagnostik**: Endpoints, der eksponerer rå data eller tillader at manipulere sessionen,
  må ikke være tilgængelige i en offentlig udrulning.
- **Hemmeligheder**: De SKAL komme fra miljøet og må aldrig committes.

Rationale: Juridisk forpligtelse (GDPR) og tillid.

### VIII. Dansk Brugerflade

Alt indhold, som brugeren ser, SKAL være på dansk og bruge dansk talformat (punktum som
tusindtalsseparator og komma som decimaltegn). Det gælder tekst, fejlbeskeder, AI-svar og
eksport. Fagudtryk SKAL følge myndighedernes terminologi (fx "pensionstillæg", "personlig
tillægsprocent", "ældrecheck"). Kode, kommentarer og commits må være på dansk eller engelsk.

Rationale: Målgruppen er danske borgere, der planlægger pension efter dansk lov.

### IX. Simpelhed

Vælg den enkleste løsning, der opfylder specifikationen. Nye komponenter, afhængigheder og
abstraktioner SKAL begrundes i `plan.md`: hvilket problem løser de, og hvorfor er den
simplere løsning ikke nok? Funktionalitet bygges kun, når en specifikation kræver den
(YAGNI).

Rationale: Projektet vedligeholdes af én udvikler. Færre dele giver mindre at vedligeholde og
sikre.

### X. Brugeroplevelse: Klarhed før Fuldstændighed

Brugerfladen er for borgere uden faglig viden om pension. Den SKAL følge disse regler:
- **Svaret først**: Hver visning SKAL først svare på brugerens hovedspørgsmål ("Hvad får jeg
  udbetalt om måneden efter skat?") med ét tydeligt tal. Detaljer (år-for-år, skat pr.
  kilde, sporing) vises ved progressiv afsløring (fold-ud, faneblade), ikke på én gang.
- **Forenkl informationen**: Højst én primær beslutning eller handling pr. skærmbillede.
  Tabeller og grafer viser kun de kolonner og serier, der understøtter beslutningen. Resten
  er tilgængeligt, men skjult som udgangspunkt.
- **Kontekstuel bevidsthed**: Spørg kun om oplysninger, når de skal bruges, og forklar
  hvorfor. Fagudtryk (fx "pensionstillæg", "tillægsprocent") SKAL forklares i konteksten,
  hvor de står (fx med info-ikon eller tooltip). Brugeren skal ikke slå dem op andre steder.
- **Konsekvent visuel logik**: Samme farve og form betyder altid det samme i hele løsningen,
  fx én linkfarve, én farve for primære handlinger og én fast farve pr. indkomstkilde i alle
  grafer. Status (verificeret/forenkling/advarsel) har fast ikon og farve og kommunikeres
  aldrig kun med farve.
- **Usikkerhed uden støj**: Forenklinger, antagelser og uverificerede satser (Princip V)
  SKAL være synlige, men placeres sammen med det tal, de påvirker. De må ikke overdøve
  hovedbudskabet.
- **Fejl og tomme tilstande**: De SKAL forklare på dansk, hvad der skete, og hvad brugeren
  kan gøre nu. Tekniske fejlkoder vises aldrig alene.
- **Tilgængelighed**: WCAG 2.2 niveau AA. Den skal kunne bruges med tastatur og på en
  mobilskærm (360 px) uden vandret scroll.
- **Klarsprog**: Korte sætninger, aktiv form og "du"-form.
- **Validering**: Hver feature med brugerflade SKAL valideres før merge, enten med en
  heuristisk evaluering (Nielsens 10 heuristikker) dokumenteret i feature-mappen eller med
  en brugertest med mindst 3 personer fra målgruppen.

Rationale: Legacy-løsningen havde korrekte tal, men en brugerflade, der var svær at bruge.
Et korrekt tal, som brugeren ikke forstår, giver ikke bedre beslutninger. Principperne
bygger på DodgeUX' fokus på forenklet information, kontekstuel bevidsthed og konsekvent
farvelogik, samt på Nielsens heuristikker og WCAG.

## Kildehierarki

Ved verifikation af en registerpost gælder denne rækkefølge, med den mest autoritative
først:

1. **Lovgivning**: lovtekst og bekendtgørelser (retsinformation.dk) og vedtagne lovforslag
   (ft.dk).
2. **Myndigheder**: skat.dk og Den juridiske vejledning, Skatteministeriet, borger.dk,
   Udbetaling Danmark, Beskæftigelsesministeriet og Finanstilsynet.
3. **Lovbestemte institutioner**: fx ATP.
4. **Sekundære kilder**: fx Ældre Sagen, pensionsselskaber, revisionshuse og fagmedier.

Status `verificeret` kræver en kilde fra niveau 1–3. En post, der kun bygger på niveau 4,
SKAL have status `sekundær kilde`.

## Legacy-løsningens rolle

`legacy/` (tag `legacy-v1`) må kun bruges som:
- **Kilde til domæneviden** (jf. `docs/domaene/`)
- **Orakel** i differentialtests (jf. Princip IV)

Den er ikke facit (jf. Princip III), og der bygges ikke videre på dens kode. Når
genopbygningen dækker al legacy-funktionalitet, kan mappen fjernes ved en ændring af denne
forfatning.

## Udviklingsproces og kvalitetsgates

- **Spec Kit-flow pr. feature**: Hver feature følger `/speckit-specify` → `/speckit-clarify`
  → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`. Specifikationen beskriver
  *hvad* og *hvorfor*, og teknologivalg hører til i `plan.md`.
- **Constitution Check i plan**: `/speckit-plan` SKAL gennemgå alle principper. Afvigelser
  SKAL begrundes i "Complexity Tracking", før arbejdet fortsætter.
- **Review af tal og satser**: En ændring, der indfører et tal uden for regelregistret, SKAL
  afvises (Princip II). En ny eller ændret regel uden lovhenvisning SKAL afvises
  (Princip III).
- **Review af AI-tekst**: Ændringer i AI-instruktioner SKAL reviewes for, om de giver AI'en
  mulighed for selv at beregne (Princip I).
- **Testsuite**: Hele testsuiten SKAL bestå før merge (Princip IV).
- **Årlig satsopdatering**:
  1. Tilføj et nyt satsår i registret.
  2. Verificér hver post mod kildehierarkiet.
  3. Opdatér golden cases med nye, eksplicit forventede tal. Det er ikke nok, at testene
     "stadig er grønne".
- **Persondata**: Ændringer, der rører persondata, SKAL beskrive opbevaring og sletning i
  `plan.md` (Princip VII).

## Governance

Denne forfatning har forrang over alle andre praksisser, skabeloner og dokumenter i
projektet. Ændringer SKAL dokumenteres med en Sync Impact Report og versioneres semantisk:
- **MAJOR**: Et princip fjernes eller omdefineres, så det ikke er bagudkompatibelt.
- **MINOR**: Et nyt princip tilføjes, eller en regel udvides væsentligt.
- **PATCH**: Sproglige præciseringer.

Alle specifikationer, planer og implementeringer SKAL vurderes mod principperne. Afvigelser
SKAL begrundes skriftligt i `plan.md`, før arbejdet fortsætter.

**Version**: 1.1.0 | **Ratified**: 2026-10-24 | **Last Amended**: 2026-10-24
