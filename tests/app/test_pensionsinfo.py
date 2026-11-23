"""Lokal PensionsInfo-parser (feature 003, R005) mod en syntetisk rapport med rigtigt layout."""
import os
from datetime import date
from pathlib import Path

import pytest

from pensionsoverblik.pdfimport.aflaeser import vaelg_aflaeser
from pensionsoverblik.pdfimport.pensionsinfo import PensionsInfoAflaeser
from pensionsoverblik.pdfimport.tekst import foedselsdato_fra_rapport, udtraek_sider
from tests.app.pensionsinfo_syntetisk import RAPPORT_MED_SALDO_PDF, RAPPORT_PDF, RAPPORT_UDEN_INDHOLD_PDF

AFLAESER = PensionsInfoAflaeser(rateloft=68_700, am_bidrag=0.08)


@pytest.fixture(scope="module")
def aflaesning():
    return AFLAESER.aflaes(RAPPORT_PDF)


def _ordning(a, nr, kategori):
    return next(o for o in a.ordninger if o.aftalenr == nr and o.kategori == kategori)


def test_foedselsdato_fra_maskeret_cpr_og_udskriftsaar():
    assert foedselsdato_fra_rapport(udtraek_sider(RAPPORT_PDF)[0]) == date(1968, 3, 15)


def test_aftalenumre_forveksles_ikke_med_cpr():
    assert foedselsdato_fra_rapport("Identifikation 1002114321 og 1234567890") is None


def test_atp_og_folkepension(aflaesning):
    assert aflaesning.atp_aarlig == 20_000
    assert not [o for o in aflaesning.ordninger if o.selskab and o.selskab.startswith(("ATP", "Folkepension"))]


def test_kun_forsikring_springes_over(aflaesning):
    assert "11111-2222" not in {o.aftalenr for o in aflaesning.ordninger}


def test_kapitalpension(aflaesning):
    o = _ordning(aflaesning, "1234567890", "kapitalpension")
    assert (o.selskab, o.saldo, o.aarlig_indbetaling) == ("Danica", 800_000, 0)
    assert (o.tidligste_udbetalingsalder, o.aftalt_udbetalingsalder, o.afgift_betalt) == (60, 65, False)


def test_ratepension_med_periode(aflaesning):
    o = _ordning(aflaesning, "5555555555", "ratepension")
    assert (o.tidligste_udbetalingsalder, o.aftalt_udbetalingsalder) == (64, 67)
    assert o.udbetalingsperioder[0].etiket == "67-76 år"


def test_saldo_og_indbetaling_fordeles_paa_produkter_under_samme_aftale(aflaesning):
    rate = _ordning(aflaesning, "5555555555", "ratepension")
    liv = _ordning(aflaesning, "5555555555", "livsvarig")
    # vægte som i legacy: nutidsværdi med 4 % — rate over 10 år, livsvarig over 25 år
    a = lambda n: (1 - 1.04 ** -n) / 0.04
    v_rate, v_liv = 150_000 * a(10), 60_000 * a(25)
    assert rate.saldo + liv.saldo == pytest.approx(2_000_000, abs=1)
    assert rate.saldo == round(2_000_000 * v_rate / (v_rate + v_liv))
    # indbetaling 100.000 før AM-bidrag → 92.000; ratepension op til loftet, resten livsvarig
    assert (rate.aarlig_indbetaling, liv.aarlig_indbetaling) == (68_700, 23_300)
    assert any("skønsmæssigt" in n for n in rate.noter)


