# Feature Specification: Planens slutning og penge tilbage

**Feature Branch**: `040-planens-slutning`

**Created**: 2026-11-26

**Status**: Afklaret 2026-11-26 (produktejer), klar til implementering

**Input**: "kan vi ikke lave så man kan udfylde den alder hvortil man vil have udbetalt pension (f.eks 90 år) så
mulighed for både start og slut år. Og dertil kunne angive et beløb man evt vil have sparet op til udløb. F.eks
250000 sparet op når man så bliver 90 (man kunne jo leve et år eller to mere..)."

**Grundlag**:
- 019 (levetid): kernen har `plan_slut_alder`, adskilt fra livrentens beregningshorisont. I dag bruges den
  kun af usikkerhedstabellens rækker "Planen rækker til 85/95 år".
- 015 US2 ("Bevar X til arvinger"), besluttet 2026-10-27: udjævningen ender med X i dagens kroner i stedet for
  0, som en ny randbetingelse i 010-algoritmen. Det faste beløb falder tilsvarende.
- 010 (ingen lån), 009 (bufferens fastpunkt: skat af afkast og formue), 037 (partnerne hver for sig).
- Princip III: slutalderen og beløbet er borgerens egne valg, ikke lovregler. Der kommer ingen nye satser.
- Starten findes allerede: stopalder og udbetalingsstart på tidslinjen.

## Clarifications

### Session 2026-11-26

- Q: Par? → A: **Slutalder og beløb pr. person (produktejer)**, som 037. "Samlet" lægger beløbene sammen.
- Q: Hvor kan det indtastes? → A: **Både i guiden (trinnet "Dine forventninger") og under "Prøv andre
  forudsætninger" (produktejer).**
- Q: Vises prisen? → A: **Ja (produktejer):** "Det koster ca. X kr. om måneden at have Y kr. tilbage."
- Beløbet er i dagens kroner og står i opsparingen uden for pension (bufferen). Det er derfor efter skat.
  Opsparing, borgeren har valgt ikke at bruge (urørt), kommer oveni.
- Livrentens ydelse ændres ikke af slutalderen (som 019). Folkepension, ATP og livrente fortsætter efter planens
  slutning; linjen under usikkerhedstabellen viser det.
- Levetidsrækkerne i usikkerhedstabellen bliver relative: planens slutning − 5 og + 5 år, for hver person ud fra
  egen slutalder.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Hvor længe skal pengene række (Priority: P1)

1. **Given** borgeren skriver 95 år, **Then** udjævnes opsparingen til og med 95 år, og det faste beløb falder.
2. **Given** feltet er tomt, **Then** regnes der som i dag (90 år), og intet ændres.
3. **Given** slutalderen er før sidste rate, **Then** forlænges planen til sidste rate (som 019).
4. **Given** en alder uden for 70–110 eller ikke efter i dag, **Then** fejl ved feltet.

### User Story 2 - Penge tilbage ved planens slutning (Priority: P1)

1. **Given** 250.000 kr., **Then** ender opsparingen i planen på 250.000 kr. i dagens kroner ved planens
   slutning. Bufferen er aldrig negativ, og det faste beløb falder aldrig (010).
2. **Given** 0 eller tomt, **Then** er alt som i dag.
3. **Given** et beløb, opsparingen ikke kan nå, **Then** bruges der intet af bufferen, og en advarsel siger,
   hvor meget der kan stå tilbage.
4. **Given** et negativt beløb, **Then** fejl ved feltet.
5. Skat af afkastet og ældrechecks formuegrænse regnes med (bufferens fastpunkt, 009).

### User Story 3 - Prisen (Priority: P2)

1. **Given** et beløb > 0, **Then** står der ved hovedtallet: "At have 250.000 kr. tilbage som 90-årig koster
   ca. 1.100 kr. om måneden." Tallet er forskellen til samme beregning med 0 kr.

### User Story 4 - Par (Priority: P1)

1. Hver person har egen slutalder og eget beløb. Mangler partnerens (gemt før 040), bruges 90 år og 0 kr.
2. Under "Prøv andre forudsætninger" ændres den viste persons værdier.

## Requirements

- **FR-001**: `Antagelser.rest_ved_plan_slut` (kr., dagens kroner, standard 0). Udjævningen ender med bufferen
  på dette beløb ved sidste række.
- **FR-002**: Guidens trin 5 og resultatsiden har felterne "Hvor længe skal pengene række?" og "Penge tilbage,
  når planen slutter".
- **FR-003**: Partnerens værdier ligger i `person.partner.antagelser` (037).
- **FR-004**: Prisen beregnes kun, når beløbet er > 0.

## Success Criteria

- **SC-001**: Golden cases regnet i hånden for randbetingelsen (rente 0, inflation 0).
- **SC-002**: Med 0 kr. og uden slutalder er alle eksisterende tal uændrede (hele suiten grøn).
