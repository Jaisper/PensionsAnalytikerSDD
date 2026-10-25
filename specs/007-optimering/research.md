# Research: Find bedste plan

## R001 Målet: fast beløb hele perioden, ikke hovedtallet (T003)

Første version optimerede hovedtallet, dvs. det jævne niveau efter det sidste engangsbeløb. På
en profil med fire ordninger flyttede den aldersopsparingen fra 67 til 78 år. Hovedtallet steg,
men beløbet de første 11 år faldt. Det er præcis det skæve forløb, legacy advarer imod.

Målet er nu det laveste jævne beløb fra udgangspunktets første udbetaling, hvor år uden
udbetaling tæller som 0. Engangsbeløbet blev derefter i bufferen tidligt, og det faste beløb
steg fra 17.375 til 18.062 kr./md. Testen
`test_skubber_ikke_engangsbeloeb_sent_for_at_hoeje_hovedtallet` sikrer det.

## R002 Samme forslag i browser og CPython (T006)

Pyodide og CPython valgte først forskellige planer: 20.700 mod 20.800 kr., efter 756 mod 935
evalueringer. Der var to årsager:
1. **Rangering på uafrundede tal.** Rettet ved at runde alle dele af rangeringen til hele kroner.
2. **Bufferens nulpunkt.** Bufferen ender i 0 i sidste år, og `buffer < 0` blev afgjort af
   regnestøj (±1e-9). Python 3.12's `sum` er mere præcis end 3.11's, og WebAssemblys libm
   afviger fra Windows'. Under 1 kr. tæller nu som 0, både i værnet og i kernens advarsel
   `JAEVN_FORUDSAETTER_SENERE_UDBETALINGER`, som kunne slå forskelligt ud af samme grund.

Efter rettelsen er planen identisk, og begge sider bruger 889 evalueringer.

## R003 Hastighed

| | CPython | Browser (Pyodide) |
|---|---|---|
| 4 ordninger (syntetisk) | 0,8 s (cirka 600–900 evalueringer) | 3,3 s |
| Rigtig rapport (5 ordninger) | | 3,5 s |

Koordinatsøgningen stopper, før budgettet på 1.500 evalueringer er brugt. SC-003 (under 10 s)
er opfyldt.
