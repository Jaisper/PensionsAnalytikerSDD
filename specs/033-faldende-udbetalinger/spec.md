# Feature Specification: Faldende udbetalinger – en equalizer for pensionsårene

**Feature Branch**: `033-faldende-udbetalinger`

**Created**: 2026-11-02

**Status**: Draft – afklaret 2026-11-02, klar til plan

**Input**: "Tænker også at faldende udbetalinger kan være relevant, f.eks. at man umiddelbart i årene
efter pensionering opretholder et højere rådighedsbeløb end når man er mellem 80 og 90 og likvid
behov nok er faldende. Kan vi ikke lave en go-go-løsning til det? F.eks. lidt som en equalizer, hvor
man kan justere % af løn i forskellige perioder." Og: "også 60–65".

**Grundlag**:
- Feature 010 (udjævning uden lån): det faste beløb låner aldrig af senere udbetalinger, og
  bufferen går aldrig i minus. Det gælder fortsat
- Feature 007/007b (den bedste plan) og 030 (stopalderen følger første udbetaling)
- Feature 012 (partner) og 017b (nettoløn ved hovedtallet)
- Princip III: profilen er borgerens eget valg, ikke en lovregel. Den skal være synlig og kunne
  ændres. Princip X: klarhed før fuldstændighed

## Problem

Det faste beløb er i dag det samme i dagens kroner hele livet (eller stiger i trin, 010). Mange
bruger mere i de første år efter pensionen ("go-go") end i 80'erne ("slow-go" og "no-go"). Med et
fladt forløb sparer de op til senere år, hvor de ikke har brug for pengene, og har mindre, mens de
har.

## Clarifications

### Session 2026-11-02

- Q: Hvad angiver skyderne? → A: **Procent af de første år.** Første bånd er altid 100 %, og de
  senere sættes i forhold til det. Værktøjet finder stadig det højeste beløb, nu med borgerens form.
  (Fravalgt: procent af nettolønnen som et mål, der ikke maksimeres.)
- Q: Hvilke perioder? → A: **Bånd på fem år fra stopalderen.** Stopper man ved 60, er første bånd
  60–64. Båndene følger stopalderen (030), også når den ændres eller trækkes i grafen (025).
- Q: Hvor mange bånd? → A: Bånd på fem år op til 85 og et sidste bånd "85+" til planens slutning.
  Stop ved 60 giver seks skydere (60–64, 65–69, 70–74, 75–79, 80–84, 85+), stop ved 67 giver fem
  (67–71, 72–76, 77–81, 82–84, 85+). Et bånd før 85, der ville være kortere end tre år, slås sammen
  med det foregående: stop ved 64 giver 64–68, 69–73, 74–78, 79–84 og 85+ (rettet under
  implementeringen; "kortere end ét år" gav et bånd på ét år, 84–84). (Tilføjet efter "også 60–65": fem faste bånd fra 60 ville samle 80–90 i ét "80+".)
- Q: Udgangspunkt? → A: **Flad, som i dag.** 100 % i alle bånd. Ingen eksisterende beregning eller
  golden case ændrer sig, før borgeren rører skyderne.
- Q: Partner? → A: **Én profil for husstanden.** Båndene regnes i kalenderår fra det år, den første i
  husstanden stopper, og vises med begges aldre.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Mere i de første år (Priority: P1)

Borgeren åbner equalizeren under grafen og sænker de senere bånd. Hovedtallet bliver beløbet i det
første bånd, som nu er højere, og grafens linje falder i trin ved båndenes grænser.

**Acceptance Scenarios**:

1. **Given** stop ved 65, plan til 90 og en flad profil, **Then** er alle beregninger som før 033.
2. **Given** samme, **When** profilen sættes til 100/100/90/80/70, **Then** er beløbet i 70–74
   lig beløbet i 65–69, i 75–79 90 % af det, i 80–84 80 % og fra 85 70 %, alt i dagens kroner.
3. **Given** en profil, der ikke stiger, **Then** er beløbet i første bånd mindst lige så højt som
   det flade beløb. (Summen af nutidsværdierne er ikke nødvendigvis den samme: en mindre buffer
   giver mindre kapitalindkomst og kan ændre ældrechecken.)
4. **Given** en hvilken som helst profil, **Then** er bufferen aldrig negativ, og intet år låner af
   senere udbetalinger (010). Kommer pengene sent, stiger beløbet i trin som i dag, men i forhold til
   profilen: forholdet mellem båndene holdes, og hele forløbet løftes.
