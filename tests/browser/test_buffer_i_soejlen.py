"""Feature 027 — bufferen i søjlerne: "Fra din buffer" i en ny farve op til linjen, og det, der
sættes til side over linjen, skraveret. Syntetisk rapport: o1 kapitalpension ved 65 år i bufferen."""
import pytest

pytestmark = pytest.mark.browser


def test_fra_din_buffer_er_en_serie_i_soejlen(resultat):
    v = resultat.evaluate("tilstand.v.graf")
    ds = resultat.evaluate("""() => tilstand.graf.data.datasets.filter(d => d.label === 'Fra din buffer')
        .map(d => ({ data: d.data, stack: d.stack, farve: d.backgroundColor }))""")
    assert len(ds) == 1 and ds[0]["stack"] == "netto"
    assert ds[0]["data"] == [None if x is None else round(x) for x in v["fra_buffer"]]
    assert any(x for x in ds[0]["data"])  # den syntetiske plan bruger af bufferen
    assert ds[0]["farve"] == resultat.evaluate("css('--kilde-buffer')")
    assert "Fra din buffer" in resultat.inner_text("#farveforklaring")
    assert "Sættes til side" in resultat.inner_text("#farveforklaring")


def test_soejlen_naar_linjen_naar_bufferen_bruges(resultat):
    v = resultat.evaluate("tilstand.v.graf")
    for i, fra in enumerate(v["fra_buffer"]):
        if fra:
            kilder = sum(s["vaerdier"][i] for s in v["serier"])
            til = v["til_side"][i]
            assert kilder + fra == pytest.approx(v["jaevn"][i] + til["skat"] + til["indskud"], abs=0.5)


def test_til_side_er_skraveret_over_linjen(resultat):
    v = resultat.evaluate("tilstand.v.graf")
    aar = [i for i, t in enumerate(v["til_side"]) if t and t["buffer"] >= 1]
    assert aar, "den syntetiske plan sætter noget til side"
    felter = resultat.evaluate("tilstand.graf.$tilSide.map(f => f.i)")
    assert set(aar) <= set(felter)
    # Feltet starter ved linjen og slutter ved søjlens top.
    f = resultat.evaluate(f"tilstand.graf.$tilSide.find(f => f.i === {aar[0]})")
    y = resultat.evaluate(f"""() => {{ const s = tilstand.graf.scales.y;
        return [s.getPixelForValue(Math.round(tilstand.v.graf.jaevn[{aar[0]}])),
                s.getPixelForValue(tilstand.graf.data.datasets.filter(d => d.stack === 'netto')
                  .reduce((sum, d) => sum + (d.data[{aar[0]}] || 0), 0))]; }}""")
    assert f["y1"] == pytest.approx(y[0], abs=1) and f["y0"] == pytest.approx(y[1], abs=1)


def test_tabellen_har_buffer_kolonner(resultat):
    hoved = resultat.locator("#graf-tabel th").all_text_contents()
    assert "Fra din buffer" in hoved and "Sættes til side" in hoved


def test_forklaringen_og_buffergrafen(resultat):
    tekst = resultat.inner_text("#jaevn-forklaring")
    assert "fra din buffer" in tekst and "skraverede" in tekst and "aldrig i minus" in tekst
    titel = resultat.evaluate("tilstand.buffergraf.options.plugins.title.text")
    assert titel.startswith("Din buffer")
    assert resultat.evaluate("tilstand.buffergraf.data.datasets[0].borderColor") == resultat.evaluate("css('--kilde-buffer')")
