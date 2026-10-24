"""T016 — golden cases for skat (domænegrundlag G-02, G-03; PSL §§ 6–10, 19)."""
import pytest

from pensionskerne.regler.skat import beregn_skat, progressiv_skat


def test_g02_ingen_mellemskat_paa_graensen(o2026):
    assert progressiv_skat(641_200, 0.25, o2026) == (0.0, 0.0)


def test_g02b_mellemskat_over_graensen(o2026):
    brutto, nedslag = progressiv_skat(741_200, 0.25, o2026)
    assert brutto == pytest.approx(7_500)
    assert nedslag == 0


def test_g03_mellem_og_topskat_uden_loft(o2026):
    brutto, nedslag = progressiv_skat(900_000, 0.25, o2026)
    assert brutto == pytest.approx(28_567.50)
    assert nedslag == 0  # 12,01 + 25 + 7,5 + 7,5 = 52,01 % < 52,07 %


def test_g03b_skatteloft_nedslag(o2026):
    # 0,1201 + 0,2571 + trin − loft = 0,0065 i alle bånd → 258.800 × 0,0065
    brutto, nedslag = progressiv_skat(900_000, 0.2571, o2026)
    assert nedslag == pytest.approx(258_800 * 0.0065)


def test_toptopskat_loft_5707(o2026):
    pi = 3_000_000
    brutto, nedslag = progressiv_skat(pi, 0.26, o2026)
    assert brutto == pytest.approx(136_700 * 0.075 + 1_814_800 * 0.15 + 407_300 * 0.20)
    assert nedslag == pytest.approx((pi - 641_200) * 0.0094)
    marginal = 0.1201 + 0.26 + 0.20 - 0.0094
    assert marginal == pytest.approx(0.5707)


def test_personfradrag_og_flad_skat(o2026):
    s = beregn_skat(100_000, 0.2452, 0.0, o2026)
    assert s.total == pytest.approx((100_000 - 54_100) * (0.1201 + 0.2452))


def test_personfradrag_kan_ikke_give_negativ_skat(o2026):
    assert beregn_skat(30_000, 0.25, 0.007, o2026).total == 0
