"""Feature 021 T004 — "Hvor skal næste krone hen?" i brugerfladen (US1, US2, SC)."""
import time

import pytest

from tests.browser.test_loen import til_resultat

pytestmark = pytest.mark.browser


def test_sammenligning_viser_alle_alternativer_hurtigt(side):
    til_resultat(side)
    start = time.perf_counter()
    side.click("#naeste-knap")
    side.wait_for_selector("#naeste-svar table")
    tid = time.perf_counter() - start
    print(f"naeste krone: {tid:.2f} s")
    assert tid < 3, f"{tid:.1f} s"                              # SC: under 3 s i browseren
    raekker = side.locator("#naeste-svar tbody tr")
    assert raekker.count() == 4
    tekst = side.inner_text("#naeste-svar")
    for titel in ("Ratepension", "Aldersopsparing", "Aktiesparekonto", "Opsparing i banken"):
        assert titel in tekst
    assert "afprøvet 4 måder" in tekst and "Afdrag på lån" in tekst
    assert side.fejl == []


def test_uden_loen_bedes_om_loennen(side):
    til_resultat(side, loen=None, stop=None)
    side.click("#naeste-knap")
    assert "Skriv din løn" in side.inner_text("#naeste-svar")


def test_axe_med_resultatet(side):
    til_resultat(side)
    side.click("#naeste-knap")
    side.wait_for_selector("#naeste-svar table")
    side.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = side.evaluate("async () => (await axe.run(document, {runOnly: "
                         "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
