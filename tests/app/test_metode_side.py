"""Feature 039 — metodebeskrivelsen som side i løsningen: samme kilde (docs/metode.md), uden det tekniske."""
import importlib.util
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROD = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("metode_html", ROD / "scripts" / "metode_html.py")
metode_html = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(metode_html)

MD = (ROD / "docs" / "metode.md").read_text(encoding="utf-8")


class _Tekst(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tekst, self.pre, self.ids, self.ankre = [], [], set(), []
        self._i_pre = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and a.get("href", "").startswith("#"):
            self.ankre.append(a["href"][1:])
        self._i_pre = self._i_pre or tag == "pre"

    def handle_endtag(self, tag):
        if tag == "pre":
            self._i_pre = False

    def handle_data(self, data):
        (self.pre if self._i_pre else self.tekst).append(data)


def laes(html: str) -> _Tekst:
    p = _Tekst()
    p.feed(html)
    return p


@pytest.fixture(scope="module")
def side():
    return laes(metode_html.side(MD))


def test_teknisk_udelades_ogsaa_midt_i_en_linje():
    md = "Før <!-- teknisk -->(`fremskrivning.py:223`)<!-- /teknisk --> efter.\n\n<!-- teknisk -->\n## Kode\n\nx\n<!-- /teknisk -->\n"
    html, overskrifter = metode_html.til_html(md)
    assert "fremskrivning" not in html and "Kode" not in html and overskrifter == []
    assert "Før  efter." in html


def test_links_til_filer_bliver_tekst_og_links_til_nettet_beholdes():
    html, _ = metode_html.til_html("Se [lovgivningen](https://www.retsinformation.dk/x) og [koden](../src/a.py).")
    assert '<a href="https://www.retsinformation.dk/x" rel="noopener">lovgivningen</a>' in html
    assert "../src" not in html and "koden" in html


def test_tabeller_lister_og_overskrifter():
    html, overskrifter = metode_html.til_html(
        "## 1. Overblik\n\n| A | B |\n|---|---|\n| **x** | y |\n\n- et\n  fortsat\n- to\n\n1. første\n2. anden\n")
    assert overskrifter == [(2, "1. Overblik", "1-overblik")]
    assert "<th scope=\"col\">A</th>" in html and "<td><strong>x</strong></td>" in html
    assert "<ul><li>et fortsat</li><li>to</li></ul>" in html and "<ol><li>første</li><li>anden</li></ol>" in html


# Kodenavne, der ikke må stå i siden: filer, stier, funktioner, snake_case og camelCase.
TEKNISKE_MOENSTRE = {
    "backtick": r"`",
    "fil": r"\b[\w-]+\.(?:py|toml|js|md|yml|json|pdf)\b",
    "sti": r"\b(?:src|tests|scripts|docs|specs|legacy)/",
    "snake_case": r"\b[a-z]{2,}_[a-z0-9_]{2,}\b",
    "KODE_NAVN": r"\b[A-Z0-9]{2,}_[A-Z0-9_]{2,}\b",
    "registerpost": r"\b[a-z]+\.[a-z_]+\.[a-z_]+\b",
    "camelCase": r"\b[a-z]+[A-Z][A-Za-z]*\b",
    "funktionskald": r"\b\w+\(\)",
}


def test_siden_har_ingen_kodenavne(side):
    tekst = " ".join(side.tekst)
    fund = {navn: sorted(set(re.findall(m, tekst)))[:8] for navn, m in TEKNISKE_MOENSTRE.items() if re.search(m, tekst)}
    assert not fund, fund


def test_kodeblokkene_er_kun_formler_og_diagrammer(side):
    for blok in side.pre:
        assert not re.search(r"\.(py|js|toml)\b|\b[a-z]{2,}_[a-z]{2,}\b", blok), blok


def test_alle_ankre_findes(side):
    assert side.ankre and set(side.ankre) <= side.ids


def test_hovedafsnittene_er_med(side):
    tekst = " ".join(side.tekst)
    for afsnit in ("Data, privatliv og sikkerhed", "Indlæsning af PensionsInfo-rapporten", "Beregningsmotoren år for år",
                   "Find bedste plan", "Forenklinger, begrænsninger og kendte afvigelser"):
        assert afsnit in tekst, afsnit


def test_siden_har_csp_og_kun_sit_eget_script():
    # 039b: knappen "Tilbage til beregningen" lukker fanen; scriptet ligger på sidens egen adresse.
    html = metode_html.side(MD)
    assert "Content-Security-Policy" in html and "script-src 'self'" in html and "connect-src 'self'" in html
    assert re.findall(r"<script[^>]*>", html) == ['<script src="saadan-fungerer.js" defer>']
    assert 'id="tilbage-til-beregningen"' in html and "Tilbage til beregningen" in html


def test_featurenumre_fjernes():
    md = "Udjævning (feature 010) virker. Equalizer (fordeling, 033/033b/037) og usikkerhed (018 og 019). Løn (017c)."
    html, _ = metode_html.til_html(md)
    assert html == "<p>Udjævning virker. Equalizer (fordeling) og usikkerhed. Løn.</p>"
