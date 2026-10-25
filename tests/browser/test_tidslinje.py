"""Feature 006 — bjælker, der trækkes (FR-001–FR-010). Kører på den syntetiske rapport:
o1 kapitalpension 65 (tidligste 60), o2 ratepension 67 i 10 år (tidligste 64),
o3 livsvarig 67, o4 livsvarig 70 (tidligste 66) og folkepension 69 (udskyd højst 10 år)."""
import pytest

pytestmark = pytest.mark.browser

HOEJDE_004 = 734  # tidslinjens højde i 004 ved 1366 px med samme rapport (px)


def start(side, oid):
    return side.evaluate(f"tilstand.aktuelleSvar.ordninger.find(o => o.id === '{oid}').udbetaling_start_alder")


def varighed(side, oid):
    return side.evaluate(f"tilstand.aktuelleSvar.ordninger.find(o => o.id === '{oid}').udbetaling_aar")


def opsaettelse(side):
    return side.evaluate("tilstand.aktuelleSvar.antagelser.folkepension_opsaettelse_aar")


def bjaelke(side, rid):
    return side.locator(f'.tl-raekke[data-id="{rid}"] .tl-bjaelke')


def greb(side, rid):
    return side.locator(f'.tl-raekke[data-id="{rid}"] .tl-greb')


def traek(side, element, aar):
    """Træk et element et antal år på aksen med musen (fra elementets midte)."""
    element.scroll_into_view_if_needed()
    boks = element.bounding_box()
    pr_aar = side.evaluate("tilstand.prAar")
    x, y = boks["x"] + boks["width"] / 2, boks["y"] + boks["height"] / 2
    side.mouse.move(x, y)
    side.mouse.down()
    for i in range(1, 6):
        side.mouse.move(x + aar * pr_aar * i / 5, y)
    side.mouse.up()


def marker_resultat(side):
    """Husk det nuværende resultat fra kernen, så vi kan vente på, at der er regnet igen."""
    side.evaluate("window.__forrige = tilstand.v")


def vent_paa_ny_beregning(side):
    # Hovedtallet ændrer sig ikke altid (fx flyttes en ratepension inden for den jævne udbetaling),
    # men grafen kommer altid fra en ny beregning.
    side.wait_for_function("() => tilstand.v !== window.__forrige")


def test_ingen_skydere_i_tidslinjen(resultat):
    assert resultat.locator("#tidslinje input[type=range]").count() == 0
    assert resultat.locator(".tl-raekke").count() == 5


def test_traek_bjaelke_flytter_start_og_regner_igen(resultat):
    marker_resultat(resultat)
    traek(resultat, bjaelke(resultat, "o2"), 2)
    assert start(resultat, "o2") == 69 and varighed(resultat, "o2") == 10
    vent_paa_ny_beregning(resultat)
    assert resultat.evaluate("tilstand.v.graf.aldre.length") > 0
    assert "69–78 år" in resultat.inner_text('.tl-raekke[data-id="o2"] .tl-hoved')


def test_traek_stopper_ved_tidligste_alder(resultat):
    traek(resultat, bjaelke(resultat, "o2"), -10)
    assert start(resultat, "o2") == 64


def test_greb_aendrer_varighed_inden_for_registrets_graenser(resultat):
    traek(resultat, greb(resultat, "o2"), 5)
    assert start(resultat, "o2") == 67 and varighed(resultat, "o2") == 15
    traek(resultat, greb(resultat, "o2"), -12)
    assert varighed(resultat, "o2") == 10


def test_engangsbeloeb_er_et_punkt_der_kan_flyttes(resultat):
    punkt = bjaelke(resultat, "o1")
    assert "tl-bjaelke--engang" in punkt.get_attribute("class")
    traek(resultat, punkt, 3)
    assert start(resultat, "o1") == 68


def test_folkepension_traekkes_til_udskydelse(resultat):
    marker_resultat(resultat)
    traek(resultat, bjaelke(resultat, "folkepension"), 2)
    assert opsaettelse(resultat) == 2
    vent_paa_ny_beregning(resultat)  # tidslinjen tegnes igen efter beregningen — træk først derefter
    traek(resultat, bjaelke(resultat, "folkepension"), -5)
    assert opsaettelse(resultat) == 0


