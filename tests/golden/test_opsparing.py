"""Feature 013 T001 — opsparing uden for pension (bank) som aktiv i kernen (US2, US4, SC-001, SC-003).

Banken forrentes med 009-bufferens rente (pensionens afkast før PAL-skat). Afkastet er positiv
kapitalindkomst (PSL § 4): det beskattes (bundfradrag og skatteloft, PSL § 7 og § 19) og indgår
i pensionstillæggets indtægtsgrundlag (LSP § 29). Saldoen pr. 1. januar tæller i ældrechecks
formuegrænse (LSP § 72 d, stk. 2).

Profilen er 68 år og folkepensionist (født 1958, folkepensionsalder 67) uden private ordninger,
så første udbetalingsår er i år, og den normale udbetaling er ens hvert år ved inflation 0.
"""
from datetime import date

import pytest

from pensionskerne import Aktiv, Antagelser, Ordning, Pensionsprofil, beregn
from pensionskerne.register.opslag import Regelopslag
from tests.conftest import BEREGNINGSDATO

NUL = Antagelser(afkast_efter_pal=0.0, inflation=0.0)
AFKAST = Antagelser(afkast_efter_pal=0.04, inflation=0.0)


def pensionist(*opsparing, foedt=date(1958, 2, 1), ordninger=()):
    return Pensionsprofil(foedselsdato=foedt, civilstand="enlig", kommune="aarhus", atp_aarlig=15_000,
                          ordninger=ordninger, opsparing=opsparing)


def rente(ant=AFKAST) -> float:
    return ant.afkast_efter_pal / (1 - Regelopslag(2026, 2026, 0.0).v("pal.sats"))


def kilde(aar, type_) -> float:
    return next((k.brutto for k in aar.kilder if k.type == type_), 0.0)


def test_uden_opsparing_er_beregningen_uaendret():
    uden = beregn(pensionist(), AFKAST, 2026, BEREGNINGSDATO)
    nul = beregn(pensionist(Aktiv("bank", 0)), AFKAST, 2026, BEREGNINGSDATO)
    assert [a.netto_i_alt for a in nul.aar] == [a.netto_i_alt for a in uden.aar]
    assert [j.jaevn for j in nul.jaevn.aar] == [j.jaevn for j in uden.jaevn.aar]


def test_bank_i_planen_fordeles_ligeligt_uden_rente():
    # Rente 0 og en flad normal udbetaling: hvert års faste beløb stiger med saldo / antal år.
    # 100.000 kr. er under formuegrænsen, så ældrechecken er uændret.
    uden = beregn(pensionist(), NUL, 2026, BEREGNINGSDATO)
    med = beregn(pensionist(Aktiv("bank", 100_000)), NUL, 2026, BEREGNINGSDATO)
    n = len(med.aar)
    for j_med, j_uden in zip(med.jaevn.aar, uden.jaevn.aar):
        assert j_med.jaevn == pytest.approx(j_uden.jaevn + 100_000 / n)
    assert all(j.buffer_rest >= -1e-6 for j in med.jaevn.aar)  # aldrig lån (010)
    assert med.jaevn.aar[-1].buffer_rest == pytest.approx(0, abs=1e-6)


def test_bank_i_planen_haever_det_faste_beloeb_med_rente():
    uden = beregn(pensionist(), AFKAST, 2026, BEREGNINGSDATO)
    med = beregn(pensionist(Aktiv("bank", 500_000)), AFKAST, 2026, BEREGNINGSDATO)
    # Mindre end saldo / antal år: afkastet beskattes, og formuen over grænsen koster ældrechecken.
    assert min(j.jaevn for j in med.jaevn.aar) > min(j.jaevn for j in uden.jaevn.aar) + 500_000 / len(med.aar) * 0.5
    assert kilde(med.aar[0], "aeldrecheck") == 0 < kilde(uden.aar[0], "aeldrecheck")
    assert all(j.buffer_rest >= -1e-6 for j in med.jaevn.aar)
    assert any(a.kapitalindkomst > 0 for a in med.aar)


