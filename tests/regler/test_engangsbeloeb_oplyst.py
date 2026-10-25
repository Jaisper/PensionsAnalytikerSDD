"""Feature 008 T001 — kernen oplyser hvert engangsbeløb (FR-001). Ingen ny beregning."""
from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, beregn
from pensionskerne.model import Engangsbeloeb
from tests.conftest import BEREGNINGSDATO, enlig_profil


def test_engangsbeloeb_pr_ordning():
    ald = Ordning("ald", "aldersopsparing", 300_000, 66, oprettet=date(2015, 1, 1))
    kap = Ordning("kap", "kapitalpension", 400_000, 67, oprettet=date(2000, 1, 1), i_buffer=False)
    rate = Ordning("rate", "ratepension", 800_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    res = beregn(enlig_profil(ordninger=(rate, ald, kap)), Antagelser(), 2026, BEREGNINGSDATO)
    assert all(isinstance(e, Engangsbeloeb) for e in res.engangsbeloeb)
    assert [(e.ordning_id, e.type, e.alder, e.i_buffer) for e in res.engangsbeloeb] == [
        ("ald", "aldersopsparing", 66, True), ("kap", "kapitalpension", 67, False)]
    pr_aar = {a.alder: a.engangsbeloeb_netto for a in res.aar}
    for e in res.engangsbeloeb:
        assert e.netto == pytest.approx(pr_aar[e.alder])
        assert e.netto > 0


def test_ingen_engangsbeloeb():
    res = beregn(enlig_profil(), Antagelser(), 2026, BEREGNINGSDATO)
    assert res.engangsbeloeb == ()
