"""T003 — aflæsning → guidedata: deterministisk og med usikkerheder (FR-005, FR-006, US2)."""
from datetime import date

import pytest

from pensionsoverblik.pdfimport.aflaeser import Aflaesning, AflaestOrdning, Periode
from pensionsoverblik.pdfimport.omsaet import til_guide

FOEDT = date(1963, 5, 1)  # folkepensionsalder 68


def ordning(**kw) -> AflaestOrdning:
    standard = dict(selskab="Danica", aftalenr="123", produkttype="Ratepension", kategori="ratepension",
                    saldo=1_000_000, aarlig_indbetaling=40_000, tidligste_udbetalingsalder=63,
                    aftalt_udbetalingsalder=65, udbetalingsperioder=[Periode(etiket="65-74 år", aarligt_beloeb=110_000)],
                    afgift_betalt=None)
    return AflaestOrdning(**{**standard, **kw})


def guide(*ordninger, atp=None, foedt=FOEDT):
    return til_guide(Aflaesning(ordninger=list(ordninger), atp_aarlig=atp), foedt, 2026)


def test_ratepension_fuldt_aflaest():
    g = guide(ordning())
    o = g["ordninger"][0]
    assert g["person"]["foedselsdato"] == "1963-05-01"
    assert o == {**o, "type": "ratepension", "saldo": 1_000_000, "aarlig_indbetaling": 40_000,
                 "udbetaling_start_alder": 65, "udbetaling_aar": 10, "oprettet": "2007_2017",
                 "kilde": "Danica · aftale 123", "tidligste_udbetalingsalder": 63}
    # Selskabet har oplyst tidligste alder → oprettelsen er ikke "udledt"; kernen bruger den oplyste alder
    assert not any("udledt" in u for u in o["usikkerheder"])


@pytest.mark.parametrize("tidligste,oprettet", [(63, "2007_2017"), (65, "fra2018"), (60, "foer2007"), (61, "ved_ikke"), (64, "ved_ikke")])
def test_oprettelse_udledes_af_tidligste_alder(tidligste, oprettet):
    assert guide(ordning(tidligste_udbetalingsalder=tidligste))["ordninger"][0]["oprettet"] == oprettet


def test_oprettelse_ukendt_uden_foedselsdato():
    g = guide(ordning(), foedt=None)
    assert g["ordninger"][0]["oprettet"] == "ved_ikke"
    assert any("Fødselsdato" in b for b in g["bemaerkninger"])


def test_folkepension_og_forsikring_ignoreres_atp_bruges():
    g = guide(ordning(kategori="folkepension"), ordning(kategori="forsikring"),
              ordning(kategori="atp", udbetalingsperioder=[Periode(etiket="Fra 68 år", aarligt_beloeb=18_000)]))
    assert g["ordninger"] == [] and g["atp_aarlig"] == 18_000


def test_atp_fra_topniveau_vinder():
    assert guide(atp=17_000)["atp_aarlig"] == 17_000


def test_kapitalpension_med_betalt_afgift_bevarer_typen():
    """Feature 009 (FR-011): typen bevares, og afgift_betalt sættes — før blev den stille lavet
    om til aldersopsparing."""
    o = guide(ordning(kategori="kapitalpension", afgift_betalt=True))["ordninger"][0]
    assert o["type"] == "kapitalpension" and o["afgift_betalt"] is True
    assert any("afgiften er betalt" in u for u in o["usikkerheder"])
    ikke = guide(ordning(kategori="kapitalpension", afgift_betalt=False))["ordninger"][0]
    assert ikke["type"] == "kapitalpension" and ikke["afgift_betalt"] is False


def test_ukendt_type_gaettes_og_markeres():
    o = guide(ordning(kategori="ukendt", produkttype="Markedsrente"))["ordninger"][0]
    assert o["type"] == "livsvarig" and any("Typen" in u for u in o["usikkerheder"])


def test_manglende_saldo_og_startalder():
    o = guide(ordning(saldo=None, aftalt_udbetalingsalder=None, tidligste_udbetalingsalder=None))["ordninger"][0]
    assert o["saldo"] is None and o["udbetaling_start_alder"] is None
    assert any("Saldo" in u for u in o["usikkerheder"]) and any("Startalder" in u for u in o["usikkerheder"])


def test_startalder_fra_tidligste_markeres():
    o = guide(ordning(aftalt_udbetalingsalder=None))["ordninger"][0]
    assert o["udbetaling_start_alder"] == 63 and any("tidligste" in u for u in o["usikkerheder"])


@pytest.mark.parametrize("perioder,aar", [
    (["65-79 år"], 15), (["65-69 år", "70-74 år"], 10), (["65 år", "66-74 år"], 10),
])
def test_rateperiode_aflaeses(perioder, aar):
    o = guide(ordning(udbetalingsperioder=[Periode(etiket=p, aarligt_beloeb=1) for p in perioder]))["ordninger"][0]
    assert o["udbetaling_aar"] == aar


def test_rateperiode_uden_for_lovens_rammer_bliver_10_og_markeres():
    o = guide(ordning(udbetalingsperioder=[Periode(etiket="Fra 65 år", aarligt_beloeb=1)]))["ordninger"][0]
    assert o["udbetaling_aar"] == 10 and any("periode" in u for u in o["usikkerheder"])


def test_livsvarig_har_ingen_periode():
    assert guide(ordning(kategori="livsvarig"))["ordninger"][0]["udbetaling_aar"] is None

