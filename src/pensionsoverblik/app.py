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


def beregn(guide_json: str, idag: str) -> dict:
    try:
        try:
            data = json.loads(guide_json)
        except ValueError:
            raise UgyldigtInput("body", "Forespørgslen kunne ikke læses") from None
        try:
            dato = date.fromisoformat(idag)
        except ValueError:
            raise UgyldigtInput("idag", "Ugyldig dato fra browseren") from None
        profil, antagelser = til_kerne(data)
        visning = byg_visning(kerne_beregn(profil, antagelser, _satsaar(), dato))
    except UgyldigtInput as e:
        return _fejl("ugyldigt_input", e.besked, e.felt)
    visning["graenser"] = graenser(profil, _satsaar())
    return _ok(visning)


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
