"""T021/T031 — property-baserede invarianter (hypothesis)."""
from hypothesis import given, settings, strategies as st

from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.folkepension import pensionstillaeg
from pensionskerne.regler.skat import beregn_skat
from pensionskerne.regler.ydelser import tillaegsprocent

O = Regelopslag(2026, 2026, 0.0)
pi = st.floats(min_value=0, max_value=5_000_000, allow_nan=False)
kommune = st.floats(min_value=0.22, max_value=0.27)
kirke = st.floats(min_value=0.0, max_value=0.015)


@given(pi, kommune, kirke)
def test_skat_mellem_nul_og_indkomst(x, k, c):
    s = beregn_skat(x, k, c, O).total
    assert 0 <= s <= x


@given(pi, st.floats(min_value=1, max_value=200_000), kommune, kirke)
@settings(max_examples=300)
def test_skat_monoton_og_marginal_under_loft(x, delta, k, c):
    a = beregn_skat(x, k, c, O).total
    b = beregn_skat(x + delta, k, c, O).total
    assert b >= a - 1e-6
    assert (b - a) / delta <= 0.5707 + c + 1e-9


@given(st.floats(min_value=0, max_value=1_000_000), st.floats(min_value=0, max_value=100_000),
       st.sampled_from(["enlig", "gift_pensionist", "gift_ikke_pensionist"]))
def test_tillaeg_monotont_faldende(x, delta, regel):
    assert pensionstillaeg(x + delta, regel, O) <= pensionstillaeg(x, regel, O) + 1e-9


@given(st.floats(min_value=0, max_value=500_000), st.booleans())
def test_tillaegsprocent_heltal_0_100(x, gift):
    tp = tillaegsprocent(x, gift, O)
    assert isinstance(tp, int) and 0 <= tp <= 100
