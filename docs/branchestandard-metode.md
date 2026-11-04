# Branchestandardens prognosemetode

**Formål**: Forklarer, hvordan PensionsAnalytikeren regner prognosen "som pensionsselskaberne"
(feature 035), og hvor kompleksiteten ligger. Supplerer [spec'en](../specs/035-branchestandard/spec.md)
og forklaringskataloget (emnerne `branchestandard` og `branchestandard_metode`).

**Kilde**: Forsikring & Pension, *Henstilling om pensionsprognoser – opdateret version*,
LP-information 20/20 af 7.10.2020, gældende for prognoser fra 1.1.2021, pkt. 5–7 og appendix 1–2,
med bilag 2 (taleksempel i Excel), bilag 3 (Munk 2017) og bilag 4 (Hessler 2018).

**Version tjekket**: 2026-11-04 på fogp.dk/branchesamarbejde/pension. Der er ingen nyere version.
Ændringen fra LP-info 35/19 er kun pkt. 7.2: år 1–5 og 6–10, men investeringsomkostninger for år
1–10.

Henstillingen er en **branchestandard, ikke lov**. Det skal fremgå af forklaringerne.

---

## Er det kompliceret?

Nej, ikke for PensionsAnalytikeren. Selve metoden er simpel. Kompleksiteten hos selskaberne ligger
i alt rundt om den (se nedenfor).

## Trin 1 og 2: få linjer

Henstillingens formler er en rekursion år for år (appendix 1). Implementeringen ligger i
[`src/pensionskerne/prognose.py`](../src/pensionskerne/prognose.py). Den genskaber bilag 2, arket
"Fraktilafkast Udledning årlige", med en nøjagtighed på 10⁻⁹
([`tests/golden/test_branchestandard_bilag2.py`](../tests/golden/test_branchestandard_bilag2.py)).
Kernen af den:

```python
def trin1(startdepot, tider):
    """M(tₙ) = M(tₙ₋₁)·F(tₙ₋₁)·e^{μΔt} + I(tₙ)
    V(tₙ) = F(tₙ₋₁)²·e^{2μΔt}·((V(tₙ₋₁) + M(tₙ₋₁)²)·e^{σ²Δt} − M(tₙ₋₁)²)"""
    m, v = startdepot + tider[0].indbetaling, 0.0       # depotet efter præmien ved t = 0
    ud = [Fordeling(m, v)]
    for forrige, nu in zip(tider, tider[1:]):
        f, vaekst = forrige.udbetalingsfaktor, exp(forrige.mu * forrige.laengde)
        m, v = (m * f * vaekst + nu.indbetaling,
                f * f * vaekst * vaekst * ((v + m * m) * exp(forrige.sigma ** 2 * forrige.laengde) - m * m))
        ud.append(Fordeling(m, v))
    return ud

def fraktil(fordeling, p):
    """Log-normal approksimation (Munk): exp(b·N⁻¹(p) + a − b²/2), a = ln M, b² = ln(1 + V·e^{−2a})."""
    a = log(fordeling.middel)
    b2 = log(1 + fordeling.varians * exp(-2 * a))
    return exp(sqrt(b2) * NormalDist().inv_cdf(p) + a - b2 / 2)

# trin 2: stien fra s til t er (depotₜ − præmieₜ) / (depotₛ · Fₛ) − 1
```

**Faldgruber** (de fanges af bilag 2):

- **Udbetalingsfaktoren** hører til skridtets **start**: F(tₙ₋₁) i trin 1 og Fₛ i trin 2. Bruges
  F(t), forskydes udbetalingen et år, og stien rammer forkert fra første udbetaling.
- **Startdepotet** er initialopsparingen **plus** præmien ved t = 0 (bilag 2: 1.000 + 100 = 1.100).
- **Variansen** skal regnes med det **forrige** M. Rækkefølgen i koden betyder noget.
- **Når depotet løber tør** (F = 0 ved sidste rate), kan stien ikke beregnes. Henstillingens løsning
  1: brug afkastet fra seneste periode, hvor det kunne beregnes.
- **Det forventede forløb** er e^{μ} − 1 og ikke en fraktilsti.

**Porteføljens μ og σ** kommer fra Rådet for Afkastforventninger:

- μ = ln(1 + Σ wᵢ·(afkastᵢ − investeringsomkostningᵢ))
- σ = √(wᵀSw), hvor S_ij = ρ_ij·σᵢ·σⱼ

Satserne ligger i registret som `raadet.*`. Afkastet skifter ved år 1–5, 6–10 og 11+.
Investeringsomkostningerne for år 1–10 gælder alle ti år. Fra år 11 har Rådet kun tre
aktivklasser. Aktieandelen kalibreres ved bisektion mod selskabets egen prognose (spec'en,
"Porteføljen").

## Trin 3: genbruger kernen, men med to tilpasninger

Trin 2 giver et afkast pr. år, og kernen tager allerede imod et afkast pr. år
(`Antagelser.afkast_forloeb`, 023a). Skat, pensionstillæg og udjævning kører uændret, bare tre gange
(højt, forventet og lavt afkast). To ting skal dog til (plan, fase 2):

- **Før PAL og omkostninger**: Stierne er afkast **før** PAL-skat og administrationsomkostninger.
  `afkast_forloeb` er afkast **efter** PAL. Stien omregnes derfor, og det faste gebyr trækkes i
  kroner.
- **Pr. ordning**: Stierne er **pr. ordning**, fordi porteføljen er det. `afkast_forloeb` er fælles
  for alle ordninger. Ordningen får derfor sit eget forløb (`Ordning.afkast_forloeb`).

## Hvorfor selskabernes beregninger er komplicerede

Kompleksiteten ligger i selskabernes trin 3:

- **Gennemsnitsrente**: kollektive reserver, bonus, kontributionsregler og rentegrupper
  (henstillingens appendix 3).
- **Garantier**: renteafdækning af aktiv- og passivsiden.
- **Kontoteknik**: ikke-lineære omkostninger, forsikringspriser, udjævningsmekanismer og
  levetidsgrundlag pr. kunde.
- **Data**: selskabets faktiske strategiske portefølje og livscyklusstier for alle kunder.

PensionsAnalytikeren undgår det. For gennemsnitsrente bruger den selskabets egen prognose. For
markedsrente kalibrerer den aktieandelen mod selskabets prognose.

## Det, der faktisk er svært for os

- **At ramme selskabernes tal præcist**: Omkostninger og udjævning gør, at tallene aldrig bliver helt
  de samme. Derfor er der en tolerance i sammenligningen (US4).
- **Formidling**: "Udbetaling ved lavt afkast" efter skat er skatten af 5 %-**forløbet**. Det er ikke
  5 %-fraktilen af beløbet efter skat, for skat og modregning er ikke lineære. Det er korrekt efter
  henstillingen, men skal forklares på niveau 3.
- **Vedligehold**: Rådet udsender forudsætninger to gange om året, 1. april og 1. oktober.
  Henstillingen siger 1. oktober, og F&P beslutter, om april-sættet skal bruges. Satserne skal ind i
  registret med kilde og dato. Nyeste sæt pr. 2026-11-04 er 1. halvår 2027, offentliggjort
  2.11.2026.

## Første test

Genskab henstillingens taleksempel (bilag 2). Når koden rammer de tal, sidder metoden rigtigt. Det er
gjort for trin 1–2 (SC-002).
