"""T043 — opsat folkepension (VT-1, R6)."""
from datetime import date

import pytest

from pensionskerne import Antagelser, beregn
from pensionskerne.regler.opsat import ventefaktor
from tests.conftest import BEREGNINGSDATO, enlig_profil

TABEL = [0.0571, 0.1194, 0.1875, 0.2623, 0.3448, 0.4337, 0.5350, 0.6443, 0.7660, 0.9023]


@pytest.mark.parametrize("aar", range(1, 11))
def test_reproducerer_aeldre_sagens_tabel_fra_67(aar, o2026):
    # Middellevetidstabellen (VEJ 10077, tabel 16) skal give præcis de publicerede procenter.
    assert ventefaktor(67, aar, o2026) == pytest.approx(1 + TABEL[aar - 1], abs=1e-9)


@pytest.mark.parametrize("fp,aar,middellevetid", [(68, 2, 192), (69, 5, 157), (70, 10, 110)])
def test_andre_folkepensionsaldre_bruger_officiel_tabel(fp, aar, middellevetid, o2026):
    assert ventefaktor(fp, aar, o2026) == pytest.approx(1 + round(aar * 12 / middellevetid, 4))
    assert not [f for f in o2026.flag if f.startswith("uverificeret")]


def test_vt1_tre_aar_fra_67():
    profil = enlig_profil(foedselsdato=date(1960, 1, 15), ordninger=(), atp_aarlig=12_000)
    res = beregn(profil, Antagelser(afkast_efter_pal=0, inflation=0, folkepension_opsaettelse_aar=3),
                 2026, BEREGNINGSDATO)
    assert res.folkepensionsalder == 67
    k = {a.alder: {x.type: x.brutto for x in a.kilder} for a in res.aar}
    assert "grundbeloeb" not in k[69] and k[68]["atp"] == pytest.approx(12_000)  # ATP fra 67
    assert k[71]["grundbeloeb"] == pytest.approx(90_528 * 1.1875)
    assert k[71]["pensionstillaeg"] == pytest.approx(104_748 * 1.1875)
    koder = [x.kode for x in res.advarsler]
    assert "750_TIMER" in koder and "OPSAT_ANDRE_FORMER" in koder
