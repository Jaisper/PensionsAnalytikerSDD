"""T019 — tidligste udbetalingsalder efter oprettelsesdato (R2, A2)."""
from datetime import date

import pytest

from pensionskerne.regler.udbetalingsalder import tidligste_udbetalingsalder as t


@pytest.mark.parametrize("foedt,oprettet,fp,forventet", [
    (date(1963, 5, 1), date(2018, 1, 1), 68, 65.0),
    (date(1963, 5, 1), date(2017, 12, 31), 68, 63.0),
    (date(1963, 5, 1), date(2007, 5, 1), 68, 63.0),
    (date(1958, 12, 31), date(2000, 1, 1), 67, 60.0),
    (date(1959, 6, 30), date(2000, 1, 1), 67, 60.5),
    (date(1959, 7, 1), date(2000, 1, 1), 67, 61.0),
    (date(1960, 3, 1), date(2000, 1, 1), 67, 61.5),
    (date(1963, 5, 1), date(2000, 1, 1), 68, 65.0),
])
def test_regler(foedt, oprettet, fp, forventet, o2026):
    assert t(foedt, oprettet, fp, o2026) == (forventet, False)


def test_ukendt_oprettelse_bruger_mest_restriktive(o2026):
    assert t(date(1963, 5, 1), None, 68, o2026) == (65.0, True)