5. **Given** stop ved 60, **Then** er der seks skydere, og den første hedder 60–64.
6. **When** stopalderen flyttes fra 65 til 62, **Then** flytter båndene med, og skydernes procenter
   beholdes i samme rækkefølge.

### User Story 2 - Den bedste plan med profilen (Priority: P1)

Optimeringen (007, 007b) maksimerer beløbet i det første bånd med borgerens profil, i stedet for det
flade beløb.

**Acceptance Scenarios**:

1. **Given** en faldende profil, **Then** finder den bedste plan det højeste beløb i første bånd,
   hvor alle senere bånd holder deres procent.
2. **When** borgeren ændrer profilen, **Then** regnes beløbene med det samme for den viste plan, og
   knappen "Find bedste plan med denne fordeling" vises. **When** borgeren trykker på den, **Then**
   søges den bedste plan fra borgerens egen plan med den nye profil. "Brug min egen plan" er stadig
   borgerens egen plan. (Først søgte vi automatisk ved hver ændring; det var uroligt, og det var
   uklart, hvad man skulle gøre.)
2. **Given** en flad profil, **Then** er den bedste plan den samme som før 033.

### User Story 3 - Forstå og gemme profilen (Priority: P2)

**Acceptance Scenarios**:

1. **Given** en faldende profil, **Then** står der under hovedtallet, hvad beløbet falder til og
   hvornår, fx "Falder til 21.700 kr. fra 75 og 16.900 kr. fra 85."
2. **Given** forklaringen ("Hvordan fremkommer tallet?", 020), **Then** nævner den profilen som
   borgerens eget valg.
3. **Given** en gemt fil (024) eller en udskrift (020d), **Then** er profilen med.
4. **Given** en partner, **Then** vises båndene med begges aldre, fx "65–69 (partner 63–67)".

## Requirements *(mandatory)*

- **FR-001**: Kernen MUST tage en profil: en procent pr. bånd, første bånd 100 %. Uden profil er
  forløbet fladt.
- **FR-002**: Udjævningen (`jaevn.py`) MUST vægte hvert år med båndets procent, så niveauet i år t er
  c · vægt(t) i dagens kroner. Kravene fra 010 gælder uændret: ingen lån, ingen negativ buffer, og
  bufferen ender i 0.
- **FR-003**: Båndene MUST regnes fra stopalderen (`stopalder`, 030), i bånd på fem år op til 85 og
  et sidste bånd til planens slutning. Arbejdsår før stopalderen udjævnes som i dag.
- **FR-004**: Optimeringen MUST bruge beløbet i første bånd (niveauet c) som mål. Ved uafgjort
  gælder 007's regel om det flade forløb, målt i forhold til profilen.
- **FR-005**: Skyderne MUST gå fra 50 % til 100 % i trin på 5 procentpoint og må ikke stige fra bånd
  til bånd. Første bånd er låst på 100 %.
- **FR-006**: Equalizeren MUST kunne betjenes med tastatur og skærmlæser (WCAG 2.2 AA). Hver
  skyder har et navn med båndets aldre og sin værdi i procent og kr. pr. måned.
- **FR-007**: Profilen er kun en fordeling over tid. Den MUST NOT ændre udbetalingerne fra
  ordningerne, lønnen eller folkepensionens grundbeløb. Skat, pensionstillæg og ældrecheck kan ændre
  sig, men kun gennem bufferen: bruges mere i de første år, bliver bufferen mindre, og dermed formuen
  og kapitalindkomsten. (Rettet under implementeringen: første udkast sagde, at ydelserne ikke
  ændrer sig.)
- **FR-008**: Profilen MUST gemmes (024), med i udskriften (020d) og i forudsætningerne ved
  hovedtallet, når den ikke er flad.

### Uden for denne feature

- En foruddefineret faldende profil (fx "Typisk forbrug") med kilde. Kræver en kilde om forbrug
  efter pensionering (Princip III) og kan komme senere.
- Profil i procent af nettolønnen.
- Stigende profiler (fx til plejehjem). FR-005 tillader kun fald.

## Success Criteria *(mandatory)*

- **SC-001**: Golden cases for profilen i `tests/golden/` (scenarie 2–5) og egenskabstest: bufferen
  er aldrig negativ og ender i 0 for vilkårlige profiler.
- **SC-002**: Alle eksisterende tests er uændrede med en flad profil.
- **SC-003**: Browsertest af equalizeren med tastatur og axe-core uden fejl, og hele suiten er grøn.
