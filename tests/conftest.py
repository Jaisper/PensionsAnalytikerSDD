from datetime import date

import pytest

from pensionskerne import Antagelser, Ordning, Pensionsprofil
from pensionskerne.register.opslag import Regelopslag

BEREGNINGSDATO = date(2026, 10, 24)


@pytest.fixture
def o2026() -> Regelopslag:
    """Regelopslag for satsår 2026 uden satsregulering (golden cases bruger 2026-tal)."""
    return Regelopslag(2026, 2026, 0.0)


@pytest.fixture
def nul_antagelser() -> Antagelser:
    return Antagelser(afkast_efter_pal=0.0, inflation=0.0)


def enlig_profil(**kw) -> Pensionsprofil:
    standard = dict(
        foedselsdato=date(1963, 5, 1), civilstand="enlig", kommune="aarhus",
        likvid_formue=50_000,
        ordninger=(Ordning("rate1", "ratepension", 1_000_000, 65, oprettet=date(2010, 1, 1),
                           udbetaling_aar=10),),
    )
    standard.update(kw)
    return Pensionsprofil(**standard)
