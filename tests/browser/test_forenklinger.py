"""Feature 020 T006 — forenklingerne i "Sådan har vi regnet" (FR-005, FR-010)."""
import pytest

from pensionskerne import register

pytestmark = pytest.mark.browser


def test_forenklingerne_vises_med_begrundelse(resultat):
    resultat.click("#forenklinger-titel")
    punkter = resultat.locator("#forenklinger li")
    altid = [f for f in register.forenklinger() if f.omfang == "altid"]
    assert punkter.count() >= len(altid)
    tekst = resultat.inner_text("#forenklinger")
    assert all(f.titel in tekst for f in altid)
    assert "Hvorfor:" in tekst


def test_anvendt_forenkling_siges_i_tekst(resultat):
    v = resultat.evaluate("tilstand.v.forenklinger")
    anvendte = [f for f in v if f["anvendt"]]
    titel = resultat.inner_text("#forenklinger-titel")
    if anvendte:
        assert "påvirker din beregning" in titel
        resultat.click("#forenklinger-titel")
        assert "Påvirker din beregning" in resultat.inner_text("#forenklinger li >> nth=0")
    else:
        assert "påvirker" not in titel


def test_axe(resultat):
    resultat.click("#forenklinger-titel")
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
