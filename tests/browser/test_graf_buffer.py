"""Feature 008 — engangsbeløb og buffer i grafen, fast beløb som hovedtal (US1–US3).
Syntetisk rapport: o1 kapitalpension ved 65 år (buffer fra start)."""
import pytest

from tests.browser.test_optimering import daarlig_plan, find_forslag

pytestmark = pytest.mark.browser


def test_linjen_hedder_fast_beloeb_og_forklares(resultat):
    forklaring = resultat.inner_text("#farveforklaring")
    assert "Fast beløb, hvis du udjævner" in forklaring and "Jævnt fordelt" not in forklaring
    tekst = resultat.inner_text("#jaevn-forklaring")
    assert "bruger du af opsparingen" in tekst and "sparer du op" in tekst  # ordlyd fra 010


def test_engangsbeloeb_vises_med_buffer_eller_udbetales(resultat):
    liste = resultat.inner_text("#graf-markeringer")
    assert "Kapitalpension" in liste and "→ buffer" in liste and "65" in liste
    resultat.click("#data-panel-knap")
    resultat.locator("#data-panel-form #o1-i_buffer").uncheck()
    resultat.click("#opdater")
    resultat.wait_for_function("() => document.querySelector('#graf-markeringer').innerText.includes('→ udbetales')")
    tabel_hoved = resultat.locator("#graf-tabel th").all_text_contents()  # tabellen ligger i en lukket <details>
    assert "Engangsbeløb" in tabel_hoved and "Buffer" in tabel_hoved


def test_buffergraf_flugter_med_hovedgrafen(resultat):
    assert resultat.locator("#buffergraf").is_visible()
    afvig = resultat.evaluate("""() => {
        const a = tilstand.graf, b = tilstand.buffergraf, n = tilstand.v.graf.aldre.length;
        const ra = a.canvas.getBoundingClientRect(), rb = b.canvas.getBoundingClientRect();
        return [0, n - 1].map(i => Math.abs((ra.left + a.scales.x.getPixelForValue(i)) - (rb.left + b.scales.x.getPixelForValue(i))));
    }""")
    assert max(afvig) <= 2, afvig


def test_hovedtal_er_fast_beloeb(resultat):
    tekst = resultat.inner_text("#hovedtal-forklaring")
    assert "hvis du selv udjævner" in tekst
    v = resultat.evaluate("tilstand.v")
    jaevn = v["graf"]["jaevn"]
    assert v["hovedtal"]["maaned"] == round(min(jaevn), -2)


def test_hovedtal_efter_anvend_er_forslagets_beloeb(resultat):
    daarlig_plan(resultat)
    find_forslag(resultat)
    efter = resultat.evaluate("tilstand.forslag.d.efter")
    resultat.evaluate("window.__f = tilstand.v")
    resultat.get_by_role("button", name="Anvend").click()
    resultat.wait_for_function("() => tilstand.v !== window.__f")
    assert resultat.evaluate("+document.querySelector('#hovedtal').dataset.vaerdi") == efter


def test_axe_og_360(resultat):
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    assert resultat.fejl == []


def test_bufferen_gaar_aldrig_i_minus_og_forklares(resultat):
    """Feature 010: udjævningen låner aldrig."""
    assert min(resultat.evaluate("tilstand.v.graf.buffer")) >= 0
    assert "aldrig i minus" in resultat.inner_text("#jaevn-forklaring")
    assert "opsparing uden for pension" in resultat.evaluate("tilstand.buffergraf.options.plugins.title.text")
