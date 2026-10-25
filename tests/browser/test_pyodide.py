"""Feature 005 T007 — siden regner i browseren som CPython (FR-001, FR-007), og intet med
persondata forlader browseren (FR-003, SC-001)."""
import json
import math

import pytest

from pensionsoverblik import app
from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF
from tests.app.test_oversaet import GUIDE

pytestmark = pytest.mark.browser

IDAG = "2026-10-25"
EKSAKTE = ("hovedtal", "graenser", "hovedtal_advarsler", "generelle_advarsler", "folkepensionsalder",
           "satser", "antagelser")
REL_TOLERANCE = 1e-9

PARTNER_GUIDE = {
    **GUIDE,
    "person": {**GUIDE["person"], "civilstand": "gift_samlevende", "foedselsdato": "1960-08-15",
               "partner": {"foedselsdato": "1965-02-01", "oevrig_indkomst_aar": 120000}},
    "ordninger": [
        {**GUIDE["ordninger"][0], "udbetaling_aar": 15},
        {"id": "o2", "type": "livsvarig", "saldo": 900000, "aarlig_indbetaling": 0, "udbetaling_start_alder": 67,
         "oprettet": "2015-01-01"},
        {"id": "o3", "type": "kapitalpension", "saldo": 300000, "aarlig_indbetaling": 0, "udbetaling_start_alder": 66,
         "oprettet": "2000-01-01"},
        {"id": "o4", "type": "aldersopsparing", "saldo": 150000, "aarlig_indbetaling": 0, "udbetaling_start_alder": 67,
         "oprettet": "2015-01-01"},
    ],
    "antagelser": {"afkast_efter_pal": 0.04, "inflation": 0.02, "folkepension_opsaettelse_aar": 3},
}


def _naer(a, b, sti=""):
    """Samme struktur; tal ens inden for REL_TOLERANCE (WebAssemblys libm, research R001)."""
    if isinstance(a, dict) and isinstance(b, dict):
        assert a.keys() == b.keys(), sti
        for k in a:
            _naer(a[k], b[k], f"{sti}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), sti
        for i, (x, y) in enumerate(zip(a, b)):
            _naer(x, y, f"{sti}[{i}]")
    elif isinstance(a, float) or isinstance(b, float):
        assert math.isclose(a, b, rel_tol=REL_TOLERANCE, abs_tol=1e-9), f"{sti}: {a} != {b}"
    else:
        assert a == b, f"{sti}: {a!r} != {b!r}"


def _sammenlign_beregning(browser_svar, cpython_svar):
    assert browser_svar["ok"] == cpython_svar["ok"]
    if not cpython_svar["ok"]:
        assert browser_svar == cpython_svar
        return
    b, c = browser_svar["data"], cpython_svar["data"]
    for k in EKSAKTE:
        assert b[k] == c[k], k
    _naer(b, c)


@pytest.mark.parametrize("guide", [GUIDE, PARTNER_GUIDE], ids=["enlig", "partner"])
def test_beregning_som_cpython(side, guide):
    svar = side.evaluate("([g, d]) => kald('beregn', g, d)", [json.dumps(guide), IDAG])
    _sammenlign_beregning(svar, app.beregn(json.dumps(guide), IDAG))


def test_kernens_feltfejl_som_cpython(side):
    guide = json.dumps({**GUIDE, "person": {**GUIDE["person"], "foedselsdato": "1950-01-01"}})
    assert side.evaluate("([g, d]) => kald('beregn', g, d)", [guide, IDAG]) == app.beregn(guide, IDAG)


def test_kommuner_som_cpython(side):
    assert side.evaluate("kald('kommuner')") == app.kommuner()


def test_pdf_aflaesning_som_cpython(side):
    svar = side.evaluate("(b) => kald('pdf', new Uint8Array(b).buffer)", list(RAPPORT_PDF))
    assert svar == app.pdf(RAPPORT_PDF)
    assert svar["ok"] and svar["data"]["ordninger"]


def test_ikke_pdf_som_cpython(side):
    svar = side.evaluate("(b) => kald('pdf', new Uint8Array(b).buffer)", list(b"ikke en pdf"))
    assert svar == app.pdf(b"ikke en pdf")


def test_intet_forlader_browseren(side, base_url, tmp_path):
    """Helt forløb: upload, guide, resultat og skyder (SC-001). Siden henter kun sine egne filer
    (PDF-læseren i baggrunden, R005), sender aldrig data og henter intet, efter rapporten er læst."""
    assert any(u.endswith("pyodide.asm.wasm") for _, u, _ in side.requests), "workerens requests skal kunne ses"
    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    side.set_input_files("#pdf-fil", str(pdf))
    side.click("#pdf-knap")
    side.wait_for_selector("#pdf-status p")
    efter_pdf = len(side.requests)
    side.fill("#kommune", "Aarhus")
    side.click("#naeste")
    for felt in side.query_selector_all(".ordning input[id$='-saldo']"):
        if not felt.input_value():
            felt.fill("0")
    for felt in side.query_selector_all(".ordning input[id$='-udbetaling_start_alder']"):
        if not felt.input_value():
            felt.fill("70")
    side.click("#naeste")
    side.click("#naeste")
    side.wait_for_selector("#resultat:not([hidden])")
    hovedtal = side.inner_text("#hovedtal")
    skyder = side.locator(".tl-raekke input[type=range]").first
    skyder.focus()
    skyder.press("ArrowRight")
    side.wait_for_function("(h) => document.querySelector('#hovedtal').innerText !== h", arg=hovedtal)
    assert all(m == "GET" and u.startswith(base_url) and not data for m, u, data in side.requests), side.requests
    assert side.requests[efter_pdf:] == []
    assert side.fejl == []
