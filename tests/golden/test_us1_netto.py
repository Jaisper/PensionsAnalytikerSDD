"""T020 — US1 ende-til-ende: håndberegnet facit (spec US1, scenarie 1, 4, 7).

Profil: født 1.5.1963 (fp 68), Aarhus 24,52 %, ingen kirkeskat, ratepension 1 mio. over
10 år fra 65 år, afkast 0, inflation og satsregulering 0. INTET AM-bidrag (A1).
"""
import pytest

from pensionskerne import beregn
from tests.conftest import BEREGNINGSDATO, enlig_profil

FLAD = 0.1201 + 0.2452
PF = 54_100


@pytest.fixture
def res(nul_antagelser):
    return beregn(enlig_profil(), nul_antagelser, 2026, BEREGNINGSDATO)


def test_folkepensionsalder(res):
    assert res.folkepensionsalder == 68


def test_us1_s1_rate_uden_am_bidrag(res):
    for alder in (65, 66, 67):
        a = res.aar_ved(alder)
        assert a.personlig_indkomst == pytest.approx(100_000)
        assert a.skat_i_alt == pytest.approx((100_000 - PF) * FLAD)
        assert a.netto_i_alt == pytest.approx(100_000 - (100_000 - PF) * FLAD)


def test_foerste_folkepensionsaar_fra_maaneden_efter(res):
    a = res.aar_ved(68)
    kilder = {k.type: k.brutto for k in a.kilder}
    andel = 7 / 12  # født i maj → udbetaling juni–december
    assert kilder["grundbeloeb"] == pytest.approx(90_528 * andel)
    assert kilder["atp"] == pytest.approx(17_340 * andel)
    tillaeg_aar = 104_748 - 0.309 * (100_000 + 17_340 - 99_200)
    assert kilder["pensionstillaeg"] == pytest.approx(tillaeg_aar * andel)
    assert a.tillaegsprocent == 0
    assert "aeldrecheck" not in kilder  # kræver folkepension pr. 1. januar
    pi = 100_000 + (90_528 + 17_340 + tillaeg_aar) * andel
    assert a.skat_i_alt == pytest.approx((pi - PF) * FLAD)


def test_efter_ratepensionen_fuldt_tillaeg_og_checks(res):
    a = res.aar_ved(75)
    kilder = {k.type: k.brutto for k in a.kilder}
    assert a.indtaegtsgrundlag == pytest.approx(17_340)
    assert kilder["pensionstillaeg"] == pytest.approx(104_748)
    assert a.tillaegsprocent == 100
    assert kilder["aeldrecheck"] == pytest.approx(26_900)
    assert kilder["mediecheck"] == pytest.approx(1_552)
    assert a.personlig_indkomst == pytest.approx(17_340 + 90_528 + 104_748 + 26_900 + 1_552)


def test_us1_s7_atp_skoennet(res):
    assert "ATP_SKOENNET" in [x.kode for x in res.advarsler]
    assert "skoennet_atp" in res.aar_ved(70).flag


def test_tabel_slutter_ved_horisonten(res):
    assert res.aar[0].alder == 65
    assert res.aar[-1].alder == 90
