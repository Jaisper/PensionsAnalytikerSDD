"""Feature 023a T004 — "Dårlige år først" i tabellen "Hvad hvis …" (FR-003)."""
import json

import pytest

from pensionsoverblik import app
from pensionsoverblik.oversaet import til_kerne
from tests.app.test_husstand_app import IDAG
from tests.app.test_oversaet import GUIDE  # født 1963-05-01, ratepension fra 65


def test_afvigelsen_er_to_standardafvigelser_efter_pal():
    """50/50 globale aktier og stats- og realkreditobligationer: σ = ½·√(16,2² + 3,9²) ≈ 8,33 %."""
    assert app.stress_afvigelse() == pytest.approx(2 * 0.5 * (0.162 ** 2 + 0.039 ** 2) ** 0.5 * (1 - 0.153))


def test_forloebet_oversaettes():
    g = {**GUIDE, "antagelser": {**GUIDE["antagelser"], "afkast_forloeb": {"2030": -0.1}}}
    assert til_kerne(g)[1].afkast_forloeb == {2030: -0.1}
    assert til_kerne(GUIDE)[1].afkast_forloeb == {}


def test_scenarierne_har_daarlige_og_gode_aar_foerst():
    s = {x["noegle"]: x for x in app.scenarier(json.dumps(GUIDE))}
    assert s["daarlige_aar_foerst"]["stress"] == -1 and s["gode_aar_foerst"]["stress"] == 1
    assert s["daarlige_aar_foerst"]["afkast"] == GUIDE["antagelser"]["afkast_efter_pal"]


def test_daarlige_aar_foerst_rammer_de_to_foerste_aar_fra_startalderen():
    g = json.dumps(GUIDE)
    a = GUIDE["antagelser"]
    base = app.scenarie(g, IDAG, a["afkast_efter_pal"], a["inflation"])["data"]["dig"]
    daarlig = app.scenarie(g, IDAG, a["afkast_efter_pal"], a["inflation"], None, -1)["data"]
    god = app.scenarie(g, IDAG, a["afkast_efter_pal"], a["inflation"], None, 1)["data"]
    assert list(daarlig["forloeb"]) == ["2028", "2029"]          # født 1963, første udbetaling som 65
    assert daarlig["forloeb"]["2028"] == pytest.approx(a["afkast_efter_pal"] - app.stress_afvigelse(), abs=1e-6)
    # Gode år kan ikke hæve det første år (udjævningen låner aldrig, 010), kun senere år.
    assert daarlig["dig"] < base <= god["dig"]
