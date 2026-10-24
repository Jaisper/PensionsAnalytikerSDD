"""T004 — POST /api/pdf og GET /api/pdf/status med falsk aflæser (US1, US3, SC-002, SC-003)."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pensionsoverblik import api
from pensionsoverblik.pdfimport.aflaeser import Aflaesning, AflaestOrdning, AflaesningFejl, Periode
from tests.app.pdfhjaelp import RAPPORT, lav_pdf

klient = TestClient(api.app)


class FalskAflaeser:
    def __init__(self, svar=None, fejl=None):
        self.modtaget: list[str] = []
        self.svar = svar or Aflaesning(atp_aarlig=17_000, ordninger=[AflaestOrdning(
            selskab="Danica", aftalenr="123456", produkttype="Ratepension", kategori="ratepension",
            saldo=1_200_000, aarlig_indbetaling=None, tidligste_udbetalingsalder=63, aftalt_udbetalingsalder=None,
            udbetalingsperioder=[Periode(etiket="63-72 år", aarligt_beloeb=130_000)], afgift_betalt=None)])
        self.fejl = fejl

    async def aflaes(self, tekst: str) -> Aflaesning:
        self.modtaget.append(tekst)
        if self.fejl:
            raise self.fejl
        return self.svar


@pytest.fixture
def falsk(monkeypatch):
    f = FalskAflaeser()
    monkeypatch.setattr(api, "AFLAESER", f)
    return f


def post(data: bytes, samtykke=True):
    headers = {"Content-Type": "application/pdf"}
    if samtykke:
        headers["X-Samtykke"] = "ja"
    return klient.post("/api/pdf", content=data, headers=headers)


def test_status_slaaet_fra_uden_aflaeser(monkeypatch):
    monkeypatch.setattr(api, "AFLAESER", None)
    assert klient.get("/api/pdf/status").json() == {"aktiv": False}
    assert post(lav_pdf(RAPPORT)).status_code == 503


def test_status_aktiv(falsk):
    assert klient.get("/api/pdf/status").json() == {"aktiv": True}


def test_kraever_samtykke(falsk):
    r = post(lav_pdf(RAPPORT), samtykke=False)
    assert r.status_code == 400 and r.json()["felt"] == "samtykke"
    assert falsk.modtaget == []


def test_ikke_pdf(falsk):
    r = post(b"dette er ikke en pdf")
    assert r.status_code == 422 and r.json()["kode"] == "ikke_pdf"


def test_for_stor(falsk, monkeypatch):
    monkeypatch.setattr(api, "MAKS_PDF_BYTES", 100)
    r = post(lav_pdf(RAPPORT))
    assert r.status_code == 413 and "MB" in r.json()["besked"]


def test_scannet(falsk):
    r = post(lav_pdf([[]]))
    assert r.status_code == 422 and r.json()["kode"] == "ingen_tekst"


def test_succes_og_ingen_cpr_sendt(falsk):
    r = post(lav_pdf(RAPPORT))
    assert r.status_code == 200
    g = r.json()
    assert g["person"]["foedselsdato"] == "1963-05-01"
    assert g["atp_aarlig"] == 17_000
    assert g["ordninger"][0]["udbetaling_aar"] == 10 and g["ordninger"][0]["oprettet"] == "2007_2017"
    sendt = "".join(falsk.modtaget)
    assert "010563" not in sendt and "[CPR fjernet]" in sendt
    assert "Reklame" not in sendt  # kun relevante sider


def test_aflaeser_fejl_giver_dansk_besked(monkeypatch):
    monkeypatch.setattr(api, "AFLAESER", FalskAflaeser(fejl=AflaesningFejl("timeout", "Det tog for lang tid.")))
    r = post(lav_pdf(RAPPORT))
    assert r.status_code == 502 and r.json()["kode"] == "timeout"
    assert "indtaste" in r.json()["besked"]


def test_ingen_filer_skrevet(falsk, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    foer = {p for p in Path(os.getcwd()).rglob("*")}
    post(lav_pdf(RAPPORT))
    assert {p for p in Path(os.getcwd()).rglob("*")} == foer
