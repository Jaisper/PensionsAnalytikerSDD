"""Feature 013b T002 — frit depot og aktiesparekonto (US2, US3, US4, FR-001–FR-004).

Samme rente for alle typer (pensionens afkast før PAL-skat). Puljen deles i lag: bank, depot og
ASK. Træk fra depotet realiserer gevinsten forholdsmæssigt og beskattes som aktieindkomst (PSL
§ 8 a), der indgår i § 29. ASK-afkastet lagerbeskattes med 17 % og indgår ikke i § 29.

Pensionisten er 68 år (født 1958, folkepensionsalder 67) uden private ordninger, så første
udbetalingsår er i år, og den normale udbetaling er ens hvert år ved inflation 0.
"""
from dataclasses import replace
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Loen, Ordning, Partner, Pensionsprofil, beregn
from pensionskerne.husstand import partner_fra
from pensionskerne.register.opslag import Regelopslag
from pensionskerne.regler.aktier import aktieindkomst_skat
from tests.conftest import BEREGNINGSDATO

NUL = Antagelser(afkast_efter_pal=0.0, inflation=0.0)
AFKAST = Antagelser(afkast_efter_pal=0.04, inflation=0.0)
O = Regelopslag(2026, 2026, 0.0)
RATE = Ordning("rate", "ratepension", 1_000_000, 68, oprettet=date(2010, 1, 1), udbetaling_aar=10)


def pensionist(*opsparing, civilstand="enlig", partner=None):
    return Pensionsprofil(foedselsdato=date(1958, 2, 1), civilstand=civilstand, kommune="aarhus", atp_aarlig=15_000,
                          opsparing=opsparing, partner=partner)


def tres_aarig(*opsparing, loen=None):
    return Pensionsprofil(foedselsdato=date(1966, 3, 1), civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=(RATE,), opsparing=opsparing, loen=loen)


def regn(profil, ant=NUL):
    return beregn(profil, ant, 2026, BEREGNINGSDATO)


def flaget(res, flag) -> bool:
    return any(flag in a.flag for a in res.aar)


def rente(ant=AFKAST) -> float:
    return ant.afkast_efter_pal / (1 - O.v("pal.sats"))


def test_depot_i_planen_realiserer_gevinsten_forholdsmaessigt():
    uden = regn(pensionist())
    # Under ældrechecks formuegrænse hele vejen, så fastpunktet ikke vipper ved grænsen.
    res = regn(pensionist(Aktiv("depot", 60_000, type="depot", urealiseret_gevinst=24_000)))
    # Rente 0: gevinstandelen er 40 % i hele perioden, og hele depotet sælges.
    assert sum(a.aktieindkomst for a in res.aar) == pytest.approx(24_000, rel=1e-6)
    for j, a, u in zip(res.jaevn.aar, res.aar, uden.aar):
        assert a.aktieindkomst == pytest.approx(0.4 * j.fra_buffer, abs=12)  # fastpunktets tolerance
        assert a.skat_aktieindkomst == pytest.approx(aktieindkomst_skat(a.aktieindkomst, O))
        # Aktieindkomsten indgår i § 29-grundlaget; den er ikke kapitalindkomst.
        assert a.indtaegtsgrundlag == pytest.approx(u.indtaegtsgrundlag + a.aktieindkomst, abs=100)
        assert a.kapitalindkomst == 0
    assert res.jaevn.aar[-1].buffer_rest == pytest.approx(0, abs=1e-6)
    assert flaget(res, "forenkling:aktieafkast_som_kursgevinst")


def test_standardandelen_for_urealiseret_gevinst():
    res = regn(pensionist(Aktiv("depot", 200_000, type="depot")))
    assert sum(a.aktieindkomst for a in res.aar) == pytest.approx(200_000 * NUL.depot_urealiseret_andel, rel=1e-6)
    assert "antagelse.depot_urealiseret_andel" in res.sporing_samlet


