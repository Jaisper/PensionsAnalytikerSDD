"""Feature 024 — gem og genindlæs lokalt (FR-001–FR-003, SC)."""
import json

import pytest

pytestmark = pytest.mark.browser

KODE = "hemmelig-kode-42"


def gem(side, kode=KODE, gentag=None):
    side.click("#gem-knap")
    side.fill("#gem-kode", kode)
    side.fill("#gem-kode2", gentag if gentag is not None else kode)
    with side.expect_download() as dl:
        side.click("#gem-fil")
    return dl.value.path()


def aabn(side, sti, kode=KODE):
    side.click("#aabn-gemt summary")
    side.set_input_files("#gemt-fil", str(sti))
    side.fill("#gemt-kode", kode)
    side.click("#gemt-aabn")


def test_gem_og_aabn_giver_samme_resultat(resultat, ny_side):
    foer = resultat.evaluate("tilstand.aktuelleSvar")
    hovedtal = resultat.evaluate("tilstand.v.hovedtal")
    sti = gem(resultat)

    ny_side.goto(ny_side.base_url)
    ny_side.evaluate("motorKlar")
    aabn(ny_side, sti)
    ny_side.wait_for_selector("#resultat:not([hidden])")
    assert ny_side.evaluate("tilstand.aktuelleSvar") == foer
    assert ny_side.evaluate("tilstand.v.hovedtal") == hovedtal
    assert "gemte beregning" in ny_side.inner_text("#hovedtal-aendring")


def test_filen_har_ingen_persondata_i_klartekst(resultat):
    sti = gem(resultat)
    tekst = open(sti, encoding="utf-8").read()
    fil = json.loads(tekst)
    assert fil["format"] == "pensionsoverblik-gem" and fil["cipher"]["navn"] == "AES-GCM"
    foedselsdato = resultat.evaluate("tilstand.aktuelleSvar.person.foedselsdato")
    assert foedselsdato not in tekst and "Aarhus" not in tekst and "ordninger" not in tekst


def test_forkert_adgangskode_giver_fejl_og_intet_resultat(resultat, ny_side):
    sti = gem(resultat)
    ny_side.goto(ny_side.base_url)
    ny_side.evaluate("motorKlar")
    aabn(ny_side, sti, kode="forkert-kode")
    ny_side.wait_for_selector('[data-felt="gemt"] .felt__fejl')
    assert "kunne ikke åbnes" in ny_side.inner_text('[data-felt="gemt"]')
    assert ny_side.is_hidden("#resultat")


def test_for_kort_eller_forskellig_adgangskode(resultat):
    resultat.click("#gem-knap")
    resultat.fill("#gem-kode", "kort")
    resultat.fill("#gem-kode2", "kort")
    resultat.click("#gem-fil")
    assert "mindst 8 tegn" in resultat.inner_text('[data-felt="gem-kode"]')
    resultat.fill("#gem-kode", KODE)
    resultat.fill("#gem-kode2", KODE + "x")
    resultat.click("#gem-fil")
    assert "ikke ens" in resultat.inner_text('[data-felt="gem-kode2"]')


def test_axe(resultat):
    resultat.click("#gem-knap")
    resultat.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = resultat.evaluate("async () => (await axe.run(document, {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
