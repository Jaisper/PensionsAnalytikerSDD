"""Feature 031 — forsikringerne i PensionsInfo-rapporten (død, tab af arbejdsevne, kritisk sygdom og
sundhed) aflæses lokalt. Syntetisk rapport med demorapportens layout og opdigtede data."""
import os
from pathlib import Path

import pytest

from pensionsoverblik.pdfimport.pensionsinfo import PensionsInfoAflaeser
from tests.app.pensionsinfo_syntetisk import (
    RAPPORT_MED_FORSIKRINGER_PDF, RAPPORT_MED_UKENDT_FORSIKRING_PDF, RAPPORT_PDF,
)

AFLAESER = PensionsInfoAflaeser(rateloft=68_700, am_bidrag=0.08)


@pytest.fixture(scope="module")
def aflaesning():
    return AFLAESER.aflaes(RAPPORT_MED_FORSIKRINGER_PDF)


def af_type(a, type_):
    return [d for d in a.daekninger if d.type == type_]


def test_doed_pr_modtager_og_kolonne(aflaesning):
    doed = af_type(aflaesning, "doed")
    assert [(d.modtager, d.selskab, d.aftalenr, d.skat, d.form, d.beloeb) for d in doed] == [
        ("Ægtefælle", "ATP", None, "A", "engang", 40_000),
        ("Ægtefælle", "Danica", "1234567890", "A", "aarraekke", 60_000),
        ("Begunstiget oplyst", "Testselskab", "5555555555", "F", "engang", 1_500_000),
    ]
    atp, danica, test = doed
    assert "Dækningsbeløbet nedtrappes." in atp.noter
    assert (danica.til_alder, danica.praemiefritagelse) == (70, False)
    assert (test.til_alder, test.praemiefritagelse) == (67, True)
    assert any("procentdel af din løn" in n for n in test.noter)


def test_tab_af_arbejdsevne(aflaesning):
    [d] = af_type(aflaesning, "erhvervsevne")
    assert (d.selskab, d.aftalenr, d.skat, d.form, d.beloeb, d.til_alder, d.praemiefritagelse) == \
        ("Testselskab", "5555555555", "S", "aarraekke", 300_000, 67, True)
    assert [(k.etiket, k.aarligt_beloeb) for k in d.kolonner] == [("Mistet arbejdsevne", 300_000), ("Indtil 67 år", 300_000)]


def test_kritisk_sygdom(aflaesning):
    [d] = af_type(aflaesning, "kritisk_sygdom")
    assert (d.selskab, d.skat, d.form, d.beloeb, d.til_alder, d.praemiefritagelse) == \
        ("Testselskab", "F", "engang", 150_000, 67, True)


def test_kritisk_sygdom_for_boern(aflaesning):
    # Undertitlen "Hvis du har børn under en vis alder" (set i en rigtig rapport, 2026-11-01).
    [d] = af_type(aflaesning, "kritisk_sygdom_boern")
    assert (d.selskab, d.skat, d.form, d.beloeb) == ("Testselskab", "F", "engang", 50_000)


def test_sundhedsforsikring(aflaesning):
    [d] = af_type(aflaesning, "sundhed")
    assert (d.selskab, d.aftalenr, d.beloeb, d.til_alder, d.praemiefritagelse) == \
        ("Testselskab", "7777777777", 100_000, 67, False)


def test_ordningerne_er_uaendrede(aflaesning):
    uden = AFLAESER.aflaes(RAPPORT_PDF)
    assert [(o.aftalenr, o.kategori, o.saldo) for o in aflaesning.ordninger] == \
        [(o.aftalenr, o.kategori, o.saldo) for o in uden.ordninger]
    assert uden.daekninger == [] and uden.bemaerkninger == []


def test_ukendt_layout_springes_over_med_en_bemaerkning():
    a = AFLAESER.aflaes(RAPPORT_MED_UKENDT_FORSIKRING_PDF)
    assert af_type(a, "doed") == []
    assert af_type(a, "erhvervsevne") and af_type(a, "kritisk_sygdom")
    assert any("død" in b for b in a.bemaerkninger)
    assert a.ordninger


DEMO = os.environ.get("PENSIONSINFO_DEMO")


@pytest.mark.skipif(not DEMO or not Path(DEMO).exists(), reason="Sæt PENSIONSINFO_DEMO til PensionsInfos demorapport")
def test_demo_rapport_lokalt():
    """PensionsInfos demorapport ("Demo Demosen", fiktive data). Ligger ikke i repoet."""
    a = AFLAESER.aflaes(Path(DEMO).read_bytes())
    doed = af_type(a, "doed")
    assert [(d.modtager, d.selskab, d.skat, d.beloeb, d.til_alder) for d in doed] == [
        ("Ægtefælle", "ATP", "A", 75_000, None),
        ("Nærmeste pårørende - inkl. samlever", "Nykredit Bank", "F", 231_000, 80),
        ("Begunstiget oplyst", "PFA Pension", "F", 2_258_000, 68),
        ("Begunstiget oplyst", "PFA Pension", "A", 1_236_000, None),
    ]
    assert sum(d.beloeb for d in doed) == 3_800_000
    assert [d.praemiefritagelse for d in doed] == [None, None, True, False]
    assert [(d.modtager, d.selskab, d.beloeb) for d in af_type(a, "doed_boern")] == [("Børn", "ATP", 50_000)]
    [tae] = af_type(a, "erhvervsevne")
    assert (tae.selskab, tae.skat, tae.form, tae.beloeb, tae.til_alder, tae.praemiefritagelse) == \
        ("PFA Pension", "S", "aarraekke", 451_000, 68, True)
    [ks] = af_type(a, "kritisk_sygdom")
    assert (ks.selskab, ks.skat, ks.form, ks.beloeb, ks.til_alder) == ("PFA Pension", "F", "engang", 500_000, 68)
    sundhed = af_type(a, "sundhed")
    assert {d.selskab for d in sundhed} == {"PFA Pension"} and sum(d.beloeb or 0 for d in sundhed) == 125_000
    assert af_type(a, "sundhed_boern")
    assert a.bemaerkninger == []
