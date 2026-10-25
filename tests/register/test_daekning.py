"""T037 — SC-002: mindst 90 % af 2026-posterne er verificeret mod niveau 1–3-kilder."""
from pensionskerne import register


def test_mindst_90_procent_verificeret():
    poster = register.poster(2026)
    andel = sum(p.status == "verificeret" for p in poster) / len(poster)
    ikke = [p.id for p in poster if p.status != "verificeret"]
    assert andel >= 0.9, f"{andel:.0%} verificeret — mangler: {ikke}"
