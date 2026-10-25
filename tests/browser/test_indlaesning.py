"""Feature 005 T009 — indlæsning af beregningsmotoren (US3, FR-006)."""
import pytest

pytestmark = pytest.mark.browser

WASM = "**/pyodide.asm.wasm"


def _udfyld_guide(side):
    side.fill("#foedselsdato", "1963-05-01")
    side.fill("#kommune", "Aarhus")
    side.click("#naeste")
    side.click("#naeste")


def test_banner_mens_motoren_indlaeses_og_guiden_kan_bruges(ny_side):
    holdt = []
    ny_side.route(WASM, lambda r: holdt.append(r))
    ny_side.goto(ny_side.base_url)
    ny_side.wait_for_function("() => document.querySelector('#motor-fremdrift').value > 0")
    assert ny_side.is_visible("#motor") and "klar" in ny_side.inner_text("#motor-tekst")
    assert ny_side.get_attribute("#motor", "role") == "status"
    ny_side.fill("#foedselsdato", "1963-05-01")  # guiden kan udfyldes imens
    holdt[0].continue_()
    ny_side.wait_for_selector("#motor", state="hidden")


def test_beregn_foer_motoren_er_klar_regner_automatisk(ny_side):
    holdt = []
    ny_side.route(WASM, lambda r: holdt.append(r))
    ny_side.goto(ny_side.base_url)
    ny_side.wait_for_function("() => document.querySelector('#motor-fremdrift').value > 0")
    _udfyld_guide(ny_side)
    ny_side.click("#naeste")  # "Se min pension", før motoren er klar
    assert ny_side.is_hidden("#resultat")
    holdt[0].continue_()
    ny_side.wait_for_selector("#resultat:not([hidden])")
    assert ny_side.fejl == []


def test_fejl_ved_indlaesning_giver_besked_og_proev_igen(ny_side):
    ny_side.add_init_script("globalThis.motorFristMs = 3000")
    ny_side.route(WASM, lambda r: r.abort())  # Pyodide hænger i stedet for at fejle → fristen
    ny_side.goto(ny_side.base_url)
    ny_side.wait_for_selector("#motor-igen:not([hidden])")
    assert "prøv igen" in ny_side.inner_text("#motor-tekst").lower()
    assert ny_side.get_attribute("#motor", "class").split().count("motor--fejl") == 1
    ny_side.unroute(WASM)
    ny_side.evaluate("globalThis.motorFristMs = 120000")  # normal frist ved genstart
    ny_side.click("#motor-igen")
    ny_side.wait_for_selector("#motor", state="hidden")
    assert ny_side.evaluate("kald('kommuner').then((k) => k.length)") == 98


def test_motoren_er_klar_uden_pdflaeseren(ny_side):
    """Opstarten venter ikke på PDF-læseren (R005). Fejler den, virker beregningen stadig."""
    ny_side.route("**/cryptography-*.whl", lambda r: r.abort())
    ny_side.goto(ny_side.base_url)
    ny_side.wait_for_selector("#motor", state="hidden")
    assert ny_side.evaluate("kald('kommuner').then((k) => k.length)") == 98
    fejl = ny_side.evaluate("kald('pdf', new Uint8Array([37, 80, 68, 70]).buffer).then(() => null, (e) => String(e))")
    assert fejl
    ny_side.unroute("**/cryptography-*.whl")
    svar = ny_side.evaluate("kald('pdf', new Uint8Array([1, 2, 3]).buffer)")  # prøver igen ved næste PDF
    assert svar["fejl"]["kode"] == "ikke_pdf"


def test_uden_webassembly_besked_om_nyere_browser(ny_side):
    ny_side.add_init_script("delete globalThis.WebAssembly")
    ny_side.goto(ny_side.base_url)
    assert "nyere version" in ny_side.inner_text("#motor-tekst")
    assert ny_side.is_hidden("#motor-igen")
