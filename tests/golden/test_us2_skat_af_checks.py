"""T030 — ældrecheck og mediecheck er skattepligtige og indgår i PI (A3, research T8)."""
import pytest

from pensionskerne import beregn
from tests.conftest import BEREGNINGSDATO, enlig_profil


def test_checks_beskattes(nul_antagelser):
    res = beregn(enlig_profil(ordninger=(), atp_aarlig=0), nul_antagelser, 2026, BEREGNINGSDATO)
    a = res.aar_ved(70)
    kilder = {k.type: k for k in a.kilder}
    assert kilder["mediecheck"].skat > 0
    assert kilder["aeldrecheck"].skat > 0
    pi = 90_528 + 104_748 + 26_900 + 1_552
    assert a.personlig_indkomst == pytest.approx(pi)
    assert a.skat_i_alt == pytest.approx((pi - 54_100) * (0.1201 + 0.2452))
