# Feature Specification: Partner – to profiler og en samlet oversigt

**Feature Branch**: `012-partner`

**Created**: 2026-10-25

**Status**: Draft

**Input**: "Nu til partnerdelen – ligesom i legacy skal en partner kunne føjes til, og der skal
laves både separate udbetalingsprofiler og vises en samlet oversigt."

**Grundlag**:
- Legacy: `legacy/husstand.py` og fanebladet "Partner/ægtefælle" (`legacy/static/index.html`)
- Legacy-spec US5
- Kernens partnerkobling (001: `Partner`, `indtaegtsgrundlag`, `tillaegsregel`)

## Clarifications

### Session 2026-10-25

- **Civilstand**: Gift og samlevende adskilles. Ydelserne behandler dem ens. Kun ægtefæller
  kan overføre uudnyttet personfradrag og bundfradrag for kapitalindkomst.
- **Udjævning**: Hver person har sin egen udjævning og buffer. "Samlet" viser summen (som
  legacy).
- **Partner**: En fuld profil med egne ordninger og egen PDF. Det enkle overslag ("pension og
  kapitalindkomst pr. år") bevares som hurtig vej.
- **Optimering**: Én person ad gangen. Den anden holdes fast (som legacy).

## Lovgrundlag (Princip III)

| Kobling | Kilde | Status |
|---|---|---|
| Pensionstillæg og personlig tillægsprocent på parrets samlede indtægtsgrundlag. Partnerens indkomst indgår fuldt, når partneren er pensionist | Lov om social pension § 29 (allerede i kernen og registret) | verificeret |
| Ældrecheckens formuegrænse gælder pensionistens og ægtefællens/samleverens *samlede* likvide formue, også begges buffer | Lov om social pension § 72 d, stk. 2 (registret) | verificeret |
| Ægtefæller: uudnyttet skatteværdi af personfradrag nedsætter den anden ægtefælles skatter | PSL § 10, stk. 3 | verificeret |
| Ægtefæller: ligger den ene ægtefælles positive nettokapitalindkomst under bundfradraget, forhøjes den andens bundfradrag med forskellen | PSL § 7, stk. 5 | verificeret |
| Indkomstskat er individuel | PSL | verificeret |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tilføj partneren som en fuld profil (Priority: P1)

Borgeren vælger "Gift" eller "Samlevende" og derefter "Hele din partners pension". Guiden får et
ekstra trin, "Din partners ordninger". Det har:
- upload af partnerens egen PensionsInfo-rapport (lokalt, som din egen)
- partnerens ordninger
- ATP og folkekirkemedlemskab

Partnerens fødselsdato hentes fra rapporten, når den kan.

**Acceptance Scenarios**:

1. **Given** gift og "Hele din partners pension", **When** guiden udfyldes, **Then** er der fire
   trin: Om dig, Dine ordninger, Din partners ordninger og Forventninger.
2. **Given** partnerens rapport, **When** den indlæses, **Then** udfyldes partnerens ordninger og
   fødselsdato. Dine egne ændres ikke.
3. **Given** "Et overslag", **Then** virker det som i dag (partnerens pension og kapitalindkomst
   pr. år).

---

### User Story 2 - Hver sin profil (Priority: P1)

Resultatsiden har fanerne **Dig | Partner | Samlet**. Under "Dig" og "Partner" ser hver person
sin egen side med det, den har i dag:
- hovedtal, graf, buffer og tidslinje, der kan trækkes
- kort og Find bedste plan

Ændringer for den ene person regnes igen for begge, fordi pensionstillæg og ældrecheck er
koblede.

**Acceptance Scenarios**:

1. **Given** to profiler, **When** partnerens ordning trækkes senere, **Then** ændres
   partnerens tal, og dit pensionstillæg ændres, hvis partnerens indkomst flytter sig.
2. **Given** fanen "Partner", **When** "Find bedste plan" køres, **Then** optimeres partnerens
   ordninger, mens dine holdes fast.

---

### User Story 3 - Samlet oversigt (Priority: P1)

Fanen "Samlet" viser:
- **parrets faste beløb**: summen af jeres to faste beløb, med hvert beløb for sig
- **en graf pr. kalenderår**: stablede søjler for dig og din partner i hver sin farve og den samlede
  linje
- **en samlet tidslinje**: begges ordninger og folkepension på samme kalenderakse, kun til visning
  (der redigeres under hver person)

**Acceptance Scenarios**:

1. **Given** to profiler, **Then** er "Samlet" lig dit faste beløb plus partnerens.
2. **Given** forskellige aldre, **Then** står grafen og tidslinjen på kalenderår, med begges alder i
   etiketterne.

---

### User Story 4 - Gift: skattereglerne for ægtefæller (Priority: P2)

For gifte bruges partnerens uudnyttede personfradrag og uudnyttede bundfradrag for
kapitalindkomst hos den anden. For samlevende gør de ikke.

**Acceptance Scenarios**:

1. **Given** en gift person, hvis partner har mindre indkomst end personfradraget, **Then** er
   personens skat lavere med partnerens uudnyttede skatteværdi.
2. **Given** det samme par som samlevende, **Then** er der ingen overførsel.

### Edge Cases

- **Partneren er ikke pensionist endnu**: Partnerens indkomst indgår med den andel, registret
  angiver (som i dag).
- **Partneren udskyder sin folkepension**: Partneren er pensionist fra sin faktiske
  folkepensionsstart.
- **Kalenderår, hvor den ene person ikke har en række** (før første udbetaling eller efter 90 år):
  Indkomsten er 0, og formuen er 0.
- **"Gift_samlevende"** (gammelt input) læses som samlevende (ingen skatteoverførsel).
- **Husstandens fastpunkt konvergerer ikke**: Der vises en advarsel som ved bufferen.

## Requirements *(mandatory)*

- **FR-001**: `civilstand` ∈ {enlig, gift, samlevende}. `gift_samlevende` accepteres som
  samlevende.
- **FR-002**: Kernen MUST have `beregn_husstand(a, b, ...)`, som regner begge personer med koblingen
  efter loven. Partnerens indkomst, formue, kapitalindkomst, uudnyttede personfradrag og
  pensionist-år går til den anden. Løsningen er deterministisk fastpunkt-iteration med loft og
  advarsel.
- **FR-003**: Ægtefællers overførsel af personfradrag (PSL § 10, stk. 3) og forhøjelse af
  bundfradraget for kapitalindkomst (§ 7, stk. 5). Det gælder kun for gifte.
- **FR-004**: Ældrecheckens formue = husstandens oplyste formue + begges buffer pr. 1. januar.
- **FR-005**: Indgangen skal returnere visning for dig, partner og samlet. `optimer` tager `hvem`.
- **FR-006**: Brugerfladen skal have guidens partnertrin med PDF, fanerne Dig/Partner/Samlet og den
  samlede graf og tidslinje på kalenderår.
- **FR-007**: Persondata forlader stadig ikke browseren. Det gælder også partnerens rapport.
- **FR-008**: Princip X: axe 0 fejl, ingen vandret scroll ved 360 px, tydelig mærkning af, hvem
  tallene gælder.

## Success Criteria *(mandatory)*

- **SC-001**: Golden cases for koblingen:
  - partnerens indkomst i pensionstillægget
  - fælles formue i ældrechecken
  - personfradrag og kapitalindkomst for gifte, men ikke for samlevende
- **SC-002**: Husstanden konvergerer på 4 eller færre iterationer i golden cases og med den
  syntetiske rapport.
- **SC-003**: Samlet er lig summen af de to faste beløb.
- **SC-004**: Samme resultat i Pyodide og CPython.
- **SC-005**: En ændring giver nye tal på under 2 s i browseren for to profiler.
