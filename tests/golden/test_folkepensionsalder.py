"""T017 — FP-1: folkepensionsalder (lov om social pension § 1 a; L 149)."""
from datetime import date

import pytest

from pensionskerne.regler.folkepension import folkepensionsalder


@pytest.mark.parametrize("foedt,alder", [
    (date(1955, 7, 1), 67), (date(1962, 12, 31), 67), (date(1963, 1, 1), 68),
    (date(1966, 12, 31), 68), (date(1967, 6, 1), 69), (date(1970, 12, 31), 69),
    (date(1971, 1, 1), 70), (date(1990, 1, 1), 70),
])
def test_fp1(foedt, alder, o2026):
    assert folkepensionsalder(foedt, o2026) == alder
