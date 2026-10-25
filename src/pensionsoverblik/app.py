"""Indgangspunkt for brugerfladen (feature 005, D1). Kaldes af browserens worker i Pyodide.

Rene funktioner uden I/O: input kommer kun som argumenter, og dagens dato gives af browseren
(Princip VI). Svar og fejl er data — {"ok": True, "data": ...} eller {"ok": False, "fejl":
{"kode", "felt", "besked"}} — med samme indhold som de tidligere HTTP-endpoints. Intet gemmes
eller logges, og intet forlader browseren (Princip VII og XI).
"""
from __future__ import annotations

import json
from datetime import date

from pensionskerne import UgyldigtInput, beregn as kerne_beregn, register

from .oversaet import til_kerne
from .pdfimport.aflaeser import AflaesningFejl, vaelg_aflaeser
from .pdfimport.omsaet import til_guide
from .visning import byg_visning, graenser

MAKS_PDF_BYTES = 25 * 1024 * 1024
# Den lokale parser (Princip XI). Oprettes først ved første PDF, så beregningen kan starte uden
# pdfplumber, pdfminer og cryptography, som browseren henter senere (research R005).
AFLAESER = None


def _satsaar() -> int:
    return max(register.satsaar())


def _ok(data) -> dict:
    return {"ok": True, "data": data}


def _fejl(kode: str, besked: str, felt: str | None = None) -> dict:
    return {"ok": False, "fejl": {"kode": kode, "felt": felt, "besked": besked}}


def kommuner() -> list[dict]:
    navne = register.kommunenavne(_satsaar())
    return sorted(({"noegle": k, "navn": v} for k, v in navne.items()), key=lambda k: k["navn"].casefold())


def _input(guide_json: str, idag: str):
    try:
        data = json.loads(guide_json)
    except ValueError:
        raise UgyldigtInput("body", "Forespørgslen kunne ikke læses") from None
    try:
        dato = date.fromisoformat(idag)
    except ValueError:
        raise UgyldigtInput("idag", "Ugyldig dato fra browseren") from None
    profil, antagelser = til_kerne(data)
    return profil, antagelser, dato


def beregn(guide_json: str, idag: str) -> dict:
    try:
        profil, antagelser, dato = _input(guide_json, idag)
        visning = byg_visning(kerne_beregn(profil, antagelser, _satsaar(), dato))
    except UgyldigtInput as e:
        return _fejl("ugyldigt_input", e.besked, e.felt)
    visning["graenser"] = graenser(profil, _satsaar())
    return _ok(visning)


def optimer(guide_json: str, idag: str, fremdrift=None) -> dict:
    """Find bedste plan (feature 007). Beløb er det faste beløb hele perioden (kr./md., dagens
    kroner), afrundet som hovedtallet. `plan` er forslaget — eller den nuværende plan, hvis
    intet er bedre."""
    from pensionskerne.optimering import optimer as kerne_optimer

    try:
        profil, antagelser, dato = _input(guide_json, idag)
        r = kerne_optimer(profil, antagelser, _satsaar(), dato, fremdrift=fremdrift)
    except UgyldigtInput as e:
        return _fejl("ugyldigt_input", e.besked, e.felt)
    foer = int(round(r.udgangspunkt_maaned, -2))
    efter = int(round(r.bedste_maaned, -2)) if r.bedste else foer
    forbedret = efter > foer  # en forbedring, der forsvinder i afrundingen, er ingen forbedring for borgeren
    plan = r.bedste if forbedret else r.udgangspunkt
    aendringer = []
    if forbedret:
        for oid, til in plan.starter.items():
            if til != r.udgangspunkt.starter[oid]:
                aendringer.append({"id": oid, "felt": "start", "fra": r.udgangspunkt.starter[oid], "til": til})
            if oid in plan.varighed and plan.varighed[oid] != r.udgangspunkt.varighed[oid]:
                aendringer.append({"id": oid, "felt": "varighed", "fra": r.udgangspunkt.varighed[oid], "til": plan.varighed[oid]})
        if plan.opsaettelse != r.udgangspunkt.opsaettelse:
            aendringer.append({"id": "folkepension", "felt": "opsaettelse", "fra": r.udgangspunkt.opsaettelse, "til": plan.opsaettelse})
    ordninger = {oid: {"udbetaling_start_alder": start} for oid, start in plan.starter.items()}
    for oid, aar in plan.varighed.items():
        ordninger.setdefault(oid, {})["udbetaling_aar"] = aar
    return _ok({
        "forbedret": forbedret, "foer": foer, "efter": efter if forbedret else foer,
        "aendringer": aendringer,
        "plan": {"ordninger": ordninger, "folkepension_opsaettelse_aar": plan.opsaettelse},
        "evalueret": r.evalueret, "mulige": r.mulige, "udtoemmende": r.udtoemmende,
    })


def pdf(data: bytes) -> dict:
    """Aflæser en PensionsInfo-rapport lokalt til guidedata."""
    global AFLAESER
    from .pdfimport.tekst import PdfFejl, foedselsdato_fra_rapport, udtraek_forside

    if len(data) > MAKS_PDF_BYTES:
        return _fejl("for_stor", f"Filen er for stor. Den må højst fylde {MAKS_PDF_BYTES // 1024 // 1024} MB.")
    try:
        forside = udtraek_forside(data)
    except PdfFejl as e:
        return _fejl(e.kode, e.besked)
    try:
        AFLAESER = AFLAESER or vaelg_aflaeser()
        aflaesning = AFLAESER.aflaes(data)
    except AflaesningFejl as e:
        return _fejl(e.kode, f"{e.besked} Du kan i stedet indtaste dine oplysninger selv.")
    return _ok(til_guide(aflaesning, foedselsdato_fra_rapport(forside), _satsaar()))
