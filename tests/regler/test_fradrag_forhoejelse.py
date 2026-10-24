"""A12 — den midlertidige forhøjelse af fradragene (§ 49 c) aftrappes til 0 i 2034."""
import pytest

from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.folkepension import fradrag_forhoejelse, pensionstillaeg
from pensionskerne.regler.ydelser import tillaegsprocent


@pytest.mark.parametrize("aar,enlig,gift", [
    (2026, 9_800, 19_700), (2030, 4_900, 9_850), (2033, 1_225, 2_462.5), (2034, 0, 0), (2040, 0, 0),
])
def test_lineaer_aftrapning_uden_satsregulering(aar, enlig, gift):
    o = Regelopslag(2026, aar, 0.0)
    assert fradrag_forhoejelse(False, o) == pytest.approx(enlig)
    assert fradrag_forhoejelse(True, o) == pytest.approx(gift)


def test_2026_giver_de_publicerede_graenser(o2026):
    # 89.400 + 9.800 = 99.200 og 25.900 + 9.800 = 35.700 (borger.dk)
    assert pensionstillaeg(99_200, "enlig", o2026) == pytest.approx(104_748)
    assert pensionstillaeg(99_300, "enlig", o2026) < 104_748
    assert tillaegsprocent(35_700, False, o2026) == 100
    assert tillaegsprocent(36_335, False, o2026) == 99


def test_efter_2034_falder_fradraget_til_grundbeloebet():
    o = Regelopslag(2026, 2035, 0.0)
    assert pensionstillaeg(89_400, "enlig", o) == pytest.approx(104_748)
    assert pensionstillaeg(99_200, "enlig", o) == pytest.approx(104_748 - 0.309 * 9_800)
    assert tillaegsprocent(25_900, False, o) == 100
    assert tillaegsprocent(26_535, False, o) == 99
