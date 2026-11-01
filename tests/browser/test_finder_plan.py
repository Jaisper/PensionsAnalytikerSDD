"""Feature 032 — mens den bedste plan søges (007b), står der "Finder bedste plan …" i stedet for den
egne plans beløb (fx 0 kr.). Erstatter talrullen fra 028."""
import pytest

from tests.browser.conftest import koer_guide, vent_paa_planen

pytestmark = pytest.mark.browser

TEKST = "Finder bedste plan …"


def til_resultat_uden_at_vente(side, tmp_path):
    from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    koer_guide(side, pdf)


def vist_beloeb(side):
    vaerdi = side.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    return side.evaluate(f"`${{kr({vaerdi})}} kr.`")


def test_teksten_staar_mens_planen_soeges_og_beloebet_bagefter(side, tmp_path):
    til_resultat_uden_at_vente(side, tmp_path)
    side.wait_for_function("() => document.body.dataset.plan === ''", timeout=10000)
    assert side.inner_text("#hovedtal") == TEKST
    assert side.locator(".hero__enhed").is_hidden()
    assert side.locator("#resultat-titel").is_visible()  # sektionens navn og første fokus
    assert side.locator("#hovedtal-forklaring").is_hidden() and side.locator("#hovedtal-loen").is_hidden()
    assert TEKST not in side.inner_text("#hovedtal-plan")  # står kun én gang
    assert side.locator("#hovedtal-plan progress").is_visible()
    tekst, fremdrift = side.locator("#hovedtal").bounding_box(), side.locator("#hovedtal-plan progress").bounding_box()
    assert 0 <= fremdrift["y"] - (tekst["y"] + tekst["height"]) < 48  # lige under teksten
    vent_paa_planen(side)
    assert side.inner_text("#hovedtal") == vist_beloeb(side)
    assert side.locator(".hero__enhed").is_visible()
    assert side.locator("#hovedtal-forklaring").is_visible()
    assert side.fejl == []


def test_aendres_planen_under_soegningen_staar_det_nye_beloeb(side, tmp_path):
    # Fundet af test_pyodide i 028: søgningen kasseres, og teksten må ikke blive stående.
    til_resultat_uden_at_vente(side, tmp_path)
    side.wait_for_function("() => document.body.dataset.plan === ''", timeout=10000)
    bjaelke = side.locator(".tl-raekke .tl-bjaelke").first
    bjaelke.focus()
    bjaelke.press("ArrowRight")
    side.wait_for_function("() => document.body.dataset.plan === 'klar'", timeout=15000)
    assert side.inner_text("#hovedtal") == vist_beloeb(side)
    assert side.fejl == []
