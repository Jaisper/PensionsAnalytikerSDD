# Designretning

Gælder alle features med brugerflade. Supplerer forfatningens Princip X
(Brugeroplevelse: Klarhed før Fuldstændighed).

## Inspiration: velliv.dk (layout, ikke brand)

Vi låner **layoutprincipper** fra velliv.dk (besøgt 2026-10-24), ikke deres
identitet. Velliv er et rigtigt pensionsselskab, og løsningen må aldrig kunne
forveksles med dem (forfatningen og almindelig redelighed). Vi bruger derfor ikke
deres navn, logo, illustrationer, fotos, tekster eller deres grøn/mint-farvepalet.

| Mønster hos velliv.dk | Sådan bruger vi det |
|---|---|
| Hvid, fast topbjælke med få menupunkter og én mørk primærknap til højre | Topbjælke med produktnavn, 2–3 menupunkter og én primær handling ("Ny beregning") |
| Todelt hero: stor, fed overskrift på mørk flade til venstre, billede til højre med skrå kant | **Resultat-hero**: hovedtallet ("Du får ca. 23.400 kr. om måneden efter skat") på mørk flade til venstre, graf over tid til højre med samme skrå overgang |
| Store, runde sans-serif-overskrifter. Kort brødtekst i normal vægt | Samme hierarki. Højst 2 skriftstørrelser i brødtekst |
| Sektioner i fuld bredde med meget luft, skiftevis mørk og lys tonet baggrund | Én sektion pr. emne: Overblik → Hvad påvirker beløbet → År for år → Antagelser |
| Kortrække: ikon → kort overskrift → 2 linjers tekst → tekstlink med pil (→) | Kort for hver indkomstkilde og hver advarsel. Pil-linket åbner detaljen (progressiv afsløring) |
| Karrusel med pile-knapper | Bruges ikke. Vi viser kort i et gitter, så intet er skjult bag en pil |
| Fremhævet info-bjælke øverst | Bruges kun til ét budskab: "Information, ikke rådgivning" |

## Egen visuel identitet

- **Primær**: dyb blå-petrol (mørke flader, primærknap). **Accent**: varm sand/okker (fremhævning
  af hovedtal og "→"-links). **Baggrunde**: hvid og en lys, kølig grå tone.
- Farver defineres som tokens med lys og mørk variant. Kontrast ≥ 4,5:1 for tekst (WCAG AA).
- **Faste kildefarver i alle grafer**:
  - Folkepension (grundbeløb + tillæg)
  - ATP
  - Ratepension
  - Livsvarig
  - Ældrecheck/mediecheck
  - Skat (neutral grå)

  Samme farve betyder altid det samme.
- **Statusikoner** bruger både ikon og tekst, aldrig kun farve: ✓ verificeret, ≈ antagelse/forenkling, ! advarsel.

## Mønstre

1. **Svaret først**: Den første visning har ét tal, én sætning og ét næste skridt.
2. **Fold-ud for detaljer**: År for år, skat pr. kilde og sporing ligger bag "Se hvordan vi har regnet →".
3. **Kontekstuel forklaring**: Fagord har et (i)-ikon med en forklaring på én til to linjer og et link til kilden i regelregistret.
4. **Antagelser kan redigeres hvor de vises**: Afkast, inflation og pensionsalder har skydeknapper med øjeblikkelig genberegning.
5. **Mobil først**: Hero, kort og grafer stables ved 360 px uden vandret scroll.
