"""T006 — Regelopslag: sporing, streng tilstand og satsregulering (FR-012, FR-060)."""
import pytest

from pensionskerne import UverificeretRegel
from pensionskerne.register.opslag import Regelopslag


def test_opslag_registreres_i_sporing():
    o = Regelopslag(2026, 2026, 0.0)
    o.v("skat.bundskat")
    o.v("skat.bundskat")
    assert o.brugt == ["skat.bundskat"]


def test_ikke_verificeret_post_markeres():
    o = Regelopslag(2026, 2026, 0.0)
    o.v("ordning.udbetalingsalder.foer_2007")
    assert "sekundaer:ordning.udbetalingsalder.foer_2007" in o.flag


def test_streng_tilstand_afviser_ikke_verificeret():
    o = Regelopslag(2026, 2026, 0.0, streng=True)
    assert o.v("skat.bundskat") == 0.1201
    with pytest.raises(UverificeretRegel) as e:
        o.v("ordning.udbetalingsalder.foer_2007")
    assert e.value.id == "ordning.udbetalingsalder.foer_2007"
    assert e.value.kilde


def test_satsregulering_kun_af_beloeb():
    o = Regelopslag(2026, 2028, 0.03)
    assert o.v("skat.personfradrag") == pytest.approx(54_100 * 1.03 ** 2)
    assert o.v("skat.bundskat") == 0.1201


def test_ingen_regulering_i_satsaaret():
    assert Regelopslag(2026, 2026, 0.05).v("skat.personfradrag") == 54_100
