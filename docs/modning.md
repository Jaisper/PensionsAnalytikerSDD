# Modning af idéerne

**Dato**: 2026-10-27. Hver idé fra roadmappen har fået et spec-udkast med lovgrundlag (første
research), åbne spørgsmål med forslag og afhængigheder. Intet er bygget. Beslutningerne træffes af
projektejeren, før der planlægges.

## Overblik

| Spec | Idé | Modenhed | Største åbne spørgsmål | Forudsætter | Størrelse |
|---|---|---|---|---|---|
| [013b](../specs/013b-frit-depot-ask/spec.md) | Frit depot og aktiesparekonto | Høj: lovgrundlaget verificeret i 013 | Trækrækkefølgen og løbende ASK-indskud | 013, 017 | Mellem |
| [021](../specs/021-naeste-krone/spec.md) | Hvor skal næste krone hen? | Mellem | Årligt eller engangs; privat eller arbejdsgiver; afdrag før 014 | 017, 013b | Lille–mellem |
| [022](../specs/022-efterladte/spec.md) | Hvad hvis min partner dør? | Mellem: flere regler kun fra sekundære kilder | Ægtefælledækning på livrenter; afgift ved død | 012, 018, 019 | Mellem |
| [023](../specs/023-afkast-pr-aar/spec.md) | Afkast pr. år og "dårlige år først" | Mellem | Hvor dårlige "dårlige år" er (kilde) | – | Mellem |
| [024](../specs/024-gem-lokalt/spec.md) | Gem og genindlæs lokalt | Høj | Påkrævet adgangskode | – | Lille |
| [014](../specs/014-bolig/spec.md) | Bolig og friværdi | Lav–mellem: grundskyld og indefrysning mangler | Kommunale grundskyldspromiller; indefrysning | 013, 013b | Stor (opdelt 014a–d) |
| [015](../specs/015-arv/spec.md) | Arv modtaget og givet | Mellem | Arv i hovedtallet (forslag: nej); "bevar X" i udjævningen | 013, 022 | Mellem |
| [016](../specs/016-monte-carlo/spec.md) | Monte Carlo | Lav | Porteføljen; ydelse i browseren | 023 | Stor |

## Tungere idéer (endnu ikke spec)

- **Efterløn, seniorpension og tidlig pension.** Hver ordning har sine egne regler for modregning,
  og efterlønnen modregner pensionsformue. De skal hver have en spec. Det første spørgsmål er, hvor
  mange brugere der har dem. Værdien er størst for 55–64-årige.
- **Omkostninger (ÅOK).** Afhænger af, om PensionsInfo-rapporten har ÅOK pr. ordning i en form,
  parseren kan læse sikkert. Det første skridt er at undersøge rapporten (syntetisk og rigtig,
  lokalt).
- **Forsikringsoverblik.** Kun aflæsning og visning, ingen beregning. Samme første skridt som ÅOK.
  Advarslen om dækninger, der ophører ved udbetaling, kræver dækningernes ophørsalder i rapporten.

## Anbefalet rækkefølge

1. **024 Gem lokalt.** Lille, uafhængig, og borgerne mærker den med det samme.
2. **013b Frit depot og ASK.** Lovgrundlaget er klar. Forudsætning for 021.
3. **021 Næste krone.** Høj værdi; genbruger scenariemønstret fra 018.
4. **023 Afkast pr. år.** Kernearbejde, der åbner for 016.
5. **022 Efterladte.** Kræver mere verifikation af reglerne ved død.
6. **014a–b Boligskat og lån**, derefter **015 Arv** og **016 Monte Carlo**.

## Besluttet 2026-10-27

Alle forslag er godkendt som foreslået, også rækkefølgen. Hver spec får clarify med primærkilder for
de satser, der kun er sekundært verificeret, før den planlægges og bygges.
