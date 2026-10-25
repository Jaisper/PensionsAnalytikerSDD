"""Aflæsning → guidedata. Deterministisk og uden AI (FR-005, FR-006).

Hver ordning får en kilde og en liste over usikkerheder, som vises ved ordningen i guiden.
"""
from __future__ import annotations

import re
from datetime import date

from pensionskerne import UgyldigtInput
from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.folkepension import folkepensionsalder

from .aflaeser import AflaestOrdning, Aflaesning

SPRINGES_OVER = {"folkepension", "forsikring", "atp"}
PERIODE_INTERVAL = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*år", re.IGNORECASE)
PERIODE_ENKELT = re.compile(r"^\s*(\d+)\s*år\s*$", re.IGNORECASE)


def _periode_aar(o: AflaestOrdning) -> int | None:
    aar = 0
    for p in o.udbetalingsperioder:
        if m := PERIODE_INTERVAL.match(p.etiket):
            aar += int(m.group(2)) - int(m.group(1)) + 1
        elif PERIODE_ENKELT.match(p.etiket):
            aar += 1
        else:
            return None
    return aar or None


def _oprettet(tidligste: int | None, fp_alder: int | None, o: Regelopslag) -> str:
    """Oprettelsesperiode udledt af tidligste udbetalingsalder (registrets regler for udbetalingsalder)."""
    if tidligste is None or fp_alder is None:
        return "ved_ikke"
    if tidligste == fp_alder - o.v("ordning.udbetalingsalder.2007_2017")["aar_foer_fp"]:
        return "2007_2017"
    if tidligste == fp_alder - o.v("ordning.udbetalingsalder.fra_2018")["aar_foer_fp"]:
        return "fra2018"
    if tidligste <= o.v("ordning.udbetalingsalder.foer_2007")["alder"]:
        return "foer2007"
    return "ved_ikke"


def _ordning(o: AflaestOrdning, fp_alder: int | None, regler: Regelopslag) -> dict:
    usikkerheder: list[str] = list(o.noter)
    type_ = o.kategori
    if o.kategori == "kapitalpension" and o.afgift_betalt:
        usikkerheder.append("Rapporten viser, at afgiften er betalt – kapitalpensionen udbetales skattefrit.")
    elif o.kategori == "ukendt":
        type_ = "livsvarig"
        usikkerheder.append(f"Typen kunne ikke aflæses ({o.produkttype}). Vi har gættet på livsvarig pension – tjek det.")

    if o.saldo is None:
        usikkerheder.append("Saldo blev ikke fundet i rapporten.")

    start = o.aftalt_udbetalingsalder or o.tidligste_udbetalingsalder
    if start is None:
        usikkerheder.append("Startalder blev ikke fundet i rapporten.")
    elif o.aftalt_udbetalingsalder is None:
        usikkerheder.append(f"Startalder sat til tidligste mulige udbetaling ({start} år).")

    udbetaling_aar = None
    if type_ == "ratepension":
        min_aar = regler.v("ordning.ratepension.min_aar")
        maks_aar = regler.v("ordning.ratepension.maks_aar_efter_udbetalingsalder")
        udbetaling_aar = _periode_aar(o)
        if udbetaling_aar is None or not min_aar <= udbetaling_aar <= maks_aar:
            udbetaling_aar = min_aar
            usikkerheder.append(f"Udbetalingsperioden kunne ikke aflæses – vi bruger {min_aar} år.")

    oprettet = _oprettet(o.tidligste_udbetalingsalder, fp_alder, regler)
    if oprettet != "ved_ikke" and o.tidligste_udbetalingsalder is None:
        usikkerheder.append("Oprettelsesperioden er udledt af den tidligste udbetalingsalder.")

    kilde = " · ".join(x for x in (o.selskab, f"aftale {o.aftalenr}" if o.aftalenr else None) if x) or o.produkttype
    return {
        "type": type_, "saldo": o.saldo, "aarlig_indbetaling": o.aarlig_indbetaling,
        "udbetaling_start_alder": start, "udbetaling_aar": udbetaling_aar, "oprettet": oprettet,
        "tidligste_udbetalingsalder": o.tidligste_udbetalingsalder,
        "afgift_betalt": bool(o.afgift_betalt) if type_ == "kapitalpension" else False,
        "kilde": kilde, "produkttype": o.produkttype, "usikkerheder": usikkerheder,
    }


def til_guide(aflaesning: Aflaesning, foedselsdato: date | None, satsaar: int) -> dict:
    regler = Regelopslag(satsaar, satsaar, 0.0)
    bemaerkninger: list[str] = []
    fp_alder = None
    if foedselsdato is None:
        bemaerkninger.append("Fødselsdato blev ikke fundet i rapporten. Udfyld den selv.")
    else:
        try:
            fp_alder = folkepensionsalder(foedselsdato, regler)
        except UgyldigtInput as e:
            bemaerkninger.append(e.besked)

    atp = aflaesning.atp_aarlig
    if atp is None:
        atp = next((p.aarligt_beloeb for o in aflaesning.ordninger if o.kategori == "atp"
                    for p in o.udbetalingsperioder if p.aarligt_beloeb), None)

    ordninger = [_ordning(o, fp_alder, regler) for o in aflaesning.ordninger if o.kategori not in SPRINGES_OVER]
    if not ordninger:
        bemaerkninger.append("Vi fandt ingen pensionsordninger ud over ATP og folkepension.")
    return {
        "person": {"foedselsdato": foedselsdato.isoformat() if foedselsdato else None},
        "atp_aarlig": atp,
        "ordninger": ordninger,
        "bemaerkninger": bemaerkninger,
    }
