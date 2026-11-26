"""Feature 039 — "Sådan fungerer løsningen": metodebeskrivelsen som side i løsningen."""
import pytest

from tests.browser.conftest import indlaes_axe
from tests.browser.test_csp import OVERTRAEDELSER

pytestmark = pytest.mark.browser


@pytest.fixture
def metodeside(ny_side):
    """Siden åbnet direkte (fx et link delt med revisionen)."""
    s = ny_side
    s.add_init_script(OVERTRAEDELSER)
    s.goto(s.base_url + "saadan-fungerer.html")
    s.wait_for_selector("h1")
    return s


def test_aabnes_i_ny_fane_og_beregningen_bliver_staaende(resultat):
    # 039b: beregningen må ikke glemmes. Linket åbner en ny fane, og "Tilbage til beregningen" lukker den.
    s = resultat
    link = s.locator("#saadan-fungerer-link")
    assert link.get_attribute("target") == "_blank" and "noopener" in link.get_attribute("rel")
    assert "(åbner i en ny fane)" in link.inner_text()
    hovedtal = s.inner_text("#hovedtal")
    with s.context.expect_page() as ny:
        link.click()
    side = ny.value
    side.wait_for_load_state("load")  # knappens script er indlæst (defer)
    assert "saadan-fungerer.html?fra=beregning" in side.url and "Sådan fungerer" in side.inner_text("h1")
    assert s.inner_text("#hovedtal") == hovedtal and s.evaluate("tilstand.v !== null")
    with side.expect_event("close", timeout=5000):  # fanen lukkes under klikket
        side.click("#tilbage-til-beregningen")
    assert side.is_closed()
    assert s.inner_text("#hovedtal") == hovedtal


def test_aabnet_direkte_foerer_knappen_til_beregningen(metodeside):
    # Åbnet direkte kan fanen ikke lukkes af siden; så går knappen til beregningen.
    s = metodeside
    s.wait_for_load_state("load")
    s.click("#tilbage-til-beregningen")
    s.wait_for_url(lambda u: "saadan-fungerer" not in u, timeout=5000)
    assert s.evaluate("window.__csp") == []


def test_siden_har_indhold_og_ingen_overtraedelser(metodeside):
    s = metodeside
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
    # 320 px og ikke kun 360: CI's skrifttyper er bredere end Chromes lokalt (fundet i udgivelsen af 039).
    for bredde in (360, 320):
        s.set_viewport_size({"width": bredde, "height": 800})
        s.wait_for_function(f"() => document.documentElement.scrollWidth <= {bredde}", timeout=5000)
    ctx.close()


# ── 041: "Sådan udvikles løsningen" ───────────────────────────────────────────
def test_udviklingsmetoden_aabnes_i_ny_fane_og_kan_lukkes(resultat):
    s = resultat
    link = s.locator("#saadan-udvikles-link")
    assert link.get_attribute("target") == "_blank" and "noopener" in link.get_attribute("rel")
    assert "(åbner i en ny fane)" in link.inner_text()
    hovedtal = s.inner_text("#hovedtal")
    with s.context.expect_page() as ny:
        link.click()
    side = ny.value
    side.wait_for_load_state("load")
    assert "saadan-udvikles.html?fra=beregning" in side.url and "Sådan udvikles" in side.inner_text("h1")
    # Henvisningen til den anden beskrivelse beholder, at fanen er åbnet fra beregningen.
    assert side.get_attribute("a.metodedok__anden", "href").endswith("saadan-fungerer.html?fra=beregning")
    with side.expect_event("close", timeout=5000):
        side.click("#tilbage-til-beregningen")
    assert s.inner_text("#hovedtal") == hovedtal


def test_udviklingsmetoden_indhold_axe_og_360(browser, base_url):
    ctx = browser.new_context(locale="da-DK", bypass_csp=True)
    s = ctx.new_page()
    s.goto(base_url + "saadan-udvikles.html")
    assert s.locator(".metodedok__indhold a").count() == 14
    tekst = s.inner_text("main")
    for ord_ in (".py", "src/", "tests/", "`"):
        assert ord_ not in tekst, ord_
    indlaes_axe(s)
    fejl = s.evaluate("async () => (await axe.run(document, {runOnly: "
                      "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    for bredde in (360, 320):
        s.set_viewport_size({"width": bredde, "height": 800})
        s.wait_for_function(f"() => document.documentElement.scrollWidth <= {bredde}", timeout=5000)
    ctx.close()
