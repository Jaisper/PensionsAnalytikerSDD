"""Feature 028 — talrullen: mens den bedste plan søges (007b), ruller hovedtallet som en enarmet
tyveknægt i stedet for at vise den egne plans beløb (fx 0 kr.). Den lander på det endelige beløb."""
import pytest

from tests.browser.conftest import koer_guide, vent_paa_planen

pytestmark = pytest.mark.browser


def til_resultat_uden_at_vente(side, tmp_path):
    from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    koer_guide(side, pdf)


def test_hovedtallet_ruller_mens_planen_soeges_og_lander_paa_beloebet(side, tmp_path):
    til_resultat_uden_at_vente(side, tmp_path)
    side.wait_for_selector("#hovedtal .rulle__hjul", timeout=10000)
    assert side.evaluate("document.body.dataset.plan") == ""
    tal = side.inner_text("#hovedtal")
    assert "Regner" in tal and "0 kr." not in tal
    assert side.locator("#hovedtal .rulle").get_attribute("aria-hidden") == "true"
    assert side.locator("#hovedtal-forklaring").is_hidden() and side.locator("#hovedtal-loen").is_hidden()
    vent_paa_planen(side)
    assert side.locator("#hovedtal .rulle").count() == 0
    vaerdi = side.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    assert side.inner_text("#hovedtal") == side.evaluate(f"`${{kr({vaerdi})}} kr.`")
    assert side.locator("#hovedtal-forklaring").is_visible()
    assert side.fejl == []


def test_uden_animationer_staar_der_kun_prikker(side, tmp_path):
    side.emulate_media(reduced_motion="reduce")
    til_resultat_uden_at_vente(side, tmp_path)
    side.wait_for_function("() => document.body.dataset.plan === ''", timeout=10000)
    assert side.locator("#hovedtal .rulle__hjul").count() == 0
    assert "…" in side.inner_text("#hovedtal")
    vent_paa_planen(side)
    assert side.inner_text("#hovedtal").endswith(" kr.")


def test_aendres_planen_under_soegningen_lander_rullen(side, tmp_path):
    # Fundet af test_pyodide: før rettelsen rullede den for evigt, når søgningen blev kasseret.
    til_resultat_uden_at_vente(side, tmp_path)
    side.wait_for_selector("#hovedtal .rulle__hjul", timeout=10000)
    bjaelke = side.locator(".tl-raekke .tl-bjaelke").first
    bjaelke.focus()
    bjaelke.press("ArrowRight")
    side.wait_for_function("() => !document.querySelector('#hovedtal .rulle') && document.body.dataset.plan === 'klar'",
                           timeout=15000)
    vaerdi = side.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi")
    assert side.inner_text("#hovedtal") == side.evaluate(f"`${{kr({vaerdi})}} kr.`")
    assert side.fejl == []
