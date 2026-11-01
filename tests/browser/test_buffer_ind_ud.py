"""Feature 029 — buffergrafen viser ind, ud og saldo pr. år i samme kolonner som søjlegrafen.
Syntetisk rapport: o1 kapitalpension ved 65 år i bufferen."""
import pytest

pytestmark = pytest.mark.browser


def datasaet(side):
    return side.evaluate("""() => Object.fromEntries(tilstand.buffergraf.data.datasets.map(d => [d.label,
        { data: d.data, type: d.type || 'bar', stack: d.stack || null }]))""")


def test_ind_ud_og_saldo(resultat):
    g = resultat.evaluate("tilstand.v.graf")
    ds = datasaet(resultat)
    assert set(ds) == {"Saldo i bufferen", "Ind i bufferen", "Sættes til side", "Fra din buffer"}
    assert ds["Saldo i bufferen"]["type"] == "line"
    assert ds["Saldo i bufferen"]["data"] == [None if x is None else round(x) for x in g["buffer"]]
    assert ds["Ind i bufferen"]["data"] == [None if x is None else round(x) for x in g["buffer_ind"]]
    assert ds["Fra din buffer"]["data"] == [None if x is None else -round(x * 12) for x in g["fra_buffer"]]
    i65 = g["aldre"].index(65)
    assert ds["Ind i bufferen"]["data"][i65] > 100_000  # kapitalpensionen kommer ind ved 65


def test_ud_foelger_soejlegrafen(resultat):
    # Samme år har "Fra din buffer" i begge grafer.
    hoved = resultat.evaluate("tilstand.graf.data.datasets.find(d => d.label === 'Fra din buffer').data")
    buffer = datasaet(resultat)["Fra din buffer"]["data"]
    assert [bool(x) for x in hoved] == [bool(x) for x in buffer]
    assert resultat.evaluate("""tilstand.buffergraf.data.datasets.find(d => d.label === 'Fra din buffer').backgroundColor""") \
        == resultat.evaluate("css('--kilde-buffer')")


def test_forklaring_og_tabel(resultat):
    assert "Ind i bufferen" in resultat.inner_text("#farveforklaring")
    assert "Saldo i bufferen" in resultat.inner_text("#farveforklaring")
    assert "Ind i bufferen (pr. år)" in resultat.locator("#graf-tabel th").all_text_contents()
    assert "Op er det, der kommer ind" in resultat.inner_text("#jaevn-forklaring")