def test_saldo_og_indbetaling_pr_produkt_bruges_naar_rapporten_oplyser_dem():
    # Lange rapporter (2026): "Pension - flere oplysninger" har opsparing og indbetaling pr. produkt.
    a = AFLAESER.aflaes(RAPPORT_MED_SALDO_PDF)
    rate = _ordning(a, "5555555555", "ratepension")
    liv = _ordning(a, "5555555555", "livsvarig")
    assert (rate.saldo, liv.saldo) == (1_400_000, 600_000)
    # før AM-bidrag som aftalens indbetaling → 92 %; "Der indbetales ikke" er 0 kr.
    assert (rate.aarlig_indbetaling, liv.aarlig_indbetaling) == (64_400, 0)
    assert not any("skønsmæssigt" in n for n in rate.noter + liv.noter)
    assert _ordning(a, "1234567890", "kapitalpension").saldo == 800_000   # aftalens saldo som før


def test_saldo_pr_produkt_men_indbetaling_kun_for_nogle():
    # Regression: alle produkter har oplyst saldo, men ét mangler indbetaling ("Der er ikke leveret
    # oplysninger om indbetalingen"). Gav uendelig rekursion i _fordel, og uploaden fejlede.
    from pensionsoverblik.pdfimport.pensionsinfo import _Aftale, _fordel, _Produkt
    kap = _Produkt("A", "X", "engang", [100_000], type_tekst="Kapitalpension", oplyst_saldo=100_000)
    rate = _Produkt("S", "X", "aarraekke", [200_000], type_tekst="Ratepension", periode_aar=10,
                    oplyst_saldo=1_500_000, oplyst_indbetaling=60_000)
    liv = _Produkt("S", "X", "livsvarig", [20_000], type_tekst="Livsvarig pension",
                   oplyst_saldo=400_000, oplyst_indbetaling=10_000)
    _fordel(_Aftale("1", indbetaling=90_000, saldo=2_000_000), [kap, rate, liv], 60, 68_700, 0.08)
    assert (kap.saldo, rate.saldo, liv.saldo) == (100_000, 1_500_000, 400_000)
    # indbetalingen fordeles skønsmæssigt (efter AM-bidrag: 82.800): rate op til loftet, rest livsvarig
    assert (kap.indbetaling, rate.indbetaling, liv.indbetaling) == (0, 68_700, 14_100)
    assert not any("saldo er fordelt" in n for n in kap.noter + rate.noter + liv.noter)


def test_uventet_fejl_bliver_til_aflaesningsfejl(monkeypatch):
    # Fejltolerance: en uventet undtagelse i efterbehandlingen må ikke vælte uploaden.
    from pensionsoverblik.pdfimport import pensionsinfo
    from pensionsoverblik.pdfimport.aflaeser import AflaesningFejl
    def boom(*a, **k):
        raise RuntimeError("uventet")
    monkeypatch.setattr(pensionsinfo, "_fordel", boom)
    with pytest.raises(AflaesningFejl):
        AFLAESER.aflaes(RAPPORT_PDF)


def test_kun_forsikring_i_bemaerkningskolonnen():
    import pdfplumber, io
    from pensionsoverblik.pdfimport.pensionsinfo import _dine_aftaler
    from tests.app.pensionsinfo_syntetisk import RAPPORT_KUN_FORSIKRING_I_BEM_PDF
    with pdfplumber.open(io.BytesIO(RAPPORT_KUN_FORSIKRING_I_BEM_PDF)) as pdf:
        aftaler = _dine_aftaler(pdf.pages[2])
    assert aftaler["11111-2222"].kun_forsikring
    assert not aftaler["1234567890"].kun_forsikring


def test_dine_aftaler_ulaeselig_giver_bemaerkning_ikke_fejl(monkeypatch):
    from pensionsoverblik.pdfimport import pensionsinfo
    def boom(*a, **k):
        raise ValueError("uventet layout")
    monkeypatch.setattr(pensionsinfo, "_dine_aftaler", boom)
    a = AFLAESER.aflaes(RAPPORT_PDF)
    assert a.ordninger and all(o.saldo is None for o in a.ordninger)
    assert any("Dine aftaler" in b for b in a.bemaerkninger)


