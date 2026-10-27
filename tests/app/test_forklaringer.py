"""Feature 020 — forklaringskataloget: dækning, niveauer, ingen tal og klarsprog (FR-002, FR-006,
FR-007, SC-001, SC-005)."""
import fnmatch
import re

import pytest

from pensionskerne import register
from pensionsoverblik import app
from pensionsoverblik.forklaring import katalog
from pensionsoverblik.katalog import ADVARSLER

NIVEAUER = ("niveau1", "niveau2", "niveau3")
# Beløb og procenter er forbudt på alle niveauer (Princip II). På niveau 1 og 2 også årstal og andre
# lange tal; niveau 3 må henvise til love som "L 117 (2023)". Paragraffer (§ 29, stk. 1) er tilladt.
BELOEB = re.compile(r"\d+[.,]\d|\d+ ?%")
LANGE_TAL = re.compile(r"\d{3,}")


def lix(tekst: str) -> float:
    tekst = re.sub(r"\{[^}]+\}", "x", tekst)
    ord_ = re.findall(r"[A-Za-zÆØÅæøå-]+", tekst)
    # Kun rigtige sætningsafslutninger: punktum o.l. efterfulgt af stort bogstav eller tekstens slutning
    # (så "kr." midt i en sætning ikke tæller).
    saetninger = max(1, len(re.findall(r"[.!?:](?=\s+[A-ZÆØÅ]|\s*$)", tekst)))
    lange = sum(1 for o in ord_ if len(o) > 6)
    return len(ord_) / saetninger + 100 * lange / len(ord_)


def test_alle_emner_har_tre_niveauer_og_ingen_tal():
    k = katalog()
    assert k["emner"]
    for e in k["emner"]:
        for n in NIVEAUER:
            assert e[n].strip(), (e["id"], n)
            tekst = re.sub(r"\{[^}]+\}", "", e[n])
            assert not BELOEB.search(tekst), (e["id"], n)
            if n != "niveau3":
                assert not LANGE_TAL.search(tekst), (e["id"], n)


def test_alle_inventarpunkter_er_daekket():
    k = katalog()
    daekket = {p for e in k["emner"] for p in e["inventar"]}
    assert set(k["inventar"]) == daekket


def test_alle_registerposter_har_et_emne():
    moenstre = [m for e in katalog()["emner"] for m in e["registerposter"]]
    for post in register.poster(2026):
        assert any(fnmatch.fnmatch(post.id, m) for m in moenstre), post.id


def test_alle_advarsler_har_et_emne():
    advarsler = {a for e in katalog()["emner"] for a in e["advarsler"]}
    assert set(ADVARSLER) <= advarsler


@pytest.mark.parametrize("emne", [e["id"] for e in katalog()["emner"]])
def test_niveau1_er_klarsprog(emne):
    e = next(x for x in katalog()["emner"] if x["id"] == emne)
    assert lix(e["niveau1"]) < 35, (emne, round(lix(e["niveau1"]), 1))
    assert "§" not in e["niveau1"]


def test_indgangen_giver_kataloget():
    assert app.forklaringer() == katalog()
