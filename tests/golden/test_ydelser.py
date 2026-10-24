"""T027 — golden G-40..G-43 og minimumsreglen (A6)."""
import pytest

from pensionskerne.regler.folkepension import pensionstillaeg
from pensionskerne.regler.ydelser import aeldrecheck, mediecheck, tillaegsprocent


@pytest.mark.parametrize("ig,tp", [(0, 100), (35_700, 100), (36_335, 99), (36_334, 100),
                                   (99_200, 0), (200_000, 0)])
def test_g40_enlig(ig, tp, o2026):
    assert tillaegsprocent(ig, False, o2026) == tp


@pytest.mark.parametrize("ig,tp", [(70_600, 100), (71_882, 99), (198_800, 0)])
def test_g41_gift(ig, tp, o2026):
    assert tillaegsprocent(ig, True, o2026) == tp


def test_g42_tillaegsprocent_er_ikke_tillaeggets_aftrapning(o2026):
    assert tillaegsprocent(99_200, False, o2026) == 0
    assert pensionstillaeg(99_200, "enlig", o2026) == pytest.approx(104_748)
    assert aeldrecheck(0, 0, o2026) == 0


def test_g43_formuegraense_haard_kun_for_aeldrecheck(o2026):
    assert aeldrecheck(100, 108_000, o2026) == pytest.approx(26_900)
    assert aeldrecheck(100, 108_001, o2026) == 0
    assert mediecheck(100, o2026) == pytest.approx(1_552)


def test_aeldrecheck_skaleres_med_tillaegsprocent(o2026):
    assert aeldrecheck(50, 0, o2026) == pytest.approx(13_450)


def test_a6_minimum_kan_ikke_bide_med_2026_satser(o2026):
    # Laveste tillægsprocent (1) giver 269 kr. ≥ 200 kr. Reglen er implementeret, men har
    # ingen effekt med 2026-satserne, fordi tillægsprocenten er et heltal.
    assert aeldrecheck(1, 0, o2026) == pytest.approx(269)


def test_a6_minimum_regel(monkeypatch, o2026):
    oprindelig = o2026.v
    monkeypatch.setattr(o2026, "v", lambda id: 10_000 if id == "yd.aeldrecheck" else oprindelig(id))
    assert aeldrecheck(1, 0, o2026) == 0      # 100 kr. < 200 kr.
    assert aeldrecheck(2, 0, o2026) == pytest.approx(200)


def test_mediecheck_kraever_100(o2026):
    assert mediecheck(99, o2026) == 0