def test_klik_viser_knapper_uden_traek(resultat):
    raekke = resultat.locator('.tl-raekke[data-id="o2"]')
    assert raekke.locator(".tl-trin").is_hidden()
    bjaelke(resultat, "o2").click()
    assert raekke.locator(".tl-trin").is_visible()
    assert start(resultat, "o2") == 67  # et klik flytter ikke
    marker_resultat(resultat)
    raekke.get_by_role("button", name="Start 1 år senere").click()
    assert start(resultat, "o2") == 68
    raekke.get_by_role("button", name="Varighed 1 år længere").click()
    assert varighed(resultat, "o2") == 11
    vent_paa_ny_beregning(resultat)


def test_tastatur(resultat):
    b = bjaelke(resultat, "o2")
    b.focus()
    b.press("ArrowRight")
    b.press("ArrowRight")
    assert start(resultat, "o2") == 69
    b.press("Home")
    assert start(resultat, "o2") == 64
    b.press("PageUp")
    assert start(resultat, "o2") == 69
    g = greb(resultat, "o2")
    g.focus()
    g.press("End")
    assert varighed(resultat, "o2") == 30


def test_aria(resultat):
    b = bjaelke(resultat, "o2")
    assert b.get_attribute("role") == "slider" and b.get_attribute("tabindex") == "0"
    assert (b.get_attribute("aria-valuemin"), b.get_attribute("aria-valuenow")) == ("64", "67")
    assert "67" in b.get_attribute("aria-valuetext")
    assert "Ratepension" in b.get_attribute("aria-label")
    g = greb(resultat, "o2")
    assert (g.get_attribute("role"), g.get_attribute("aria-valuemin"), g.get_attribute("aria-valuemax")) == ("slider", "10", "30")
    assert bjaelke(resultat, "folkepension").get_attribute("aria-valuemax") == "10"


def test_datapanel_er_synkront(resultat):
    traek(resultat, bjaelke(resultat, "o2"), 2)
    resultat.click("#data-panel-knap")
    assert resultat.input_value("#data-panel-form #o2-udbetaling_start_alder") == "69"


def test_bjaelke_flugter_med_grafen(resultat):
    afvig = resultat.evaluate("""() => {
        const g = tilstand.graf, aldre = tilstand.v.graf.aldre, sx = g.scales.x, ramme = g.canvas.getBoundingClientRect();
        return [...document.querySelectorAll('.tl-raekke')].map(r => {
          const b = r.querySelector('.tl-bjaelke');
          if (b.classList.contains('tl-bjaelke--engang')) return 0;
          const start = Math.max(+b.dataset.start, aldre[0]);
          const forventet = ramme.left + sx.getPixelForValue(aldre.indexOf(start)) - tilstand.prAar / 2;
          return Math.abs(b.getBoundingClientRect().left - forventet);
        });
    }""")
    assert max(afvig) <= 2, afvig


def test_maal_mindst_24_px(resultat):
    for e in resultat.locator(".tl-bjaelke, .tl-greb").all():
        boks = e.bounding_box()
        assert boks["height"] >= 24 and boks["width"] >= 24, boks


def test_kompakt_axe_og_360_px(resultat):
    hoejde = resultat.evaluate("document.querySelector('#tidslinje').getBoundingClientRect().height")
    assert hoejde <= 0.7 * HOEJDE_004, hoejde  # SC-001
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    bjaelke(resultat, "o2").click()  # også med knapperne synlige
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    resultat.set_viewport_size({"width": 360, "height": 800})
    # Chart.js skalerer grafen via en ResizeObserver; vent til layoutet har sat sig.
    try:
        resultat.wait_for_function("() => document.documentElement.scrollWidth <= 360", timeout=5000)
    except Exception:
        ud = resultat.evaluate("""() => [...document.querySelectorAll('body *')]
            .filter(e => e.getBoundingClientRect().right > 361 && e.offsetParent !== null)
            .slice(0, 12).map(e => `${e.tagName}#${e.id}.${e.className} ${Math.round(e.getBoundingClientRect().right)}`)""")
        pytest.fail(f"Vandret scroll ved 360 px: {resultat.evaluate('document.documentElement.scrollWidth')} px. Stikker ud: {ud}")
    assert resultat.fejl == []
