"""T028 — grænseværdier for de tre tillægsregler (lov om social pension § 29)."""
import pytest

from pensionskerne.regler.folkepension import pensionstillaeg

REGLER = [
    ("enlig", 104_748, 99_200, 0.309),
    ("gift_pensionist", 53_604, 198_800, 0.16),
    ("gift_ikke_pensionist", 53_604, 198_800, 0.32),
]


@pytest.mark.parametrize("regel,ydelse,fradrag,sats", REGLER)
def test_fuldt_tillaeg_til_og_med_fradraget(regel, ydelse, fradrag, sats, o2026):
    assert pensionstillaeg(fradrag, regel, o2026) == pytest.approx(ydelse)
    assert pensionstillaeg(fradrag + 1_000, regel, o2026) == pytest.approx(ydelse - 1_000 * sats)


@pytest.mark.parametrize("regel,ydelse,fradrag,sats,borger_dk", [
    (*REGLER[0], 438_200), (*REGLER[1], 533_800), (*REGLER[2], 366_400),
])
def test_bortfald_matcher_borger_dk(regel, ydelse, fradrag, sats, borger_dk, o2026):
    bortfald = fradrag + ydelse / sats
    assert abs(bortfald - borger_dk) < 100   # borger.dk afrunder
    assert pensionstillaeg(bortfald + 1, regel, o2026) == 0
    assert pensionstillaeg(bortfald - 100, regel, o2026) > 0
