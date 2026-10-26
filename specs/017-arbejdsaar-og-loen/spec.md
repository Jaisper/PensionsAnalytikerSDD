# Feature Specification: Arbejdsår og løn – hvornår kan jeg stoppe?

**Feature Branch**: `017-arbejdsaar-og-loen`

**Created**: 2026-10-26

**Status**: Draft – afventer clarify

**Input**: Idéliste punkt 1 ("Hvornår kan jeg stoppe?") og punkt 3 ("Arbejde ved siden af
pensionen"). Featuren er også en forudsætning for punkt 2 ("Hvor skal næste krone hen?") og for
013 US3 (se [docs/roadmap.md](../../docs/roadmap.md)).

**Grundlag**:
- 013: opsparing uden for pension. Den kan i dag først bruges fra første udbetalingsår.
- 007: "Find bedste plan" og det faste beløb (`fast_niveau`).
- 010: udjævning uden lån.
- 012: partnerens arbejdsindkomst indgår ikke i pensionstillægget (allerede i kernen).
- Kernen kender ikke borgerens løn. Tabellen begynder ved første udbetaling, og skatten i
  arbejdsårene regnes ikke (hul 1 fra 013's clarify).

## Problem

Det oftest stillede spørgsmål er "Hvornår kan jeg stoppe med at arbejde?". Det kan værktøjet ikke
besvare i dag. Det kender hverken lønnen, eller hvornår den stopper. Årene mellem sidste løn og
første pensionsudbetaling bliver derfor ikke finansieret i beregningen.

## Clarifications

### Session 2026-10-26

- [NEEDS CLARIFICATION: Hvordan angives lønnen: én årsløn i dag, der følger antagelsen om
  lønvækst, eller et beløb pr. år? Forslag: én årsløn i dag + lønvækst.]
- [NEEDS CLARIFICATION: Stopper man på én gang, eller skal nedtrapning med i første omgang
  (fx 60 % løn fra 62 til 65 år)? Forslag: én stopalder i P1, nedtrapning i US4.]
- [NEEDS CLARIFICATION: Skal "Hvornår kan jeg stoppe?" kun flytte stopalderen med den nuværende
  udbetalingsplan, eller også flytte pensionernes udbetalingsstart (som 007)? Forslag: først kun
  stopalderen. Derefter kan man trykke "Find bedste plan" for den fundne alder.]
- [NEEDS CLARIFICATION: Det nye seniorfradrag fra 2026, de sidste fem år før
  folkepensionsalderen. Hvilken paragraf, og hvilken sats? Kun BDO er fundet som kilde.]
- [NEEDS CLARIFICATION: Skal fradraget for pensionsindbetalinger i arbejdsårene med her (korrekt
  skat i arbejdsårene), eller vente til "Hvor skal næste krone hen?"? Forslag: med her, fordi
  ellers er skatten i arbejdsårene forkert.]

## Lovgrundlag (Princip III)

| Kobling | Kilde | Status |
|---|---|---|
| Løn er personlig indkomst efter AM-bidrag (8 %) | AMBL; registret `skat.am_bidrag` | verificeret (i registret) |
| Beskæftigelsesfradrag 12,75 % af lønnen, højst 63.300 kr. (2026) | Ligningsloven § 9 J; tax.dk | uverificeret |
| Jobfradrag 4,5 % af lønnen over 235.200 kr., højst 3.100 kr. (2026) | Ligningsloven § 9 K; tax.dk | uverificeret |
| Seniorfradrag de sidste fem år før folkepensionsalderen (fra 2026) | ? (BDO) | uverificeret |
| Ligningsmæssige fradrag nedsætter grundlaget for kommune- og kirkeskat, ikke bundskat eller topskat | PSL § 6 og § 8; KSL | uverificeret |
| Indbetaling til ratepension og livsvarig pension fradrages i den personlige indkomst | PBL §§ 16 og 18 | uverificeret |
| En folkepensionists egen arbejdsindkomst indgår ikke i pensionstillæggets indtægtsgrundlag. Grundbeløbet påvirkes ikke af indkomst | LSP § 29, stk. 1, nr. 7; borger.dk; Ældre Sagen | uverificeret (borger.dk og Ældre Sagen er enige) |
| Arbejdsindkomst over 122.004 kr. tæller i den personlige tillægsprocent (ældrecheck, mediecheck) | LSP; Ældre Sagen | uverificeret |
| Partnerens arbejdsindkomst indgår ikke i pensionstillæggets indtægtsgrundlag | LSP § 29, stk. 1, nr. 10 | verificeret (i kernen) |
| Opsat folkepension kræver mindst 750 timers arbejde om året | LSP § 15 a | verificeret (advarsel i kernen) |
| Seniorpension, efterløn og tidlig pension modregner arbejdsindkomst | – | uden for scope |

Nye satser SKAL ind i regelregistret med kilde og status, før der merges (Princip II):
beskæftigelsesfradrag, jobfradrag, seniorfradrag og tillægsprocentens grænse for arbejdsindkomst.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Angiv din løn, og hvornår du stopper (Priority: P1)

I trinnet "Om dig" kan borgeren angive sin årsløn før skat og den alder, hvor lønnen stopper
("Jeg stopper med at arbejde som …-årig"). Begge felter er valgfrie.

**Acceptance Scenarios**:

1. **Given** ingen løn, **Then** er resultatet det samme som før 017 (alle golden cases uændrede).
2. **Given** løn og en stopalder, **Then** vises arbejdsårene i grafen med løn efter skat, og den
   faste udbetaling begynder ved stopalderen.
3. **Given** løn i arbejdsårene, **Then** regnes skatten med AM-bidrag, beskæftigelsesfradrag og
   jobfradrag. Kapitalindkomst fra opsparingen beskattes oven på lønnen.

---

### User Story 2 - Opsparingen bygger bro (Priority: P1)

Fra stopalderen er der ingen løn. Det faste beløb skal finansieres af opsparingen uden for pension
(013) og de ordninger, der kan udbetales. Det faste beløb udjævnes fra stopalderen og ikke fra
første pensionsudbetaling.

**Acceptance Scenarios**:

1. **Given** stop som 62-årig, første pension som 65-årig og 300.000 kr. i banken, **Then**
   bruges banken i årene 62–64, og det faste beløb er aldrig finansieret af lån (010).
2. **Given** stop før første udbetaling og ingen opsparing, **Then** er det faste beløb 0 i
   årene uden indtægt, og der vises en tydelig advarsel om hullet.

---

### User Story 3 - "Hvornår kan jeg stoppe?" (Priority: P1)

Borgeren skriver sit ønskede beløb om måneden efter skat i dagens kroner. Værktøjet
finder den tidligste stopalder, hvor det faste beløb når ønsket, med den nuværende udbetalingsplan.

**Acceptance Scenarios**:

1. **Given** et ønske, der kan nås, **Then** vises den tidligste alder, og det faste beløb ved den
   alder.
2. **Given** et ønske, der ikke kan nås, selv ved folkepensionsalderen, **Then** siges det, og det
   højeste mulige faste beløb vises.
3. **Then** oplyses søgningens omfang (alle aldre fra i dag til folkepensionsalderen er afprøvet,
   Princip V).

---

### User Story 4 - Arbejd ved siden af pensionen (Priority: P2)

Borgeren kan angive løn efter stopalderen eller efter folkepensionsalderen (deltid), fx 120.000 kr.
om året fra 67 til 70 år.

**Acceptance Scenarios**:

1. **Given** en folkepensionist med løn, **Then** nedsættes pensionstillægget ikke af lønnen, og
   lønnen beskattes sammen med pensionen.
2. **Given** løn over grænsen for den personlige tillægsprocent, **Then** falder ældrechecken
   tilsvarende.
3. **Given** opsat folkepension og under 750 timer, **Then** vises advarslen som i dag.

---

### User Story 5 - Partnerens løn (Priority: P2)

Med en fuld partnerprofil (012) kan partnerens løn og stopalder angives på samme måde.
Partnerens løn påvirker kun partnerens egen skat og de overførsler mellem ægtefæller, loven
tillader (personfradrag, PSL § 10, stk. 3).

### Edge Cases

- **Stopalder efter folkepensionsalderen**: Tilladt (arbejde ved siden af folkepensionen).
- **Stopalder i dag eller tidligere**: Ingen løn regnes.
- **Løn, men ingen stopalder**: Lønnen stopper ved folkepensionsalderen (forslag, afklares).
- **Høj løn**: Mellemskat og topskat i arbejdsårene. Skatteloftet gælder som i dag.

## Requirements *(mandatory)*

- **FR-001**: Profilen MUST kunne have en løn (årsløn i dag) og en stopalder. Uden løn er
  beregningen uændret.
- **FR-002**: Tabellen MUST begynde i dag, når der er løn. Arbejdsårene har deres egne rækker med
  løn, skat og nettoindkomst.
- **FR-003**: Skatten af lønnen MUST regnes med AM-bidrag, beskæftigelsesfradrag, jobfradrag (og
  evt. seniorfradrag). Ligningsmæssige fradrag nedsætter kun grundlaget for kommune- og kirkeskat.
- **FR-004**: Den faste udbetaling MUST udjævnes fra stopalderen. Arbejdsårene indgår ikke i
  udjævningen.
- **FR-005**: Opsparing i planen (013) MUST kunne bruges fra stopalderen.
- **FR-006**: Egen arbejdsindkomst MUST ikke indgå i pensionstillæggets indtægtsgrundlag, men
  over grænsen i den personlige tillægsprocent.
- **FR-007**: Den omvendte beregning (US3) MUST være deterministisk og afprøve alle aldre i
  intervallet. Den vises med søgningens omfang (Princip V).
- **FR-008**: Satserne MUST ligge i regelregistret med kilde og status (Princip II).
- **FR-009**: Persondata forlader ikke browseren (Princip VII og XI).
- **FR-010**: Princip X: felterne forklares i konteksten, axe 0 fejl og ingen vandret scroll ved
  360 px.

### Key Entities

- **Arbejdsindkomst**: årsløn i dag, stopalder og evt. løn efter stop (deltid) med periode.
- **Ønsket beløb**: kr. om måneden efter skat i dagens kroner (US3).

## Success Criteria *(mandatory)*

- **SC-001**: Uden løn er alle eksisterende tests grønne uden ændrede facit-tal.
- **SC-002**: Golden cases med kildehenvisning for skatten af løn: under og over
  beskæftigelsesfradragets loft, med og uden jobfradrag, og med mellemskat.
- **SC-003**: Golden case for broen: stop før første udbetaling, finansieret af banken (US2).
- **SC-004**: Golden case for en folkepensionist med løn: pensionstillægget er uændret, og
  tillægsprocenten falder over grænsen.
- **SC-005**: Samme resultat i Pyodide og CPython.
- **SC-006**: Den omvendte beregning svarer på under 5 s i browseren for en typisk profil.

## Uden for scope

- Seniorpension, efterløn og tidlig pension (se roadmap: "Tungere, senere").
- Sammenligning af, hvor en ekstra indbetaling gør mest gavn (punkt 2, egen feature).
- Løn pr. år og karriereforløb ud over én løn og én deltidsperiode.

## Kilder (2026-10-26)

- borger.dk, "Grundbeløb og pensionstillæg" og "Når du får folkepension"
- Ældre Sagen, "Arbejd og få samtidig fuld folkepension" og "Folkepension 2026"
- tax.dk, beskæftigelsesfradrag (Ligningsloven § 9 J); oversigt over beløbsgrænser 2026 (themis.dk)
- BDO, "Det nye beskæftigelsesfradrag for seniorer" (2025)