def test_uroert_bank_vokser_og_afkastet_er_kapitalindkomst():
    s, r = 200_000, rente()
    res = beregn(pensionist(Aktiv("bank", s, i_plan=False)), AFKAST, 2026, BEREGNINGSDATO)
    o = Regelopslag(2026, 2026, 0.0)
    marginal = o.v("skat.bundskat") + o.kommuneskat("aarhus")
    for n, a in enumerate(res.aar):
        # Kapitalindkomsten er den urørte banks afkast plus bufferens (udjævningen kan spare op).
        assert a.kapitalindkomst >= s * (1 + r) ** n * r - 1e-6
        # Under bundfradraget (55.000 kr.) og oven på en personlig indkomst, der bruger
        # personfradraget: kun bund- og kommuneskat (PSL § 7, stk. 1).
        if a.kapitalindkomst < o.v("skat.kapitalindkomst.bundfradrag"):
            assert a.skat_kapitalindkomst == pytest.approx(a.kapitalindkomst * marginal)
    for n, f in enumerate(res.formue):
        assert f.uden_for_plan == pytest.approx(s * (1 + r) ** (n + 1))


@pytest.mark.parametrize("saldo, har_aeldrecheck", [(108_000, True), (108_001, False)])
def test_uroert_bank_taeller_i_aeldrechecks_formuegraense(saldo, har_aeldrecheck):
    # Rente 0: saldoen er den samme hvert år. Grænsen er 108.000 kr. (over grænsen: ingen check).
    res = beregn(pensionist(Aktiv("bank", saldo, i_plan=False)), NUL, 2026, BEREGNINGSDATO)
    assert Regelopslag(2026, 2026, 0.0).v("yd.aeldrecheck.formuegraense") == 108_000
    assert all((kilde(a, "aeldrecheck") > 0) == har_aeldrecheck for a in res.aar)


def test_aeldrechecken_bortfalder_i_de_aar_formuen_er_over_graensen():
    # Med rente vokser formuen over grænsen. Ældrechecken gives i præcis de år, hvor formuen
    # pr. 1. januar er under grænsen (SC-003).
    res = beregn(pensionist(Aktiv("bank", 100_000, i_plan=False)), AFKAST, 2026, BEREGNINGSDATO)
    graense = Regelopslag(2026, 2026, 0.0).v("yd.aeldrecheck.formuegraense")
    primo = res.formue_primo()
    aeldrecheck = {a.alder: kilde(a, "aeldrecheck") for a in res.aar}
    assert aeldrecheck[68] > 0 and aeldrecheck[90] == 0
    assert all((v > 0) == (primo[alder] <= graense) for alder, v in aeldrecheck.items())


def test_restformue_er_start_plus_afkast_minus_traek():
    s, r = 300_000, rente()
    res = beregn(pensionist(Aktiv("a", s, i_plan=False), Aktiv("b", s)), AFKAST, 2026, BEREGNINGSDATO)
    assert res.formue[-1].uden_for_plan == pytest.approx(s * (1 + r) ** len(res.aar))
    assert res.formue[-1].i_plan == pytest.approx(0, abs=1e-6)   # planen bruger opsparingen op (010)
    # Primo = ultimo året før; i dag er primo startsaldoen.
    primo = res.formue_primo()
    assert primo[68] == pytest.approx(2 * s)
    assert primo[69] == pytest.approx(res.formue[0].i_plan + res.formue[0].uden_for_plan)


def test_opsparing_vokser_frem_til_foerste_udbetaling():
    # 60-årig med en ratepension fra 65: banken vokser 5 år med renten før første udbetalingsår og
    # indsættes derefter i bufferen. Skatten af afkastet før da betales af lønnen (ikke modelleret).
    s, r = 100_000, rente()
    rate = Ordning("r", "ratepension", 500_000, 65, oprettet=date(2010, 1, 1), udbetaling_aar=10)
    res = beregn(pensionist(Aktiv("bank", s), foedt=date(1966, 3, 1), ordninger=(rate,)), AFKAST, 2026, BEREGNINGSDATO)
    assert res.aar[0].alder == 65
    foer = {f.alder: f for f in res.formue}
    assert min(foer) == 60
    assert foer[64].i_plan == pytest.approx(s * (1 + r) ** 5)
    assert any(a.kode == "OPSPARING_FOER_UDBETALING" for a in res.advarsler)


def test_ingen_advarsel_om_tiden_foer_udbetaling_for_en_pensionist():
    res = beregn(pensionist(Aktiv("bank", 100_000)), AFKAST, 2026, BEREGNINGSDATO)
    assert not any(a.kode == "OPSPARING_FOER_UDBETALING" for a in res.advarsler)
