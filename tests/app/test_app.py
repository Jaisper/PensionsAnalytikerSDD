"""Feature 005 T003 — indgangspunktet, som browserens worker kalder (D1). Samme svar og fejl som
de tidligere endpoints /api/kommuner, /api/beregn og /api/pdf, men som data i stedet for HTTP."""
import json
import os
from pathlib import Path

import pytest

from pensionsoverblik import app
from pensionsoverblik.pdfimport.aflaeser import Aflaesning, AflaestOrdning, AflaesningFejl, Periode
from tests.app.pdfhjaelp import RAPPORT, lav_pdf
from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF
from tests.app.test_oversaet import GUIDE

IDAG = "2026-10-25"


def beregn(guide, idag=IDAG):
    return app.beregn(json.dumps(guide), idag)


# --- kommuner -----------------------------------------------------------------------------------

def test_kommuner_sorteret_med_navne():
    r = app.kommuner()
    assert len(r) == 98
    assert {"noegle": "kobenhavn", "navn": "København"} in r
    assert [k["navn"] for k in r] == sorted((k["navn"] for k in r), key=str.casefold)


# --- beregn -------------------------------------------------------------------------------------

def test_beregn_ok():
    r = beregn(GUIDE)
    assert r["ok"] is True
    v = r["data"]
    assert v["hovedtal"]["maaned"] > 0 and v["folkepensionsalder"] == 68
    assert v["graenser"]["ordninger"]["o1"] == {"tidligste": 63, "oplyst": False}


def test_beregn_er_deterministisk_for_given_dato():
    assert beregn(GUIDE) == beregn(GUIDE)


def test_beregn_feltfejl_fra_kernen():
    r = beregn({**GUIDE, "person": {**GUIDE["person"], "foedselsdato": "1950-01-01"}})
    assert r["ok"] is False
    assert r["fejl"]["kode"] == "ugyldigt_input"
    assert r["fejl"]["felt"] == "foedselsdato" and "1955" in r["fejl"]["besked"]


def test_beregn_feltfejl_fra_oversaettelse():
    r = beregn({"person": {}, "ordninger": []})
    assert r["ok"] is False and r["fejl"]["felt"].startswith("person.")


def test_beregn_ulaeselig_json():
    r = app.beregn("{ikke json", IDAG)
    assert r["ok"] is False and r["fejl"]["felt"] == "body"


def test_beregn_ugyldig_dato_fra_browseren():
    r = beregn(GUIDE, idag="i går")
    assert r["ok"] is False and r["fejl"]["felt"] == "idag"


def test_svar_kan_serialiseres_til_json():
    json.dumps(beregn(GUIDE), allow_nan=False)


# --- pdf ----------------------------------------------------------------------------------------

class FalskAflaeser:
    def __init__(self, svar=None, fejl=None):
        self.modtaget: list[bytes] = []
        self.svar = svar or Aflaesning(atp_aarlig=17_000, ordninger=[AflaestOrdning(
            selskab="Danica", aftalenr="123456", produkttype="Ratepension", kategori="ratepension",
            saldo=1_200_000, aarlig_indbetaling=None, tidligste_udbetalingsalder=63, aftalt_udbetalingsalder=None,
            udbetalingsperioder=[Periode(etiket="63-72 år", aarligt_beloeb=130_000)], afgift_betalt=None)])
        self.fejl = fejl

    def aflaes(self, data: bytes) -> Aflaesning:
        self.modtaget.append(data)
        if self.fejl:
            raise self.fejl
        return self.svar


@pytest.fixture
def falsk(monkeypatch):
    f = FalskAflaeser()
    monkeypatch.setattr(app, "AFLAESER", f)
    return f


def test_ikke_pdf(falsk):
    r = app.pdf(b"dette er ikke en pdf")
    assert r == {"ok": False, "fejl": {"kode": "ikke_pdf", "felt": None, "besked": r["fejl"]["besked"]}}


def test_for_stor(falsk, monkeypatch):
    monkeypatch.setattr(app, "MAKS_PDF_BYTES", 100)
    r = app.pdf(lav_pdf(RAPPORT))
    assert r["fejl"]["kode"] == "for_stor" and "MB" in r["fejl"]["besked"]
    assert not falsk.modtaget


def test_scannet(falsk):
    assert app.pdf(lav_pdf([[]]))["fejl"]["kode"] == "ingen_tekst"


