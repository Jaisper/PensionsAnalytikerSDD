"""T029 — indtægtsgrundlag (A4, A5; borger.dk; § 32 a)."""
import pytest

from pensionskerne import PartnerIndkomst
from pensionskerne.regler.folkepension import indtaegtsgrundlag


def test_egne_kilder(o2026):
    assert indtaegtsgrundlag(100_000, 17_340, 5_000, None, False, o2026) == pytest.approx(122_340)


def test_partner_pensionist_fuldt_arbejdsindkomst_aldrig(o2026):
    p = PartnerIndkomst(am_pligtig_arbejdsindkomst=300_000, oevrig_indkomst=100_000)
    assert indtaegtsgrundlag(0, 0, 0, p, True, o2026) == pytest.approx(100_000)


def test_partner_ikke_pensionist_46_procent(o2026):
    p = PartnerIndkomst(am_pligtig_arbejdsindkomst=300_000, oevrig_indkomst=100_000)
    assert indtaegtsgrundlag(0, 0, 0, p, False, o2026) == pytest.approx(46_000)
