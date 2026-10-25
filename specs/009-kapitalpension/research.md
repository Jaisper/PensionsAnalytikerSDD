# Research: Kapitalpensionens muligheder

Alle opslag er foretaget 2026-10-25. Påstandene kommer fra produktejeren (citat fra en bankartikel),
og hver påstand er efterprøvet.

| Påstand | Resultat | Kilde |
|---|---|---|
| Kan omlægges til rate eller livrente, så længe afgiften ikke er betalt | **Holder.** Overførsel fra kapitalforsikring eller opsparing til en ordning med løbende udbetalinger eller en rateordning behandles ikke som ud- og indbetaling | PBL § 41, stk. 1, nr. 4 og 6 (danskelove.dk) |
| Udbetaling i mindre portioner i højst 20 år, resten under PAL | **Holder.** PBL § 26 giver ret til at få udbetalt en del af en kapitalpension. Seneste udbetaling er 20 år efter pensionsudbetalingsalderen (15 år før 2018). "Kun én gang" gælder kun en lavere alder godkendt af Skatterådet | JV C.A.10.2.5.4.1 (info.skat.dk), PBL § 12, stk. 1, nr. 3, § 25, stk. 1, nr. 7, og § 26 |
| Ved omlægning skifter beskatningen fra 40 % afgift til marginalskat, og det giver kun gevinst ved marginalskat under 40 % | **Rigtig, men ufuldstændig.** Ratepension indgår i indtægtsgrundlaget, så modregningen i pensionstillægget (30,9 %/32 %) kommer oveni. For en folkepensionist med tillæg er den effektive sats cirka 68 %. Kernen afgør det for den enkelte | Lov om social pension § 29 og § 49 (registret) |
| Kapitalpension modregnes ikke i pensionstillægget | **Holder for selve udbetalingen.** Den er afgiftsbelagt og ikke personlig indkomst. **Men:** står beløbet bagefter i banken, er afkastet kapitalindkomst (indgår i indtægtsgrundlaget, § 29), og beløbet er likvid formue (ældrecheck, § 72 d, stk. 2). Det var hidtil kun en advarsel. Nu modelleres det | Lov om social pension §§ 29 og 72 d |
| Afgift betalt tidligere (37,3 % i 2013) | **Holder.** Omlægning i 2013 (og 2014) mod 37,3 % afgift, hvorefter udbetalingen er skattefri | Skatteministeriet, notat 5.10.2013. Industriens Pension, årsrapport 2013. lex.dk |

## Satser verificeret til registret

- **PAL**: 15,3 % af det skattepligtige afkast. Kilde: pensionsafkastbeskatningsloven § 2.
- **Bundfradrag** for positiv nettokapitalindkomst i mellemskattegrundlaget for ugifte: 55.000 kr.
  (2026, PSL § 7, stk. 1). **Skatteloft** for positiv nettokapitalindkomst: 42,0 % (PSL § 19,
  stk. 2). Kilde: Skatteministeriets satsoversigt for personskatteloven (svmn.dk).

## Valg

- **Portioner beregnes med § 11 A-formlen** (restværdi divideret med resterende år). Det svarer
  til ratepensionens rater, og legacy brugte en annuitet ("kapital_rate").
- **Bufferens afkast før skat** er afkastet efter PAL divideret med (1 − PAL). Antagelsen er, at
  bufferen investeres som pensionen. Det erstatter legacys og 001's faste 27 %.
- **Kapitalindkomst som marginal skat**: skat(PI + KI) − skat(PI). Hele merskatten tilskrives
  bufferen. Det svarer til, at kapitalindkomsten "ligger øverst", hvilket er praksis ved
  skatteloftet for kapitalindkomst.

## R002 Fastpunktet: iterationer og hastighed

Bufferens kapitalindkomst og formue afhænger af den jævne udbetaling og omvendt.

**Første iteration** (KI = 0) overvurderer bufferen. Derefter konvergerer det monotont. Stop, når:
- den jævne udbetaling ændrer sig mindre end 1 kr./md. i hvert år, eller
- kapitalindkomsten ændrer sig mindre end 12 kr./år, og intet år skifter side af ældrechecks
  formuegrænse.

**Kold start** tager 3–6 iterationer (SC-002 er justeret fra 3 til 6). I optimeringen bruges den
forrige kandidat som startgæt: 1 iteration for cirka 1/3 af kandidaterne.

| | CPython | Browser |
|---|---|---|
| Én beregning, 4 ordninger, kold | 7 ms (før 009: 2 ms) | |
| Find bedste plan, syntetisk (4 ordninger) | 2,3 s | 7,6 s (SC-003 < 10 s) |
| Find bedste plan, rigtig rapport (5 ordninger) | | 13,1 s |

**Tiltag:**
- Registret husker værdier pr. år.
- Optimeringen bruger et startgæt for bufferen.
- Udbetalingsformen afprøves på et groft gitter af år (2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30),
  og borgeren finjusterer på tidslinjen.

**Afvist:**
- Et lavere budget, fordi kandidaterne ud over 1.000 er billige.
- En tidsgrænse, fordi den giver forskellige svar på hurtige og langsomme maskiner (Princip I).

Over 10 s har brugeren i stedet "Afbryd".

## R003 Konsekvens for optimeringen

Med en realistisk buffer koster opsparing skat og pensionstillæg. En sen ratepension er derfor
ikke længere klart dårlig: én profil gik fra en tydelig forbedring til cirka 70 kr./md. fra det
bedste. Testen bruger nu en profil, der er tydeligt dårlig ("alt sent", cirka 2.000 kr./md.).
