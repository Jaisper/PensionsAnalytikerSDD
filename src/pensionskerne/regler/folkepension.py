"""Folkepension — lov om social pension §§ 1 a, 26, 29 og 32 a.

Grundbeløbet er uafhængigt af anden indkomst (forudsat ingen arbejdsindkomst).
Pensionstillægget aftrappes efter én af tre regler afhængigt af civilstand og
partnerens pensionsstatus. Indtægtsgrundlaget omfatter ATP, skattepligtige private
pensionsudbetalinger og kapitalindkomst — ikke aldersopsparing og ikke egen
arbejdsindkomst (borger.dk; domænegrundlag A4, A5).
"""
from __future__ import annotations

import math
from datetime import date
from typing import Literal

from ..model import PartnerIndkomst, UgyldigtInput
from ..register.opslag import Regelopslag

Tillaegsregel = Literal["enlig", "gift_pensionist", "gift_ikke_pensionist"]

MAANEDER = 12


def folkepensionsalder(foedselsdato: date, o: Regelopslag) -> int:
    for raekke in o.v("fp.folkepensionsalder"):
        if raekke["foedt_fra"] <= foedselsdato <= raekke["foedt_til"]:
            return int(raekke["alder"])
    raise UgyldigtInput("foedselsdato", "Fødselsdatoen er uden for de fødselsår, kernen understøtter")


def foerste_aar_andel(foedselsdato: date) -> float:
    """Andel af året med udbetaling i det år, folkepensionsalderen nås.

    Folkepension (og ATP) udbetales fra den 1. i måneden efter, at alderen er nået.
    """
    return (MAANEDER - foedselsdato.month) / MAANEDER


def fradrag_forhoejelse(gift: bool, o: Regelopslag) -> float:
    """Midlertidig forhøjelse af fradraget for pensionstillæg og tillægsprocent (§ 49 c).

    Forhøjelsen nedsættes med lige store trin hvert år og er 0 fra `nul_aar`.
    """
    beloeb = o.v("fp.fradrag_forhoejelse.gift" if gift else "fp.fradrag_forhoejelse.enlig")
    nul_aar = o.v("fp.fradrag_forhoejelse.nul_aar")
    andel = max(0, nul_aar - o.kalenderaar) / (nul_aar - o.satsaar)
    return beloeb * min(1.0, andel)


def tillaegsregel(gift: bool, partner_er_pensionist: bool) -> Tillaegsregel:
    if not gift:
        return "enlig"
    return "gift_pensionist" if partner_er_pensionist else "gift_ikke_pensionist"


def pensionstillaeg(indtaegtsgrundlag: float, regel: Tillaegsregel, o: Regelopslag) -> float:
    """Pensionstillæg pr. år efter aftrapning (lov om social pension § 29)."""
    if regel == "enlig":
        ydelse = o.v("fp.tillaeg.enlig.ydelse")
        fradrag = o.v("fp.tillaeg.enlig.fradrag") + fradrag_forhoejelse(False, o)
        aftrapning = o.v("fp.tillaeg.enlig.aftrapning")
    else:
        ydelse = o.v("fp.tillaeg.gift.ydelse")
        fradrag = o.v("fp.tillaeg.gift.fradrag") + fradrag_forhoejelse(True, o)
        aftrapning = o.v(f"fp.tillaeg.{regel}.aftrapning")
    return max(0.0, ydelse - aftrapning * max(0.0, indtaegtsgrundlag - fradrag))


def indtaegtsgrundlag(
    privat_pensionsindkomst: float,
    atp: float,
    kapitalindkomst: float,
    partner: PartnerIndkomst | None,
    partner_er_pensionist: bool,
    o: Regelopslag,
    aktieindkomst: float = 0.0,
) -> float:
    """Indtægtsgrundlaget for pensionstillæg og personlig tillægsprocent.

    Partnerens AM-bidragspligtige arbejdsindkomst indgår aldrig. Partnerens øvrige
    indkomst indgår fuldt, hvis partneren er pensionist, ellers med den andel, der
    ikke ses bort fra (§ 29, stk. 5). Den opgjorte indtægt afrundes nedad til hele
    hundreder (§ 29, stk. 6).
    """
    # Aktieindkomst indgår (§ 29), undtagen aktieudbytte op til et grundbeløb; kernen regner ikke
    # med udbytte (013b), så hele aktieindkomsten er gevinst ved salg og indgår.
    grundlag = privat_pensionsindkomst + atp + kapitalindkomst + max(0.0, aktieindkomst)
    if partner is not None:
        andel = 1.0 if partner_er_pensionist else o.v("fp.partner_ikke_pensionist.medregnet_andel")
        grundlag += partner.oevrig_indkomst * andel
    afrunding = o.v("fp.indtaegtsgrundlag.afrunding")
    return math.floor(grundlag / afrunding) * afrunding
