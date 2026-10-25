"""Guidedata (JSON fra brugerfladen) → kernens Pensionsprofil og Antagelser.

Ingen regler her: kun typeomsætning. Kernen validerer indholdet (FR-003).
"""
from __future__ import annotations

from datetime import date
from typing import Any

from pensionskerne import Antagelser, Ordning, Partner, PartnerIndkomst, Pensionsprofil, UgyldigtInput

# Partnerens indkomst indtastes som ét årsbeløb og bruges for alle kalenderår.
PARTNER_AAR = range(2000, 2101)


def _kraev(data: dict, noegle: str, felt: str) -> Any:
    if not isinstance(data, dict) or data.get(noegle) in (None, ""):
        raise UgyldigtInput(felt, "Feltet skal udfyldes")
    return data[noegle]


def _dato(vaerdi: Any, felt: str, valgfri: bool = False) -> date | None:
    if valgfri and vaerdi in (None, ""):
        return None
    try:
        return date.fromisoformat(str(vaerdi))
    except ValueError:
        raise UgyldigtInput(felt, "Ugyldig dato") from None


def _tal(vaerdi: Any, felt: str, standard: float | None = 0.0) -> float | None:
    if vaerdi in (None, ""):
        return standard
    try:
        return float(vaerdi)
    except (TypeError, ValueError):
        raise UgyldigtInput(felt, "Skal være et tal") from None


def _heltal(vaerdi: Any, felt: str, standard: int | None = None) -> int | None:
    tal = _tal(vaerdi, felt, None)
    if tal is None:
        return standard
    if tal != int(tal):
        raise UgyldigtInput(felt, "Skal være et helt tal")
    return int(tal)


def til_kerne(data: dict) -> tuple[Pensionsprofil, Antagelser]:
    person = _kraev(data, "person", "person")
    partner = None
    if person.get("partner"):
        p = person["partner"]
        indkomst = PartnerIndkomst(oevrig_indkomst=_tal(p.get("oevrig_indkomst_aar"), "person.partner.oevrig_indkomst_aar"))
        partner = Partner(
            foedselsdato=_dato(_kraev(p, "foedselsdato", "person.partner.foedselsdato"), "person.partner.foedselsdato"),
            indkomst_pr_aar={aar: indkomst for aar in PARTNER_AAR},
        )

    ordninger = []
    for i, o in enumerate(data.get("ordninger") or []):
        id = str(o.get("id") or f"ordning{i + 1}")
        felt = f"ordninger[{id}]"
        ordninger.append(Ordning(
            id=id,
            type=_kraev(o, "type", f"{felt}.type"),
            saldo=_tal(o.get("saldo"), f"{felt}.saldo"),
            udbetaling_start_alder=_heltal(_kraev(o, "udbetaling_start_alder", f"{felt}.udbetaling_start_alder"),
                                           f"{felt}.udbetaling_start_alder"),
            oprettet=_dato(o.get("oprettet"), f"{felt}.oprettet", valgfri=True),
            aarlig_indbetaling=_tal(o.get("aarlig_indbetaling"), f"{felt}.aarlig_indbetaling"),
            udbetaling_aar=_heltal(o.get("udbetaling_aar"), f"{felt}.udbetaling_aar"),
            i_buffer=bool(o.get("i_buffer", True)),
            afgift_betalt=bool(o.get("afgift_betalt", False)),
            udbetalingsform=str(o.get("udbetalingsform") or "engangs"),
            tidligste_udbetalingsalder=_tal(o.get("tidligste_udbetalingsalder"), f"{felt}.tidligste_udbetalingsalder", None),
        ))

    profil = Pensionsprofil(
        foedselsdato=_dato(_kraev(person, "foedselsdato", "person.foedselsdato"), "person.foedselsdato"),
        civilstand=_kraev(person, "civilstand", "person.civilstand"),
        kommune=_kraev(person, "kommune", "person.kommune"),
        folkekirkemedlem=bool(person.get("folkekirkemedlem", False)),
        likvid_formue=_tal(person.get("likvid_formue"), "person.likvid_formue"),
        atp_aarlig=_tal(person.get("atp_aarlig"), "person.atp_aarlig", None),
        ordninger=tuple(ordninger),
        partner=partner,
    )

    a = data.get("antagelser") or {}
    standard = Antagelser()
    antagelser = Antagelser(
        afkast_efter_pal=_tal(a.get("afkast_efter_pal"), "antagelser.afkast_efter_pal", standard.afkast_efter_pal),
        inflation=_tal(a.get("inflation"), "antagelser.inflation", standard.inflation),
        folkepension_opsaettelse_aar=_heltal(a.get("folkepension_opsaettelse_aar"),
                                             "antagelser.folkepension_opsaettelse_aar", 0),
    )
    return profil, antagelser
