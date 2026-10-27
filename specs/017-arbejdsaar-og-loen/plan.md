# Implementation Plan: 017 Arbejdsår og løn

**Branch**: `017-loen` | **Spec**: [spec.md](spec.md) | **Dato**: 2026-10-27

## Tekniske beslutninger

### Model

`Pensionsprofil.loen: Loen | None`. Uden løn er beregningen uændret (SC-001).

```python
Loen(aarlig, stop_alder=None, deltid_aarlig=0.0, deltid_til_alder=None)
```

- `aarlig` er årslønnen før skat i dag, inklusive borgerens pensionsindbetaling.
- `stop_alder` er det første år uden løn. `None` betyder folkepensionsalderen.
- `deltid_aarlig` og `deltid_til_alder` er løn efter stop (US4), til og med året før
  `deltid_til_alder`.

**Lønnen reguleres med satsreguleringen** (konstant købekraft, som ATP), ikke med
`Antagelser.loenvaekst`. Afvigelse fra clarify: `loenvaekst` er 0 som standard og bruges til
pensionsindbetalinger. Med den ville lønnen falde i købekraft hvert år. En løn i dagens kroner er
det, borgeren forventer.

### Fremskrivning

- **Med løn begynder tabellen i dag.** Arbejdsårene får rækker med løn, skat og nettoindkomst.
- **Udjævningen begynder ved stopalderen**, eller ved første udbetaling, hvis den kommer senere.
  Den nye `Fremskrivning.jaevn_fra_alder` angiver året. Rækkerne før indgår ikke i udjævningen.
  - I disse år er det faste beløb lig nettoindkomsten.
  - Opsparing i planen og engangsbeløb, der falder før stopalderen, samles i bufferen og vokser
    med renten. Det samlede beløb indsættes ved stopalderen. Afkastet beskattes i arbejdsåret
    sammen med lønnen.
- **Skatten af lønnen**:
  - AM-bidrag af hele lønnen (`skat.am_bidrag`).
  - Pensionsindbetalinger til ratepension og livsvarig pension fradrages i den personlige
    indkomst (forenkling: regnet som arbejdsgiverordning).
  - Ligningsmæssige fradrag (beskæftigelsesfradrag, jobfradrag og seniorfradrag) nedsætter kun
    grundlaget for kommune- og kirkeskat.
  - `beregn_skat` får parameteren `ligningsmaessige_fradrag`. Personfradraget regnes for bundskat
    og kommune-/kirkeskat hver for sig.
- **Pensionsindbetalinger stopper ved stopalderen**, når der er løn. Uden løn er det som i dag.
- **Ydelser**:
  - Egen løn indgår ikke i pensionstillæggets indtægtsgrundlag (L 117).
  - Egen løn over bundfradraget (`tp.arbejdsindkomst.bundfradrag`) indgår i grundlaget for den
    personlige tillægsprocent.
- **Advarsel `INDKOMSTHUL`**: år efter stopalderen, hvor det faste beløb er 0.

### Hovedtal, optimering og graf

- Hovedtallet og "Find bedste plan" (`vindue`, `fast_niveau`, `slutniveau`) bruger årene fra
  `jaevn_fra_alder`.
- Grafen viser løn som en ny serie ("Løn efter skat"). Linjen for det faste beløb begynder ved
  `jaevn_fra_alder`.

### "Hvornår kan jeg stoppe?" (US3)

`app.stopalder(guide_json, idag, maaned)` afprøver alle stopaldre fra i dag til
folkepensionsalderen med den nuværende plan. Den giver den tidligste alder, hvor hovedtallet når
ønsket, eller det højeste mulige beløb. Antallet af afprøvede aldre vises (Princip V).

### Registret

Nye poster (verificeret i clarify):
- `skat.beskaeftigelsesfradrag.sats` og `.maks`
- `skat.jobfradrag.sats`, `.graense` og `.maks`
- `skat.seniorfradrag.sats`, `.maks` og `.aar_foer_fp`
- `tp.arbejdsindkomst.bundfradrag`

Kilden for `skat.am_bidrag` opdateres: posten bruges nu til løn.

**Forenklingsregistret**:
- `ingen_loen` bliver `markeret` og gælder kun, når der ikke er oplyst løn, og borgeren er under
  folkepensionsalderen.
- Ny: `pensionsindbetaling_som_arbejdsgiverordning` (markeret).
- `partnerens_loen_ukendt` får ny tekst.

### Brugerflade

- **Trin 1**: "Din årsløn før skat" og "Jeg stopper med at arbejde som". Under fold-ud'en
  "Arbejder du ved siden af pensionen?" ligger deltidsløn og til hvilken alder.
- **Partnertrinnet**: partnerens løn og stopalder (US5).
- **Resultatet**: et nyt kort "Løn".
  - I "Prøv andre forudsætninger" ligger "Hvornår kan jeg stoppe?": ønsket beløb, knap og svar.
  - "Brug denne alder" sætter stopalderen.
  - Uden løn står der, at lønnen skal skrives under "Dine oplysninger".

## Constitution check

- **Princip II og III**: alle satser ligger i registret med kilde. Seniorfradraget følger gældende
  lov.
- **Princip IV**: test først. Golden cases med håndregning for skatten af løn.
- **SC-001**: uden løn er alle golden cases uændrede.
