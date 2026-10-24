"""HTTP-API for pensionsoverblikket (contracts/api.md).

Stateless: input lever kun i requesten og logges ikke (Princip VII).
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from pensionskerne import UgyldigtInput, beregn, register

from .oversaet import til_kerne
from .visning import byg_visning

STATIC = Path(__file__).parent / "static"

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