def test_depot_giver_mindre_end_bank_naar_der_er_gevinst():
    bank = regn(pensionist(Aktiv("b", 200_000)))
    depot = regn(pensionist(Aktiv("d", 200_000, type="depot", urealiseret_gevinst=100_000)))
    assert min(j.jaevn for j in depot.jaevn.aar) < min(j.jaevn for j in bank.jaevn.aar)


def test_aktiesparekonto_lagerbeskattes_og_er_ikke_i_paragraf_29():
    uden = regn(pensionist(), AFKAST)
    res = regn(pensionist(Aktiv("ask", 150_000, type="ask")), AFKAST)
    r = rente()
    for j, a, u in zip(res.jaevn.aar, res.aar, uden.aar):
        assert a.kapitalindkomst == pytest.approx(0, abs=1e-6) and a.aktieindkomst == 0
        assert a.skat_aktiesparekonto == pytest.approx(O.v("ask.sats") * max(0.0, j.buffer_rest) * r / (1 + r), abs=1)
        assert a.indtaegtsgrundlag == pytest.approx(u.indtaegtsgrundlag)
    assert any(a.skat_aktiesparekonto > 0 for a in res.aar)


def test_traekraekkefoelgen_bank_foer_depot_og_kan_aendres():
    opsparing = (Aktiv("b", 100_000), Aktiv("d", 100_000, type="depot", urealiseret_gevinst=50_000))
    standard = regn(pensionist(*opsparing))
    assert standard.aar[0].aktieindkomst == 0 < standard.aar[-1].aktieindkomst
    omvendt = regn(pensionist(*opsparing), replace(NUL, traekraekkefoelge=("depot", "bank", "ask")))
    assert omvendt.aar[0].aktieindkomst > 0 == omvendt.aar[-1].aktieindkomst


def test_uroert_depot_vokser_uden_skat_og_taeller_i_formuen():
    s, r = 300_000, rente()
    res = regn(pensionist(Aktiv("d", s, type="depot", i_plan=False)), AFKAST)
    assert all(a.aktieindkomst == 0 and a.skat_aktieindkomst == 0 and a.kapitalindkomst < 1 for a in res.aar)
    for n, f in enumerate(res.formue):
        assert f.uden_for_plan == pytest.approx(s * (1 + r) ** (n + 1))


def test_uroert_aktiesparekonto_betaler_lagerskat_af_udbetalingen():
    s, r = 100_000, rente()
    res = regn(pensionist(Aktiv("a", s, type="ask", i_plan=False)), AFKAST)
    for n, a in enumerate(res.aar):
        assert a.skat_aktiesparekonto >= O.v("ask.sats") * s * (1 + r) ** n * r - 1e-6


def test_aktiesparekonto_foer_foerste_udbetaling_vokser_efter_skat():
    # 60-årig uden løn med ratepension fra 68: ASK vokser med afkastet efter 17 % frem til 68.
    s, r = 100_000, rente()
    res = regn(tres_aarig(Aktiv("a", s, type="ask", i_plan=False)), AFKAST)
    assert res.formue[0].uden_for_plan == pytest.approx(s * (1 + r * (1 - O.v("ask.sats"))))
    assert not flaget(res, "forenkling:opsparing_skat_foer_udbetaling")


