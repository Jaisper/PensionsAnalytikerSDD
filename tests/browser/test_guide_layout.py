"""UX: felterne i en ordning står på linje, også når en label går over to linjer."""
import pytest

from tests.app.pensionsinfo_syntetisk import RAPPORT_PDF

pytestmark = pytest.mark.browser


@pytest.mark.parametrize("bredde", [1366, 900])
def test_ordningens_felter_staar_paa_linje(side, tmp_path, bredde):
    side.set_viewport_size({"width": bredde, "height": 900})
    pdf = tmp_path / "rapport.pdf"
    pdf.write_bytes(RAPPORT_PDF)
    side.set_input_files("#pdf-fil", str(pdf))
    side.wait_for_selector("#pdf-status p")
    side.fill("#kommune", "Aarhus")
    side.click("#naeste")
    side.wait_for_selector("#ordninger .ordning")
    raekker = side.evaluate("""() => [...document.querySelectorAll('#ordninger .ordning__felter')].map((g) => {
        const felter = [...g.children].filter((f) => f.querySelector(':scope > input, :scope > select'));
        const top = felter.map((f) => [f.getBoundingClientRect().top, f.querySelector(':scope > input, :scope > select').getBoundingClientRect().top]);
        const raekke = {};
        for (const [ft, it] of top) (raekke[Math.round(ft)] ??= []).push(Math.round(it));
        return Object.values(raekke);
    })""")
    for gitter in raekker:
        for raekke in gitter:
            assert max(raekke) - min(raekke) <= 1, raekke
    side.screenshot(path=str(tmp_path / f"guide_{bredde}.png"), full_page=True)
