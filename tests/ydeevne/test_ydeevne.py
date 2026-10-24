"""T050 — SC-005: 40 år og 10 ordninger på under 100 ms."""
import time
from datetime import date

from pensionskerne import Antagelser, Ordning, beregn
from tests.conftest import BEREGNINGSDATO, enlig_profil


def test_under_100_ms():
    typer = ["ratepension", "livsvarig", "aldersopsparing", "kapitalpension"]
    ordninger = tuple(
        Ordning(f"o{i}", typer[i % 4], 200_000 + i * 50_000, 67 + i % 5, oprettet=date(2019, 1, 1),
                aarlig_indbetaling=5_000, udbetaling_aar=10 if typer[i % 4] == "ratepension" else None)
        for i in range(10)
    )
    profil = enlig_profil(foedselsdato=date(1980, 1, 1), ordninger=ordninger)
    a = Antagelser(livsvarig_horisont_alder=95)
    beregn(profil, a, 2026, BEREGNINGSDATO)  # opvarmning (registercache)
    start = time.perf_counter()
    for _ in range(20):
        res = beregn(profil, a, 2026, BEREGNINGSDATO)
    gennemsnit = (time.perf_counter() - start) / 20
    assert len(res.aar) >= 25
    assert gennemsnit < 0.1, f"{gennemsnit * 1000:.1f} ms"
