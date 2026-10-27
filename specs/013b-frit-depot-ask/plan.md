# Implementation Plan: 013b Frit depot og aktiesparekonto

**Branch**: `013b-frit-depot-ask` | **Spec**: [spec.md](spec.md) | **Dato**: 2026-10-27

## Beslutninger (2026-10-27)

- **Én rente for alle typer**, som i 013 (pensionens afkast før PAL-skat). Afkast pr. aktivtype
  flyttes til 023. Udjævningen ser fortsat én samlet pulje, så "låner aldrig" (010) holder uændret.
  Skatten afhænger af, hvilken del af puljen der bruges.
- **Aktieafkast er kursgevinst**, der beskattes ved salg. Der er intet løbende udbytte
  (forenkling `aktieafkast_som_kursgevinst`). Udbyttegrænsen på 5.000 kr. i § 29 bliver derfor
  ikke brugt, og posten kommer ikke i registret.
- **Obligationsbaserede investeringsbeviser** lagerbeskattes som kapitalindkomst (ABL § 19 C). De
  skrives under bank. "Lagerbeskattede fonde først" er dermed opfyldt af rækkefølgen bank → depot.

## Model

Puljen (bufferen fra 009/013) deles i tre lag: bank, depot og ASK. Udjævningen bestemmer, hvad
der sættes ind og trækkes ud hvert år. Lagene bestemmer skatten. Hvert år sker følgende:

1. **Indskud**:
   - Engangsbeløb og overskud går i banklaget.
   - Opsparing i planen indsættes i sit eget lag ved `tabel_start`. For depotet føres
     anskaffelsessummen med.
   - Løbende ASK-indskud går i ASK-laget. Indskud over loftet går i depotlaget, og der kommer en
     advarsel.
2. **Træk** følger `Antagelser.traekraekkefoelge` (standard bank → depot → ASK). Træk fra
   depotet realiserer gevinsten forholdsmæssigt: gevinst = træk × (værdi − anskaffelse) / værdi.
3. **Afkast**: Bankens afkast er kapitalindkomst (som før). Depotets afkast er urealiseret
   gevinst og beskattes ikke, før der sælges. ASK-afkastet beskattes med 17 % (lager).

Skatterne betales af årets udbetaling, som bufferens kapitalindkomstskat (009):

- `Aarsresultat.aktieindkomst`, `skat_aktieindkomst` og `skat_aktiesparekonto`.
- Udjævningen bruger `Aarsresultat.disponibel`. Det er nettoindkomsten minus skat af opsparing
  minus løbende ASK-indskud.

**Aktieindkomst (PSL § 8 a)**:
- 27 % op til progressionsgrænsen og 42 % over. Skatten regnes særskilt, uden personfradrag.
- Gifte: partnerens uudnyttede grænse forhøjer grænsen (stk. 4) via `Partner.aktieindkomst_pr_aar`.
- Aktieindkomsten indgår i § 29-grundlaget og i den personlige tillægsprocent. Den indgår også i
  partnerens øvrige indkomst.

**ASK**: Afkastet indgår ikke i § 29. Lageret fanger både opsparing i planen og urørt opsparing.

**Før første udbetalingsår** (uden løn):
- Depotet vokser uden skat. Det er korrekt efter loven, fordi der ikke sælges.
- ASK vokser med afkast efter 17 %, fordi banken trækker skatten på kontoen.
- Kun banken har forenklingen `opsparing_skat_foer_udbetaling`.

**Urørt opsparing**:
- Bank: afkastet er kapitalindkomst (som før).
- Depot: vokser og sælges aldrig.
- ASK: lagerskatten betales af udbetalingen.

**Likvid formue** (§ 72 d, stk. 2) er summen af alle lag og urørt opsparing.

**Fastpunktet** (009) får aktieindkomst og ASK-afkast med i tilstanden ved siden af
kapitalindkomst og formue.

## Model og brugerflade

- `Aktiv.type`: "bank" | "depot" | "ask".
- `Aktiv.urealiseret_gevinst` (kun depot). `None` betyder standardandelen, som er en antagelse.
- `Aktiv.aarligt_indskud` (kun ASK): i dagens kroner, reguleres og kun med løn frem til
  stopalderen.
- `Antagelser.depot_urealiseret_andel` (0,5) og `traekraekkefoelge`.
- Guiden: frit depot (beløb, "heraf urealiseret gevinst", i planen) og aktiesparekonto (beløb,
  i planen, indskud om året) for dig og partneren.
- Registerposter:
  - `skat.aktieindkomst.sats_lav`, `skat.aktieindkomst.sats_hoej` og
    `skat.aktieindkomst.progressionsgraense` (reguleres)
  - `ask.sats` og `ask.indskudsloft` (reguleres)
- Advarsler:
  - `AKTIEINDKOMST_OVER_GRAENSE`: aldre og forslag om at sprede salget.
  - `ASK_OVER_LOFT`.
- Forenklinger:
  - `aktieafkast_som_kursgevinst`
  - `ask_indskud_lig_saldo`: hidtidige indskud = saldoen.
  - `afkast_som_kapitalindkomst` gælder kun bank (FR-003).

## Constitution check

- Princip III: alle satser i registret med kilde, hentet fra 013's verificerede lovgrundlag.
- Princip IV: golden cases skrives først.
- Princip VII og XI: uændret. Alt regnes i browseren, og der sendes ingen persondata.

## Risiko

Fastpunktet har flere størrelser. Konvergensen måles mod SC fra 013. Advarslen
`BUFFER_IKKE_KONVERGERET` dækker de tilfælde, hvor fastpunktet ikke konvergerer.
