"""Content-Security-Policy (metodebeskrivelsens fund M5): browseren blokerer selv forbindelser til andre
domæner fra siden, og et helt forløb giver ingen overtrædelser. GitHub Pages kan ikke sætte headere, så
politikken står i et <meta>-tag. Den dækker siden; workeren er dækket af kodegennemgang og
netværkstesten i test_pyodide.py."""
import pytest

from tests.browser.conftest import koer_guide, vent_paa_planen

pytestmark = pytest.mark.browser

OVERTRAEDELSER = """window.__csp = [];
document.addEventListener('securitypolicyviolation',
  (e) => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI));"""


@pytest.fixture
def side_med_csp(ny_side):
    s = ny_side
    s.add_init_script(OVERTRAEDELSER)
    s.goto(s.base_url)
    s.evaluate("motorKlar")
    return s


def politik(side):
    return side.get_attribute('meta[http-equiv="Content-Security-Policy"]', "content")


def test_politikken_findes(side_med_csp):
    p = politik(side_med_csp)
    assert p is not None
    direktiver = {d.split()[0]: d.split()[1:] for d in p.split(";") if d.strip()}
    assert direktiver["default-src"] == ["'self'"]
    assert direktiver["connect-src"] == ["'self'"]
    assert direktiver["object-src"] == ["'none'"]
    assert direktiver["form-action"] == ["'none'"]
    assert "'unsafe-eval'" not in direktiver["script-src"]


def test_forbindelser_til_andre_domaener_blokeres(side_med_csp):
    s = side_med_csp
    fejl = s.evaluate("""async () => { try { await fetch('https://example.org/x', {method: 'POST', body: 'data'});
                                           return null; } catch (e) { return String(e); } }""")
    assert fejl is not None
    s.evaluate("() => { new Image().src = 'https://example.org/pixel.gif'; }")
    s.wait_for_timeout(300)
    blokeret = s.evaluate("window.__csp")
    assert any("connect-src" in x and "example.org" in x for x in blokeret)
    assert any("img-src" in x and "example.org" in x for x in blokeret)


def test_et_helt_forloeb_giver_ingen_overtraedelser(side_med_csp, tmp_path):
    from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

    s = side_med_csp
    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    koer_guide(s, pdf)
    vent_paa_planen(s)
    s.click("#metode-link")
    s.wait_for_selector("#metode:not([hidden])")
    assert s.evaluate("window.__csp") == []
    assert s.fejl == []
