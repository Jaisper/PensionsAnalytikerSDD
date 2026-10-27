"""Husstanden: to fulde profiler koblet efter loven (feature 012).

Indkomstskatten er individuel, og hver person har sin egen udbetalingsplan, udjævning og buffer.
Personerne kobles kun dér, hvor loven kobler dem:

- Pensionstillæg og personlig tillægsprocent bygger på parrets samlede indtægtsgrundlag (lov om
  social pension § 29): partnerens private pension, ATP og kapitalindkomst indgår — fuldt, når
  partneren er pensionist, ellers med registrets andel.
- Ældrechecks formuegrænse gælder husstandens samlede likvide formue (§ 72 d, stk. 2), også
  begges buffer og opsparing uden for pension (013).
- Kun ægtefæller: uudnyttet skatteværdi af personfradrag nedsætter den andens skatter (PSL § 10,
  stk. 3), et uudnyttet bundfradrag for kapitalindkomst forhøjer den andens (PSL § 7, stk. 5), og
  en uudnyttet progressionsgrænse for aktieindkomst forhøjer den andens (PSL § 8 a, stk. 4; 013b).

Hver persons tal afhænger af den andens (fx via bufferens kapitalindkomst), så husstanden løses
ved deterministisk fastpunkt-iteration: B regnes uden kendt partner, så A med B, så B med A, …
indtil begges jævne udbetaling ændrer sig mindre end 1 kr./md. i alle år.

Partnerens indkomst før vedkommendes første udbetaling (fx løn) kendes ikke; den regnes som 0, og
uudnyttet personfradrag overføres kun fra år, hvor partneren har en række (forsigtigt).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from .fremskrivning import beregn
from .jaevn import BUFFER_TOLERANCE_KR
from .model import Advarsel, Antagelser, Fremskrivning, Partner, PartnerIndkomst, Pensionsprofil

HUSSTAND_MAKS_ITERATIONER = 6
PARTNER_AAR = 80  # kalenderår frem, partnerens tal udfyldes for (0, hvor partneren ingen række har)
PRIVAT_INDKOMST = ("ratepension", "livsvarig", "atp")


@dataclass(frozen=True)
class Husstand:
    a: Fremskrivning
    b: Fremskrivning
    iterationer: int
    konvergeret: bool


def partner_fra(res: Fremskrivning, profil: Pensionsprofil, antagelser: Antagelser) -> Partner:
    """Partneroplysningerne, den anden person skal bruge, udledt af denne persons beregning."""
    aar = range(res.beregningsdato.year, res.beregningsdato.year + PARTNER_AAR)
    pr_aar = {a.kalenderaar: a for a in res.aar}
    foedselsaar = profil.foedselsdato.year

    def privat(a) -> float:
        return sum(k.brutto for k in a.kilder if k.type in PRIVAT_INDKOMST) + a.kapitalindkomst + a.aktieindkomst

    return Partner(
        foedselsdato=profil.foedselsdato,
        indkomst_pr_aar={
            k: PartnerIndkomst(oevrig_indkomst=(privat(pr_aar[k]) if k in pr_aar else 0.0) + profil.anden_kapitalindkomst)
            for k in aar
        },
        formue_pr_aar={foedselsaar + alder: v for alder, v in res.formue_primo().items() if v > 0},
        kapitalindkomst_pr_aar={k: pr_aar[k].kapitalindkomst if k in pr_aar else 0.0 for k in aar},
        uudnyttet_personfradrag_pr_aar={k: a.uudnyttet_personfradrag for k, a in pr_aar.items()},
        aktieindkomst_pr_aar={k: pr_aar[k].aktieindkomst if k in pr_aar else 0.0 for k in aar},
        pensionist_fra_aar=foedselsaar + res.folkepensionsalder + antagelser.folkepension_opsaettelse_aar,
    )


def _ukendt_partner(profil: Pensionsprofil, beregningsdato: date) -> Partner:
    """Startgæt: en partner uden kendt indkomst eller formue."""
    aar = range(beregningsdato.year, beregningsdato.year + PARTNER_AAR)
    return Partner(foedselsdato=profil.foedselsdato, indkomst_pr_aar={k: PartnerIndkomst() for k in aar},
                   kapitalindkomst_pr_aar={k: 0.0 for k in aar})


def _samme(x: Fremskrivning | None, y: Fremskrivning) -> bool:
    if x is None or x.jaevn is None or y.jaevn is None or len(x.jaevn.aar) != len(y.jaevn.aar):
        return False
    return max(abs(r.jaevn - s.jaevn) for r, s in zip(x.jaevn.aar, y.jaevn.aar)) < BUFFER_TOLERANCE_KR * 12


def beregn_husstand(
    profil_a: Pensionsprofil,
    antagelser_a: Antagelser,
    profil_b: Pensionsprofil,
    antagelser_b: Antagelser,
    satsaar: int,
    beregningsdato: date,
) -> Husstand:
    res_b = beregn(replace(profil_b, partner=_ukendt_partner(profil_a, beregningsdato)), antagelser_b,
                   satsaar, beregningsdato)
    res_a = None
    konvergeret = False
    iteration = 0
    while iteration < HUSSTAND_MAKS_ITERATIONER:
        iteration += 1
        ny_a = beregn(replace(profil_a, partner=partner_fra(res_b, profil_b, antagelser_b)), antagelser_a,
                      satsaar, beregningsdato)
        ny_b = beregn(replace(profil_b, partner=partner_fra(ny_a, profil_a, antagelser_a)), antagelser_b,
                      satsaar, beregningsdato)
        if _samme(res_a, ny_a) and _samme(res_b, ny_b):
            res_a, res_b, konvergeret = ny_a, ny_b, True
            break
        res_a, res_b = ny_a, ny_b
    if not konvergeret:
        advarsel = Advarsel("HUSSTAND_IKKE_KONVERGERET",
                            "Jeres to beregninger påvirker hinanden (pensionstillæg og ældrecheck) og kunne ikke "
                            "regnes helt præcist sammen. Tallene kan afvige lidt.")
        res_a = replace(res_a, advarsler=res_a.advarsler + (advarsel,))
        res_b = replace(res_b, advarsler=res_b.advarsler + (advarsel,))
    return Husstand(res_a, res_b, iteration, konvergeret)