def test_daekninger_ulaeselige_giver_bemaerkning_ikke_fejl(monkeypatch):
    from pensionsoverblik.pdfimport import pensionsinfo
    def boom(*a, **k):
        raise ValueError("uventet layout")
    monkeypatch.setattr(pensionsinfo, "aflaes_daekninger", boom)
    a = AFLAESER.aflaes(RAPPORT_PDF)
    assert a.ordninger and a.daekninger == []
    assert any("forsikringer" in b for b in a.bemaerkninger)


def test_aftale_uden_prognose_bliver_ukendt(aflaesning):
    o = _ordning(aflaesning, "9999999999", "ukendt")
    assert o.saldo == 50_000 and o.noter


def test_hele_vejen_til_beregning():
    """Rapport → guidedata → kernen, uden fejl."""
    from pensionskerne import beregn
    from pensionsoverblik.oversaet import til_kerne
    from pensionsoverblik.pdfimport.omsaet import til_guide
    g = til_guide(AFLAESER.aflaes(RAPPORT_PDF), date(1968, 3, 15), 2026)
    for o in g["ordninger"]:
        o["saldo"] = o["saldo"] or 0
        o["udbetaling_start_alder"] = o["udbetaling_start_alder"] or 69
        o["oprettet"] = ""  # frontenden oversætter kategorien; selskabets oplyste alder har forrang
    guide = {"person": {"foedselsdato": g["person"]["foedselsdato"], "civilstand": "enlig", "kommune": "Odense"},
             "ordninger": [{**o, "id": f"o{i}"} for i, o in enumerate(g["ordninger"])], "antagelser": {}}
    profil, antagelser = til_kerne(guide)
    res = beregn(profil, antagelser, 2026, date(2026, 10, 25))
    assert res.folkepensionsalder == 69 and res.aar


def test_kun_de_noedvendige_sider_laeses(monkeypatch):
    """PensionsInfo-rapporter har altid samme hovedsektioner: indholdsfortegnelsen udpeger de få
    sider, der skal læses. Forsiden læses af API'et, bilag og øvrige sider aldrig."""
    from pensionsoverblik.pdfimport import pensionsinfo as pi
    laest = []
    original = pi._tekst
    def spion(side):
        if id(side) not in pi._TEKST:
            laest.append(side.page_number)
        return original(side)
    monkeypatch.setattr(pi, "_tekst", spion)
    AFLAESER.aflaes(RAPPORT_PDF)
    assert laest == [2, 3, 4, 5]  # indhold, aftaler, udbetalingstabel, flere oplysninger


def test_uden_indholdsfortegnelse_bruges_fallback():
    a = AFLAESER.aflaes(RAPPORT_UDEN_INDHOLD_PDF)
    assert {o.aftalenr for o in a.ordninger} == {"1234567890", "5555555555", "9999999999"}


def test_vaelg_aflaeser_er_den_lokale_parser():
    assert isinstance(vaelg_aflaeser(), PensionsInfoAflaeser)


RIGTIG = os.environ.get("PENSIONSINFO_RAPPORT")


@pytest.mark.skipif(not RIGTIG or not Path(RIGTIG).exists(), reason="Sæt PENSIONSINFO_RAPPORT til en lokal rapport")
def test_rigtig_rapport_lokalt():
    """Kører kun lokalt mod en rigtig rapport. Tjekker invarianter — ingen persondata i koden."""
    data = Path(RIGTIG).read_bytes()
    a = AFLAESER.aflaes(data)
    foedt = foedselsdato_fra_rapport(udtraek_sider(data)[0])
    assert foedt is not None and 18 <= 2026 - foedt.year <= 110
    assert a.ordninger
    for o in a.ordninger:
        assert o.kategori != "ukendt" or o.noter
        if o.aftalt_udbetalingsalder and o.tidligste_udbetalingsalder:
            assert o.aftalt_udbetalingsalder >= o.tidligste_udbetalingsalder
        assert o.saldo is None or o.saldo >= 0
