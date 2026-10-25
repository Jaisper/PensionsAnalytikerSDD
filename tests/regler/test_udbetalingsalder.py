"""T019 — tidligste udbetalingsalder efter oprettelsesdato (R2, A2)."""
from datetime import date

import pytest

from pensionskerne.regler.udbetalingsalder import tidligste_udbetalingsalder as t


@pytest.mark.parametrize("foedt,oprettet,fp,forventet", [
    (date(1963, 5, 1), date(2018, 1, 1), 68, 65.0),
    (date(1963, 5, 1), date(2017, 12, 31), 68, 63.0),
    (date(1963, 5, 1), date(2007, 5, 1), 68, 63.0),
    # Aftaler før 1.5.2007: 60 år — bekræftet af en rigtig PensionsInfo-rapport (født 1971, "kan
    # tidligst udbetales fra 60 år") og Ældre Sagen. Den tidligere overgangstabel efter
    # fødselsdato var forkert anvendt på denne aftalekategori.
    (date(1958, 12, 31), date(2000, 1, 1), 67, 60.0),
    (date(1963, 5, 1), date(2000, 1, 1), 68, 60.0),
    (date(1971, 7, 8), date(2005, 1, 1), 70, 60.0),
])
def test_regler(foedt, oprettet, fp, forventet, o2026):
    assert t(foedt, oprettet, fp, o2026) == (forventet, False)


def test_ukendt_oprettelse_bruger_mest_restriktive(o2026):
    assert t(date(1963, 5, 1), None, 68, o2026) == (65.0, True)  # max(fp−3, fp−5, 60)


def test_selskabets_oplyste_alder_overstyrer_reglen():
    """Pensionsselskabet oplyser den tidligste alder pr. aftale (PensionsInfo). Den er autoritativ."""
    from datetime import date as d
    from pensionskerne import Antagelser, Ordning, beregn
    from tests.conftest import BEREGNINGSDATO, enlig_profil
    # Født 1963 (fp 68, 63 år i 2026), oprettet 2020 → reglen siger 65, men selskabet oplyser 60.
    o = Ordning("x", "kapitalpension", 100_000, 64, oprettet=d(2020, 1, 1), tidligste_udbetalingsalder=60)
    res = beregn(enlig_profil(ordninger=(o,)), Antagelser(), 2026, BEREGNINGSDATO)
    assert res.aar_ved(64).engangsbeloeb_netto > 0
    assert "UDBETALING_FOER_LOVLIG_ALDER" not in [a.kode for a in res.advarsler]


def test_oplyst_alder_haandhaeves_ogsaa():
    from datetime import date as d
    import pytest as pt
    from pensionskerne import Antagelser, Ordning, UgyldigtInput, beregn
    from tests.conftest import BEREGNINGSDATO, enlig_profil
    o = Ordning("x", "kapitalpension", 100_000, 59, oprettet=None, tidligste_udbetalingsalder=60)
    with pt.raises(UgyldigtInput) as e:
        beregn(enlig_profil(ordninger=(o,)), Antagelser(), 2026, BEREGNINGSDATO)
    assert e.value.felt == "ordninger[x].udbetaling_start_alder"
