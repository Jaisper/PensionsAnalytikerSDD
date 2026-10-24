"""Inputvalidering (FR-003): ugyldigt input giver UgyldigtInput med felt og dansk besked."""
from __future__ import annotations

import math
from datetime import date

from . import register
from .model import Antagelser, Pensionsprofil, UgyldigtInput
from .regler.folkepension import folkepensionsalder
from .regler.udbetalingsalder import tidligste_udbetalingsalder
from .register.opslag import Regelopslag

ORDNINGSTYPER = ("ratepension", "livsvarig", "aldersopsparing", "kapitalpension")


def _ikke_negativ(felt: str, vaerdi: float | None) -> None:
    if vaerdi is not None and vaerdi < 0:
        raise UgyldigtInput(felt, "Beløbet må ikke være negativt")


def valider(profil: Pensionsprofil, antagelser: Antagelser, satsaar: int, beregningsdato: date) -> None:
    if satsaar not in register.satsaar():
        raise UgyldigtInput("satsaar", f"Satsår {satsaar} findes ikke i regelregistret")
    o = Regelopslag(satsaar, beregningsdato.year, 0.0)

    if profil.foedselsdato >= beregningsdato:
        raise UgyldigtInput("foedselsdato", "Fødselsdatoen skal ligge før beregningsdatoen")
    foerste = min(r["foedt_fra"] for r in o.v("fp.folkepensionsalder"))
    if profil.foedselsdato < foerste:
        raise UgyldigtInput("foedselsdato", f"Kernen understøtter kun personer født {foerste:%d.%m.%Y} eller senere")
    fp_alder = folkepensionsalder(profil.foedselsdato, o)

    if profil.civilstand not in ("enlig", "gift_samlevende"):
        raise UgyldigtInput("civilstand", "Civilstand skal være 'enlig' eller 'gift_samlevende'")
    if profil.civilstand == "gift_samlevende" and profil.partner is None:
        raise UgyldigtInput("partner", "Gift/samlevende kræver oplysninger om partneren")
    if register.kommune_noegle(satsaar, profil.kommune) is None:
        raise UgyldigtInput("kommune", f"Ukendt kommune: {profil.kommune}")
    _ikke_negativ("likvid_formue", profil.likvid_formue)
    _ikke_negativ("anden_kapitalindkomst", profil.anden_kapitalindkomst)
    _ikke_negativ("atp_aarlig", profil.atp_aarlig)

    if profil.partner is not None:
        if profil.partner.foedselsdato < foerste:
            raise UgyldigtInput("partner.foedselsdato", f"Partneren skal være født {foerste:%d.%m.%Y} eller senere")
        for aar, ind in profil.partner.indkomst_pr_aar.items():
            _ikke_negativ(f"partner.indkomst_pr_aar[{aar}].am_pligtig_arbejdsindkomst", ind.am_pligtig_arbejdsindkomst)
            _ikke_negativ(f"partner.indkomst_pr_aar[{aar}].oevrig_indkomst", ind.oevrig_indkomst)

    set_ids: set[str] = set()
    for ordning in profil.ordninger:
        felt = f"ordninger[{ordning.id}]"
        if ordning.id in set_ids:
            raise UgyldigtInput(felt, "Ordnings-id skal være unikt")
        set_ids.add(ordning.id)
        if ordning.type not in ORDNINGSTYPER:
            raise UgyldigtInput(f"{felt}.type", f"Ukendt ordningstype: {ordning.type}")
        _ikke_negativ(f"{felt}.saldo", ordning.saldo)
        _ikke_negativ(f"{felt}.aarlig_indbetaling", ordning.aarlig_indbetaling)

        tidligste, usikker = tidligste_udbetalingsalder(profil.foedselsdato, ordning.oprettet, fp_alder, o)
        if not usikker and ordning.udbetaling_start_alder < tidligste:
            raise UgyldigtInput(
                f"{felt}.udbetaling_start_alder",
                f"Ordningen kan tidligst udbetales fra {tidligste:g} år (afhænger af oprettelsesdatoen)",
            )
        if ordning.type == "ratepension" and ordning.udbetaling_aar is not None:
            min_aar = o.v("ordning.ratepension.min_aar")
            if ordning.udbetaling_aar < min_aar:
                raise UgyldigtInput(f"{felt}.udbetaling_aar", f"En ratepension udbetales over mindst {min_aar} år")
            sidste_tilladte = math.ceil(tidligste) + o.v("ordning.ratepension.maks_aar_efter_udbetalingsalder")
            if ordning.udbetaling_start_alder + ordning.udbetaling_aar - 1 > sidste_tilladte:
                raise UgyldigtInput(
                    f"{felt}.udbetaling_aar",
                    f"Sidste rate må senest udbetales som {sidste_tilladte}-årig",
                )

    if not 0 <= antagelser.folkepension_opsaettelse_aar <= o.v("opsat.maks_aar"):
        raise UgyldigtInput(
            "antagelser.folkepension_opsaettelse_aar",
            f"Folkepensionen kan opsættes 0–{o.v('opsat.maks_aar')} år",
        )
    for navn in ("afkast_efter_pal", "inflation", "loenvaekst"):
        if getattr(antagelser, navn) <= -1:
            raise UgyldigtInput(f"antagelser.{navn}", "Satsen skal være større end -100 %")
    if antagelser.satsregulering is not None and antagelser.satsregulering <= -1:
        raise UgyldigtInput("antagelser.satsregulering", "Satsen skal være større end -100 %")
    if antagelser.livsvarig_min_aar < 1:
        raise UgyldigtInput("antagelser.livsvarig_min_aar", "Skal være mindst 1 år")
    if not 0 <= antagelser.buffer_kapitalskat < 1:
        raise UgyldigtInput("antagelser.buffer_kapitalskat", "Angives som brøk, fx 0.27")
