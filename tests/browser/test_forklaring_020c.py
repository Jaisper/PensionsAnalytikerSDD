"""Feature 020c — forklaringen af "Find bedste plan" på tre niveauer med søgningens omfang og
forbeholdet "information, ikke rådgivning" (US5, Princip V)."""
import pytest

pytestmark = pytest.mark.browser

FUNDET = "{forbedret: false, udtoemmende: false, evalueret: 1234, mulige: 98765}"


def test_forklaringen_af_forslaget(resultat):
    resultat.wait_for_function("() => !!tilstand.forklaringer")
    resultat.evaluate(f"visForslag({FUNDET}, svarNoegle()); document.querySelector('#forslag').hidden = false")
    boks = resultat.locator("#forslag [data-optimering]")
    boks.locator("summary").click()
    niveau1 = boks.inner_text()
    assert "rådgiver" in niveau1                        # forbeholdet på alle niveauer
    resultat.evaluate("saetNiveau('niveau3')")
    tekst = boks.inner_text()
    assert "1.234" in tekst and "98.765" in tekst and "ikke alle" in tekst
    assert "deterministisk" in tekst
