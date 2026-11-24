"""Feature 039 — "Sådan fungerer løsningen": metodebeskrivelsen som side i løsningen."""
import pytest

from tests.browser.conftest import indlaes_axe
from tests.browser.test_csp import OVERTRAEDELSER

pytestmark = pytest.mark.browser


@pytest.fixture
def metodeside(ny_side):
    s = ny_side
    s.add_init_script(OVERTRAEDELSER)
    s.goto(s.base_url)
    s.click("#saadan-fungerer-link")
    s.wait_for_selector("h1")
    return s


def test_siden_aabnes_fra_forsiden(metodeside):
    s = metodeside
    assert s.url.endswith("saadan-fungerer.html")
    assert "Sådan fungerer" in s.inner_text("h1")
    assert s.locator(".metodedok h2").count() >= 13
    assert s.evaluate("window.__csp") == []
    assert s.fejl == []


def test_indholdsfortegnelsen_virker(metodeside):
    s = metodeside
    links = s.locator(".metodedok__indhold a")
    assert links.count() == 13
    links.nth(1).click()
    assert s.url.endswith("#2-data-privatliv-og-sikkerhed")
    assert s.locator('[id="2-data-privatliv-og-sikkerhed"]').is_visible()


def test_ingen_kode_i_teksten(metodeside):
    tekst = metodeside.inner_text("main")
    for ord_ in (".py", "src/", "tests/", "Regelopslag", "RATEPENSION_LOFT", "`"):
        assert ord_ not in tekst, ord_


def test_axe_og_360(browser, base_url):
    # Siden har ingen scripts og en CSP med script-src 'none', så axe-core kan kun køre i en kontekst, der
    # ser bort fra CSP'en. Politikken selv testes i test_siden_aabnes_fra_forsiden.
    ctx = browser.new_context(locale="da-DK", bypass_csp=True)
    s = ctx.new_page()
    s.goto(base_url + "saadan-fungerer.html")
    indlaes_axe(s)
    fejl = s.evaluate("async () => (await axe.run(document, {runOnly: "
                      "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    s.set_viewport_size({"width": 360, "height": 800})
    s.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    ctx.close()
