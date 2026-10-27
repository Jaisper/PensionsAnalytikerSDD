"""Feature 017 T001 — skat af løn: ligningsmæssige fradrag og personfradrag pr. skattegrundlag.

- Beskæftigelsesfradrag (LL § 9 J, stk. 1): 12,75 %, højst 63.300 kr. (2026).
- Jobfradrag (LL § 9 K): 4,5 % af grundlaget over 235.200 kr., højst 3.100 kr. (2026).
- Seniorfradrag (LL § 9 J, stk. 5–6): 1,4 %, højst 6.100 kr. (2026), de to sidste indkomstår før
  folkepensionsalderen.
- Ligningsmæssige fradrag nedsætter den skattepligtige indkomst, som er grundlaget for kommune- og
  kirkeskat, men ikke bundskat, mellem- eller topskat (PSL §§ 6–7).
"""
import pytest

from pensionskerne.regler.loen import beskaeftigelsesfradrag, jobfradrag, seniorfradrag
from pensionskerne.regler.skat import beregn_skat


@pytest.mark.parametrize("grundlag, forventet", [(0, 0), (400_000, 51_000), (496_471, 63_300), (600_000, 63_300)])
def test_beskaeftigelsesfradrag(o2026, grundlag, forventet):
    assert beskaeftigelsesfradrag(grundlag, o2026) == pytest.approx(forventet, abs=1)


@pytest.mark.parametrize("grundlag, forventet", [(200_000, 0), (235_200, 0), (250_000, 666), (400_000, 3_100)])
def test_jobfradrag(o2026, grundlag, forventet):
    assert jobfradrag(grundlag, o2026) == pytest.approx(forventet, abs=1e-6)


@pytest.mark.parametrize("alder, forventet", [(64, 0), (65, 5_600), (66, 5_600), (67, 0)])
def test_seniorfradrag_de_to_sidste_aar_foer_folkepensionsalderen(o2026, alder, forventet):
    assert seniorfradrag(400_000, alder, 67, o2026) == pytest.approx(forventet)


def test_seniorfradrag_har_et_loft(o2026):
    assert seniorfradrag(1_000_000, 66, 67, o2026) == pytest.approx(6_100)


def test_ligningsmaessige_fradrag_nedsaetter_kun_kommune_og_kirkeskat(o2026):
    kommune, kirke = 0.2452, 0.0074
    uden = beregn_skat(400_000, kommune, kirke, o2026)
    med = beregn_skat(400_000, kommune, kirke, o2026, ligningsmaessige_fradrag=50_000)
    assert uden.total - med.total == pytest.approx(50_000 * (kommune + kirke))


def test_personfradrag_regnes_pr_skattegrundlag(o2026):
    # PI 60.000, fradrag 20.000: bundskattens grundlag 60.000, kommuneskattens 40.000. Personfradraget
    # (54.100 kr.) bruges fuldt i bundskatten og kun med 40.000 i kommuneskatten.
    kommune, kirke = 0.2452, 0.0
    s = beregn_skat(60_000, kommune, kirke, o2026, ligningsmaessige_fradrag=20_000)
    pf = o2026.v("skat.personfradrag")
    assert s.total == pytest.approx((60_000 - pf) * o2026.v("skat.bundskat"))
    assert s.uudnyttet_personfradrag == pytest.approx((pf - 40_000) * kommune)
