"""ATP-feltet (tomt eller 0 → ATP's gennemsnit) og markører for engangsbeløb, der ikke overlapper."""
import pytest

pytestmark = pytest.mark.browser


def test_atp_tomt_eller_nul_giver_gennemsnit(resultat):
    resultat.click("#data-panel-knap")
    atp = resultat.locator("#data-panel-form #atp")
    assert atp.get_attribute("placeholder") in (None, "")  # ingen pladsholder, der ligner et svar
    for vaerdi in ("", "0"):
        atp.fill(vaerdi)
        resultat.evaluate("window.__f = tilstand.v")
        resultat.click("#opdater")
        resultat.wait_for_function("() => tilstand.v !== window.__f")
        assert resultat.evaluate("tilstand.aktuelleSvar.person.atp_aarlig") is None
        assert "ATP_SKOENNET" in resultat.evaluate("JSON.stringify(tilstand.v)")  # advarslen står på ATP-kortet


def test_markoerer_overlapper_ikke(resultat):
    """Engangsbeløb i år ved siden af hinanden må ikke skrive oven i hinanden."""
    resultat.evaluate("""() => {
        const g = tilstand.graf, f = css('--kilde-engangs');
        g.$engangs = [
          {alder: 65, farve: f, kort: 'Aldersopsparing ca. 218.000 kr. → buffer'},
          {alder: 66, farve: f, kort: 'Kapitalpension 2 portioner ca. 1.092.000 kr. → buffer'},
          {alder: 65, farve: f, kort: 'Kapitalpension ca. 300.000 kr. → buffer'},
          {alder: 88, farve: f, kort: 'Aldersopsparing ca. 100.000 kr. → udbetales'},
        ];
        g.update('none');
    }""")
    resultat.wait_for_function("() => tilstand.graf.$engangsBokse.length === 4")  # tegnes ved næste frame
    bokse = resultat.evaluate("tilstand.graf.$engangsBokse")
    assert len(bokse) == 4
    for i, a in enumerate(bokse):
        for b in bokse[i + 1:]:
            vandret = a["x1"] <= b["x0"] or b["x1"] <= a["x0"]
            lodret = a["y1"] <= b["y0"] or b["y1"] <= a["y0"]
            assert vandret or lodret, (a, b)
