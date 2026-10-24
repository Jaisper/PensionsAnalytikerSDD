"""HTTP-API for pensionsoverblikket (contracts/api.md).

Stateless: input lever kun i requesten og logges ikke (Princip VII).
"""
from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pensionskerne import UgyldigtInput, beregn, register

from .oversaet import til_kerne
from .pdfimport.aflaeser import AflaesningFejl, vaelg_aflaeser
from .pdfimport.omsaet import til_guide
from .pdfimport.tekst import PdfFejl, fjern_cpr, relevante_sider, udtraek_sider
from .visning import byg_visning

STATIC = Path(__file__).parent / "static"
MAKS_PDF_BYTES = 25 * 1024 * 1024
AFLAESER = vaelg_aflaeser()  # None = PDF-indlæsning slået fra (FR-009)

app = FastAPI(title="Pensionsoverblik", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _satsaar() -> int:
    return max(register.satsaar())


@app.exception_handler(UgyldigtInput)
async def _ugyldigt_input(_: Request, fejl: UgyldigtInput) -> JSONResponse:
    return JSONResponse({"felt": fejl.felt, "besked": fejl.besked}, status_code=422)


@app.get("/", include_in_schema=False)
async def forside() -> FileResponse:
    return FileResponse(STATIC / "index.html", media_type="text/html; charset=utf-8")


@app.get("/api/kommuner")
async def kommuner() -> list[dict]:
    navne = register.kommunenavne(_satsaar())
    return sorted(({"noegle": k, "navn": v} for k, v in navne.items()), key=lambda k: k["navn"].casefold())


@app.post("/api/beregn")
async def beregn_api(request: Request) -> dict:
    try:
        data = json.loads(await request.body())
    except ValueError:
        raise UgyldigtInput("body", "Forespørgslen kunne ikke læses") from None
    profil, antagelser = til_kerne(data)
    return byg_visning(beregn(profil, antagelser, _satsaar(), date.today()))


def _fejl(status: int, kode: str, besked: str, felt: str | None = None) -> JSONResponse:
    return JSONResponse({"kode": kode, "besked": besked, "felt": felt}, status_code=status)


@app.get("/api/pdf/status")
async def pdf_status() -> dict:
    return {"aktiv": AFLAESER is not None}


@app.post("/api/pdf")
async def pdf_import(request: Request):
    """Aflæser en PensionsInfo-rapport til guidedata. Intet gemmes (FR-008)."""
    if AFLAESER is None:
        return _fejl(503, "slaaet_fra", "Automatisk aflæsning er ikke slået til. Indtast dine oplysninger selv.")
    if request.headers.get("x-samtykke") != "ja":
        return _fejl(400, "samtykke", "Sæt flueben for at give samtykke, før rapporten kan aflæses.", felt="samtykke")
    if int(request.headers.get("content-length") or 0) > MAKS_PDF_BYTES:
        return _fejl(413, "for_stor", f"Filen er for stor. Den må højst fylde {MAKS_PDF_BYTES // 1024 // 1024} MB.")
    data = await request.body()
    if len(data) > MAKS_PDF_BYTES:
        return _fejl(413, "for_stor", f"Filen er for stor. Den må højst fylde {MAKS_PDF_BYTES // 1024 // 1024} MB.")
    try:
        sider = await asyncio.to_thread(udtraek_sider, data)
    except PdfFejl as e:
        return _fejl(422, e.kode, e.besked)

    _, foedselsdato = fjern_cpr("\n".join(sider))
    tekst, _ = fjern_cpr(relevante_sider(sider))
    try:
        aflaesning = await AFLAESER.aflaes(tekst)
    except AflaesningFejl as e:
        return _fejl(502, e.kode, f"{e.besked} Du kan i stedet indtaste dine oplysninger selv.")
    return til_guide(aflaesning, foedselsdato, _satsaar())
