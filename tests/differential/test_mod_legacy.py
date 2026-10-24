"""T049 — differentialtest mod legacy/engine.py (research T7).

Lag 1: regelfunktioner, hvor reglen er uændret, skal give samme tal (±0,01).
Lag 2: år med kun ratepension og afkast 0, hvor den eneste kendte forskel er A1
(legacy trækker 8 % AM-bidrag af udbetalingen). Legacy-netto skal derfor svare til
den nye skatteberegning anvendt på 92 % af bruttoudbetalingen.
"""
import sys
from datetime import date
from pathlib import Path

import pytest

LEGACY = Path(__file__).resolve().parents[2] / "legacy"
if not (LEGACY / "engine.py").exists():
    pytest.skip("legacy/ findes ikke", allow_module_level=True)
sys.path.insert(0, str(LEGACY))
import engine as legacy  # noqa: E402

from pensionskerne import Antagelser, Ordning, beregn  # noqa: E402
from pensionskerne.register.opslag import Regelopslag  # noqa: E402
from pensionskerne.regler.folkepension import folkepensionsalder, pensionstillaeg  # noqa: E402
from pensionskerne.regler.skat import beregn_skat, progressiv_skat  # noqa: E402
from pensionskerne.regler.ydelser import tillaegsprocent  # noqa: E402
from tests.conftest import BEREGNINGSDATO, enlig_profil  # noqa: E402

O = Regelopslag(2026, 2026, 0.0)


# ── Lag 1 ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("pi", [0, 300_000, 641_200, 700_000, 777_900, 900_000, 1_500_000, 3_000_000])
@pytest.mark.parametrize("kommune", [0.2339, 0.25, 0.2571, 0.263])
def test_progressiv_skat_som_legacy(pi, kommune):
    brutto, nedslag = progressiv_skat(pi, kommune, O)
    assert brutto - nedslag == pytest.approx(legacy._progressiv_skat_total_aar(pi, kommune), abs=0.01)


@pytest.mark.parametrize("ig", [0, 99_200, 150_000, 250_000, 400_000, 600_000])
def test_pensionstillaeg_som_legacy(ig):
    enlig = legacy.SkatParametre.fra_pct(25, 0.7, enlig=True)
    gift = legacy.SkatParametre.fra_pct(25, 0.7, enlig=False)
    assert pensionstillaeg(ig, "enlig", O) == pytest.approx(legacy.folkepension_pensionstillaeg_aar(ig, enlig))
    assert pensionstillaeg(ig, "gift_pensionist", O) == pytest.approx(
        legacy.folkepension_pensionstillaeg_aar(ig, gift, partner_er_fp=True))
    assert pensionstillaeg(ig, "gift_ikke_pensionist", O) == pytest.approx(
        legacy.folkepension_pensionstillaeg_aar(ig, gift, partner_er_fp=False))


@pytest.mark.parametrize("ig", range(0, 220_000, 1_037))
def test_tillaegsprocent_som_legacy(ig):
    assert tillaegsprocent(ig, False, O) == legacy.beregn_tillaegsprocent(ig, True)
    assert tillaegsprocent(ig, True, O) == legacy.beregn_tillaegsprocent(ig, False)


@pytest.mark.parametrize("aar", range(1955, 1990))
def test_folkepensionsalder_som_legacy(aar):
    # 1. juli: legacy kender ikke § 1 a's 66½ år for født 1.1.–30.6.1955 (A10)
    assert folkepensionsalder(date(aar, 7, 1), O) == legacy.folkepension_alder(aar)


# ── Lag 2 ────────────────────────────────────────────────────────────────────

def test_ratepension_foer_folkepension_forskel_er_kun_am_bidrag():
    """A1: legacy-netto = ny skatteberegning på 92 % af brutto. Ingen andre forskelle."""
    profil_legacy = {
        "person": {"alder": 63, "foedselsdato": "01.05.1963"},
        "pensionsprodukter": [{"selskab": "X", "produkttype": "ratepension",
                               "opsparing": 1_000_000, "skat_type": "S",
                               "aldersperioder": {"65-74 år": 1}}],
    }
    param = {"pensionsalder": 65, "udbetaling_aar": 10, "afkast_pct": 0.0,
             "kommuneskat_pct": 24.52, "kirkeskat_pct": 0.0, "inflation_pct": 0.0}
    gammel = {r["alder"]: r for r in legacy.generer_udbetalingstabel(profil_legacy, param)["tabel"]}
    ny = beregn(enlig_profil(), Antagelser(afkast_efter_pal=0, inflation=0), 2026, BEREGNINGSDATO)
    for alder in (65, 66, 67):
        brutto = ny.aar_ved(alder).personlig_indkomst
        assert brutto == pytest.approx(100_000)
        legacy_netto = gammel[alder]["total_netto_aar"]
        forventet = 0.92 * brutto - beregn_skat(0.92 * brutto, 0.2452, 0.0, O).total
        assert legacy_netto == pytest.approx(forventet, abs=1)
        assert ny.aar_ved(alder).netto_i_alt - legacy_netto > 0  # A1 giver højere netto
