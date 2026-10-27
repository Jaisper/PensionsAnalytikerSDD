"""Feature 013b T001 — aktieindkomst (PSL § 8 a) og aktiesparekonto."""
import pytest

from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.aktier import aktieindkomst_skat, ask_skat

O = Regelopslag(2026, 2026, 0.0)
GRAENSE = 79_400


def test_under_graensen_27_procent():
    assert aktieindkomst_skat(50_000, O) == pytest.approx(50_000 * 0.27)


def test_over_graensen_42_procent_af_det_overskydende():
    assert aktieindkomst_skat(100_000, O) == pytest.approx(GRAENSE * 0.27 + (100_000 - GRAENSE) * 0.42)


def test_gifte_faar_aegtefaellens_uudnyttede_graense():
    # Ægtefællen har 30.000 kr. aktieindkomst: 49.400 kr. af grænsen overføres (§ 8 a, stk. 4).
    ekstra = GRAENSE - 30_000
    assert aktieindkomst_skat(150_000, O, ekstra_graense=ekstra) == pytest.approx(
        (GRAENSE + ekstra) * 0.27 + (150_000 - GRAENSE - ekstra) * 0.42)


def test_overfoerslen_er_hoejst_en_graense():
    assert aktieindkomst_skat(300_000, O, ekstra_graense=10**6) == aktieindkomst_skat(300_000, O, ekstra_graense=GRAENSE)


def test_ingen_eller_negativ_aktieindkomst_giver_ingen_skat():
    assert aktieindkomst_skat(0, O) == 0 and aktieindkomst_skat(-5_000, O) == 0


def test_graensen_reguleres():
    o = Regelopslag(2026, 2028, 0.02)
    assert aktieindkomst_skat(100_000, o) == pytest.approx(
        GRAENSE * 1.02**2 * 0.27 + (100_000 - GRAENSE * 1.02**2) * 0.42)


def test_aktiesparekonto_17_procent_af_positivt_afkast():
    assert ask_skat(10_000, O) == pytest.approx(1_700)
    assert ask_skat(-10_000, O) == 0