def test_succes(falsk):
    r = app.pdf(lav_pdf(RAPPORT))
    assert r["ok"] is True
    g = r["data"]
    assert g["person"]["foedselsdato"] == "1963-05-01"
    assert g["atp_aarlig"] == 17_000
    assert g["ordninger"][0]["udbetaling_aar"] == 10 and g["ordninger"][0]["oprettet"] == "2007_2017"
    assert falsk.modtaget[0].startswith(b"%PDF-")


def test_aflaeser_fejl_giver_dansk_besked(monkeypatch):
    monkeypatch.setattr(app, "AFLAESER", FalskAflaeser(fejl=AflaesningFejl("ukendt_format", "Det ligner ikke en rapport.")))
    r = app.pdf(lav_pdf(RAPPORT))
    assert r["fejl"]["kode"] == "ukendt_format" and "indtaste" in r["fejl"]["besked"]


def test_rigtig_parser_paa_syntetisk_rapport():
    r = app.pdf(RAPPORT_PDF)
    assert r["ok"] is True and r["data"]["ordninger"]


def test_ingen_filer_skrevet(falsk, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    foer = set(Path(os.getcwd()).rglob("*"))
    app.pdf(lav_pdf(RAPPORT))
    assert set(Path(os.getcwd()).rglob("*")) == foer


# --- optimer (feature 007) ----------------------------------------------------------------------

DAARLIG_PLAN = {
    **GUIDE,
    "ordninger": [
        {"id": "o1", "type": "ratepension", "saldo": 1500000, "aarlig_indbetaling": 0, "udbetaling_start_alder": 75,
         "udbetaling_aar": 10, "oprettet": "2010-01-01"},
        {"id": "o2", "type": "livsvarig", "saldo": 600000, "aarlig_indbetaling": 0, "udbetaling_start_alder": 66,
         "oprettet": "2010-01-01"},
    ],
}


def anvend_plan(guide, plan):
    ny = json.loads(json.dumps(guide))
    for o in ny["ordninger"]:
        o.update(plan["ordninger"].get(o["id"], {}))
    ny["antagelser"]["folkepension_opsaettelse_aar"] = plan["folkepension_opsaettelse_aar"]
    return ny


def test_optimer_format_og_anvendt_plan_giver_efter():
    from datetime import date

    from pensionskerne import beregn as kerne_beregn
    from pensionskerne.optimering import fast_niveau, vindue
    from pensionsoverblik.oversaet import til_kerne

    fremdrift = []
    r = app.optimer(json.dumps(DAARLIG_PLAN), IDAG, lambda n, i_alt: fremdrift.append((n, i_alt)))
    assert r["ok"] is True
    d = r["data"]
    assert d["forbedret"] is True and d["efter"] > d["foer"]
    assert d["efter"] % 100 == 0 and d["foer"] % 100 == 0
    assert {"id", "felt", "fra", "til"} <= set(d["aendringer"][0])
    assert all(a["fra"] != a["til"] for a in d["aendringer"])
    assert d["evalueret"] <= d["mulige"] and isinstance(d["udtoemmende"], bool)
    assert fremdrift and fremdrift[-1][0] == fremdrift[-1][1]
    json.dumps(r, allow_nan=False)

    def niveau(guide):
        p, a = til_kerne(guide)
        return fast_niveau(kerne_beregn(p, a, 2026, date.fromisoformat(IDAG)), vindue(kerne_beregn(*til_kerne(DAARLIG_PLAN), 2026, date.fromisoformat(IDAG))))

    assert round(niveau(anvend_plan(DAARLIG_PLAN, d["plan"])), -2) == d["efter"]
    assert round(niveau(DAARLIG_PLAN), -2) == d["foer"]


def test_optimer_feltfejl_som_beregn():
    r = app.optimer(json.dumps({"person": {}, "ordninger": []}), IDAG)
    assert r["ok"] is False and r["fejl"]["felt"].startswith("person.")


def test_optimer_i_buffer_fra_guiden():
    guide = {**GUIDE, "ordninger": [*GUIDE["ordninger"],
             {"id": "o9", "type": "aldersopsparing", "saldo": 200000, "aarlig_indbetaling": 0,
              "udbetaling_start_alder": 67, "oprettet": "2010-01-01", "i_buffer": False}]}
    d = app.optimer(json.dumps(guide), IDAG)["data"]
    assert "o9" not in d["plan"]["ordninger"]
    assert all(a["id"] != "o9" for a in d["aendringer"])