def test_loebende_indskud_paa_aktiesparekontoen_i_arbejdsaarene():
    profil = tres_aarig(Aktiv("a", 50_000, type="ask", aarligt_indskud=20_000), loen=Loen(500_000, stop_alder=64))
    res = regn(profil, AFKAST)
    for a in res.aar:
        assert a.indskud_opsparing == pytest.approx(20_000 if a.alder < 64 else 0)
    # Indskuddet trækkes fra årets rådighedsbeløb i arbejdsårene.
    a = res.aar_ved(61)
    assert a.disponibel == pytest.approx(a.netto_i_alt - a.skat_kapitalindkomst - a.skat_aktieindkomst
                                         - a.skat_aktiesparekonto - 20_000)
    assert not any(x.kode == "ASK_OVER_LOFT" for x in res.advarsler)
    assert sum(a.aktieindkomst for a in res.aar) == 0
    assert flaget(res, "forenkling:ask_indskud_lig_saldo")
    over = regn(replace(profil, opsparing=(Aktiv("a", 170_000, type="ask", aarligt_indskud=20_000),)), AFKAST)
    assert any(x.kode == "ASK_OVER_LOFT" for x in over.advarsler)
    assert sum(a.aktieindkomst for a in over.aar) > 0      # det overskydende står i frit depot


def test_stort_salg_over_progressionsgraensen_giver_advarsel():
    res = regn(pensionist(Aktiv("d", 3_000_000, type="depot", urealiseret_gevinst=2_000_000)))
    adv = next(a for a in res.advarsler if a.kode == "AKTIEINDKOMST_OVER_GRAENSE")
    assert adv.aldre[0] == res.aar[0].alder
    assert "skat.aktieindkomst.progressionsgraense" in adv.registerposter
    assert not any(a.kode == "AKTIEINDKOMST_OVER_GRAENSE"
                   for a in regn(pensionist(Aktiv("d", 100_000, type="depot"))).advarsler)


def test_gifte_faar_aegtefaellens_uudnyttede_progressionsgraense():
    depot = Aktiv("d", 3_000_000, type="depot", urealiseret_gevinst=2_000_000)
    ukendt = Partner(foedselsdato=date(1958, 6, 1))
    kendt = Partner(foedselsdato=date(1958, 6, 1), aktieindkomst_pr_aar={k: 0.0 for k in range(2026, 2066)})
    uden = regn(pensionist(depot, civilstand="gift", partner=ukendt))
    med = regn(pensionist(depot, civilstand="gift", partner=kendt))
    a, b = uden.aar[0], med.aar[0]
    assert b.skat_aktieindkomst == pytest.approx(aktieindkomst_skat(b.aktieindkomst, O, ekstra_graense=79_400))
    assert a.skat_aktieindkomst == pytest.approx(aktieindkomst_skat(a.aktieindkomst, O))
    assert min(j.jaevn for j in med.jaevn.aar) > min(j.jaevn for j in uden.jaevn.aar)


def test_partneren_faar_aktieindkomsten_til_paragraf_29_og_overfoerslen():
    profil = pensionist(Aktiv("d", 500_000, type="depot", urealiseret_gevinst=250_000))
    res = regn(profil)
    p = partner_fra(res, profil, NUL)
    a = res.aar[0]
    assert a.aktieindkomst > 0
    assert p.aktieindkomst_pr_aar[a.kalenderaar] == pytest.approx(a.aktieindkomst)
    assert p.indkomst_pr_aar[a.kalenderaar].oevrig_indkomst >= a.aktieindkomst


def test_formuen_omfatter_depot_og_aktiesparekonto():
    res = regn(pensionist(Aktiv("d", 100_000, type="depot", i_plan=False), Aktiv("a", 50_000, type="ask")))
    assert res.formue_start == 150_000
    assert res.formue_primo()[res.aar[1].alder] > 100_000


def test_fastpunktet_konvergerer_med_depot_og_aktiesparekonto():
    # Plan-risikoen (013b): flere skattekasser i fastpunktet. Formuen krydser ældrechecks grænse.
    for opsparing in ((Aktiv("d", 400_000, type="depot"),),
                      (Aktiv("b", 100_000), Aktiv("d", 300_000, type="depot"), Aktiv("a", 150_000, type="ask", i_plan=False))):
        res = regn(pensionist(*opsparing), AFKAST)
        assert not any(a.kode == "BUFFER_IKKE_KONVERGERET" for a in res.advarsler)
        assert res.buffer_iterationer <= 10
