"""T045 — gift/samlevende (PT-1, R1, A4)."""
from datetime import date

import pytest

from pensionskerne import Partner, PartnerIndkomst, beregn
from pensionskerne.regler.folkepension import pensionstillaeg
from tests.conftest import BEREGNINGSDATO, enlig_profil


def test_pt1_begge_pensionister_giver_hoejere_tillaeg(o2026):
    assert pensionstillaeg(300_000, "gift_pensionist", o2026) > \
        pensionstillaeg(300_000, "gift_ikke_pensionist", o2026)


def _profil(partner_indkomst):
    # Person født 1958 (fp 67, pensionist i hele tabellen). Partner født 1975 (fp 70 → 2045).
    partner = Partner(date(1975, 3, 1), {aar: partner_indkomst for aar in range(2026, 2050)})
    return enlig_profil(foedselsdato=date(1958, 2, 1), civilstand="gift_samlevende",
                        ordninger=(), atp_aarlig=20_000, partner=partner)


def test_skift_fra_32_til_16_procent(nul_antagelser):
    res = beregn(_profil(PartnerIndkomst(oevrig_indkomst=400_000)), nul_antagelser, 2026, BEREGNINGSDATO)
    foer = res.aar_ved(2044 - 1958)   # partner 69
    efter = res.aar_ved(2045 - 1958)  # partner 70
    tillaeg = lambda a: next((k.brutto for k in a.kilder if k.type == "pensionstillaeg"), 0.0)
    assert foer.indtaegtsgrundlag == pytest.approx(20_000 + 0.46 * 400_000)
    # 2044/2045: den midlertidige forhøjelse (§ 49 c) er udløbet → fradrag 179.100 kr. (A12)
    assert tillaeg(foer) == pytest.approx(max(0, 53_604 - 0.32 * (204_000 - 179_100)))
    assert efter.indtaegtsgrundlag == pytest.approx(420_000)
    assert tillaeg(efter) == pytest.approx(max(0, 53_604 - 0.16 * (420_000 - 179_100)))


def test_arbejdsindkomst_ignoreres(nul_antagelser):
    a = beregn(_profil(PartnerIndkomst(am_pligtig_arbejdsindkomst=900_000)), nul_antagelser, 2026,
               BEREGNINGSDATO).aar_ved(70)
    assert a.indtaegtsgrundlag == pytest.approx(20_000)


def test_manglende_aar_bruger_naermeste_og_markeres(nul_antagelser):
    partner = Partner(date(1975, 3, 1), {2026: PartnerIndkomst(oevrig_indkomst=50_000)})
    profil = enlig_profil(foedselsdato=date(1958, 2, 1), civilstand="gift_samlevende",
                          ordninger=(), atp_aarlig=0, partner=partner)
    a = beregn(profil, nul_antagelser, 2026, BEREGNINGSDATO).aar_ved(80)
    assert a.indtaegtsgrundlag == pytest.approx(0.46 * 50_000)
    assert "forenkling:partnerindkomst_naermeste_aar" in a.flag


def test_g41_gift_tillaegsprocent_bruger_samlet_grundlag(nul_antagelser):
    a = beregn(_profil(PartnerIndkomst(oevrig_indkomst=200_000)), nul_antagelser, 2026,
               BEREGNINGSDATO).aar_ved(70)
    # 2028: bund = 50.900 + 19.700 × 6/8 = 65.675 (§ 49 c aftrappes)
    # grundlag 20.000 + 46 % × 200.000 = 112.000 → (112.000 − 65.675) // 1.282 = 36 trin
    assert a.tillaegsprocent == 64
