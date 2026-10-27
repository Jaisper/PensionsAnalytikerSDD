"""Guidedata (JSON fra brugerfladen) → kernens Pensionsprofil og Antagelser.

Ingen regler her: kun typeomsætning. Kernen validerer indholdet (FR-003).
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date
from typing import Any

from pensionskerne import Aktiv, Antagelser, Loen, Ordning, Partner, PartnerIndkomst, Pensionsprofil, UgyldigtInput

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
        foedt = _dato(_kraev(p, "foedselsdato", "person.partner.foedselsdato"), "person.partner.foedselsdato")
        if p.get("profil"):
            partner = Partner(foedselsdato=foedt)  # fuld profil: husstanden udfylder resten (012)
        else:
            indkomst = PartnerIndkomst(oevrig_indkomst=_tal(p.get("oevrig_indkomst_aar"), "person.partner.oevrig_indkomst_aar"))
            partner = Partner(foedselsdato=foedt, indkomst_pr_aar={aar: indkomst for aar in PARTNER_AAR})

    profil = Pensionsprofil(
        foedselsdato=_dato(_kraev(person, "foedselsdato", "person.foedselsdato"), "person.foedselsdato"),
        civilstand=_kraev(person, "civilstand", "person.civilstand"),
        kommune=_kraev(person, "kommune", "person.kommune"),
        folkekirkemedlem=bool(person.get("folkekirkemedlem", False)),
        likvid_formue=_tal(person.get("likvid_formue"), "person.likvid_formue"),
        atp_aarlig=_tal(person.get("atp_aarlig"), "person.atp_aarlig", None),
        ordninger=_ordninger(data.get("ordninger") or []),
        opsparing=_opsparing(person.get("opsparing") or []),
        loen=_loen(person.get("loen")),
        partner=partner,
    )

    a = data.get("antagelser") or {}
    standard = Antagelser()
    antagelser = Antagelser(
        afkast_efter_pal=_tal(a.get("afkast_efter_pal"), "antagelser.afkast_efter_pal", standard.afkast_efter_pal),
        inflation=_tal(a.get("inflation"), "antagelser.inflation", standard.inflation),
        folkepension_opsaettelse_aar=_heltal(a.get("folkepension_opsaettelse_aar"),
                                             "antagelser.folkepension_opsaettelse_aar", 0),
        plan_slut_alder=_heltal(a.get("plan_slut_alder"), "antagelser.plan_slut_alder"),
        # 013b: rækkefølgen, opsparingen bruges i (grænseflade til en senere optimering).
        traekraekkefoelge=tuple(a.get("traekraekkefoelge") or standard.traekraekkefoelge),
    )
    return profil, antagelser


def til_husstand(data: dict) -> tuple[Pensionsprofil, Antagelser, Pensionsprofil, Antagelser] | None:
    """Er partneren angivet som fuld profil (feature 012): begge personers profil og antagelser.
    Kommune, husstandens likvide formue og afkast/inflation er fælles; resten er partnerens eget."""
    p = (data.get("person") or {}).get("partner") or {}
    if not p.get("profil"):
        return None
    profil_a, antagelser_a = til_kerne(data)
    pp = p["profil"]
    profil_b = replace(
        profil_a,
        foedselsdato=profil_a.partner.foedselsdato,
        folkekirkemedlem=bool(pp.get("folkekirkemedlem", False)),
        atp_aarlig=_tal(pp.get("atp_aarlig"), "person.partner.profil.atp_aarlig", None),
        anden_kapitalindkomst=0.0,
        ordninger=_ordninger(pp.get("ordninger") or []),
        opsparing=_opsparing(pp.get("opsparing") or []),
        loen=_loen(pp.get("loen")),
        partner=Partner(foedselsdato=profil_a.foedselsdato),
    )
    antagelser_b = replace(antagelser_a, folkepension_opsaettelse_aar=_heltal(
        pp.get("folkepension_opsaettelse_aar"), "person.partner.profil.folkepension_opsaettelse_aar", 0))
    return profil_a, antagelser_a, profil_b, antagelser_b


def _loen(l: dict | None) -> Loen | None:
    """Løn (feature 017). Uden årsløn og deltidsløn: ingen løn."""
    if not l:
        return None
    aarlig = _tal(l.get("aarlig"), "loen.aarlig")
    deltid = _tal(l.get("deltid_aarlig"), "loen.deltid_aarlig")
    if not aarlig and not deltid:
        return None
    return Loen(aarlig=aarlig, stop_alder=_heltal(l.get("stop_alder"), "loen.stop_alder"),
                deltid_aarlig=deltid, deltid_til_alder=_heltal(l.get("deltid_til_alder"), "loen.deltid_til_alder"))


def _opsparing(liste: list) -> tuple[Aktiv, ...]:
    """Opsparing uden for pension (feature 013 og 013b). Type og brug i planen har standardværdier;
    en tom gevinst på et depot giver antagelsens andel."""
    aktiver = []
    for i, a in enumerate(liste):
        id = str(a.get("id") or f"opsparing{i + 1}")
        gevinst = a.get("urealiseret_gevinst")
        aktiver.append(Aktiv(id=id, saldo=_tal(a.get("saldo"), f"opsparing[{id}].saldo"),
                             type=str(a.get("type") or "bank"), i_plan=bool(a.get("i_plan", True)),
                             urealiseret_gevinst=None if gevinst in (None, "") else _tal(
                                 gevinst, f"opsparing[{id}].urealiseret_gevinst"),
                             aarligt_indskud=_tal(a.get("aarligt_indskud"), f"opsparing[{id}].aarligt_indskud")))
    return tuple(aktiver)


def _ordninger(liste: list) -> tuple[Ordning, ...]:
    ordninger = []
    for i, o in enumerate(liste):
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
    return tuple(ordninger)
