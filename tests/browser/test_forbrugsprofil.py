"""Feature 033 — equalizeren for faldende udbetalinger. Den syntetiske rapport med løn og stopalder 64:
båndene er 64–68, 69–73, 74–78, 79–84 og 85+. Beløbene regnes med det samme, og den bedste plan søges
først, når borgeren trykker "Find bedste plan med denne fordeling"."""
import pytest

from tests.browser.test_stopalder_graf import med_loen  # noqa: F401 (fixture)
from tests.browser.test_tidslinje import marker_resultat, vent_paa_ny_beregning

pytestmark = pytest.mark.browser

SKYDERE = "#forbrug-baand input[type=range]"


def procenter(side):
    return side.evaluate("tilstand.aktuelleSvar.antagelser.forbrugsprofil ?? null")


def efter_soegning(side, handling):
    """Udfør handlingen og vent, til den nye søgning efter den bedste plan er færdig."""
    nr = side.evaluate("autoNr")
    handling()
    side.wait_for_function(f"() => autoNr > {nr} && document.body.dataset.plan === 'klar'", timeout=120000)


def saet(side, i, vaerdi):
    """Flyt en skyder og vent på den nye beregning (uden søgning)."""
    skyder = side.locator(SKYDERE).nth(i)
    marker_resultat(side)
    skyder.fill(vaerdi)
    skyder.dispatch_event("input")
    vent_paa_ny_beregning(side)


def test_et_baand_pr_periode_og_det_foerste_er_laast(med_loen):
    skydere = med_loen.locator(SKYDERE)
    assert skydere.count() == 5
    assert skydere.first.is_disabled()
    navne = [skydere.nth(i).get_attribute("aria-label") for i in range(5)]
    assert navne[0].startswith("64–68 år") and navne[-1].startswith("85 år og derover")
    assert all(skydere.nth(i).input_value() == "100" for i in range(5))
    assert procenter(med_loen) is None                       # flad, før borgeren rører skyderne
    # Beløbene er altid i dagens kroner, så procenterne kan sammenlignes direkte.
    assert "i dagens kroner, også når grafen viser årets kroner" in med_loen.inner_text("#forbrug-kroner")


def test_saenk_et_baand_med_tastaturet(med_loen):
    foer = med_loen.evaluate("tilstand.v.hovedtal.maaned")
    sidste = med_loen.locator(SKYDERE).last

    marker_resultat(med_loen)
    sidste.focus()
    for _ in range(4):
        sidste.press("ArrowDown")                            # 100 → 80 i trin på 5
    med_loen.wait_for_function("() => tilstand.aktuelleSvar.antagelser.forbrugsprofil?.[4] === 0.8")
    vent_paa_ny_beregning(med_loen)
    assert procenter(med_loen) == [1, 1, 1, 1, 0.8]
    assert "80 %" in med_loen.locator(SKYDERE).last.get_attribute("aria-valuetext")
    assert med_loen.evaluate("tilstand.v.hovedtal.maaned") >= foer
    assert "fra 85" in med_loen.inner_text("#hovedtal-forklaring")


def test_baandene_kan_ikke_stige(med_loen):
    saet(med_loen, 2, "70")                                   # 74–78 til 70 %: senere bånd følger med ned
    assert procenter(med_loen) == [1, 1, 0.7, 0.7, 0.7]
    saet(med_loen, 3, "90")                                   # 79–84 kan ikke komme over 74–78
    assert procenter(med_loen) == [1, 1, 0.7, 0.7, 0.7]
    assert med_loen.locator(SKYDERE).nth(3).input_value() == "70"


def test_knappen_soeger_den_bedste_plan_fra_egen_plan(med_loen):
    egen_foer = med_loen.evaluate("tilstand.planer && structuredClone(tilstand.planer.egen.ordninger)")
    knap = med_loen.get_by_role("button", name="Find bedste plan med denne fordeling")
    assert knap.is_hidden()
    nr = med_loen.evaluate("autoNr")
    saet(med_loen, 3, "85")
    saet(med_loen, 4, "70")
    assert med_loen.evaluate("autoNr") == nr                  # ingen søgning, mens borgeren justerer
    assert knap.is_visible()
    efter_soegning(med_loen, knap.click)
    assert knap.is_hidden()
    assert procenter(med_loen) == [1, 1, 1, 0.85, 0.7]
    planer = med_loen.evaluate("tilstand.planer")
    if planer is not None:
        # Den bedste plan har profilen, og "min egen plan" er stadig borgerens egen, nu med profilen.
        assert planer["bedste"]["antagelser"]["forbrugsprofil"] == [1, 1, 1, 0.85, 0.7]
        assert planer["egen"]["antagelser"]["forbrugsprofil"] == [1, 1, 1, 0.85, 0.7]
        if egen_foer is not None:
            assert planer["egen"]["ordninger"] == egen_foer
    assert med_loen.fejl == []


def test_samme_beloeb_hele_livet_nulstiller(med_loen):
    saet(med_loen, 4, "95")
    marker_resultat(med_loen)
    med_loen.get_by_role("button", name="Samme beløb hele livet").click()
    vent_paa_ny_beregning(med_loen)
    assert procenter(med_loen) is None
    assert med_loen.get_by_role("button", name="Samme beløb hele livet").is_hidden()


def test_note_naar_et_baand_alligevel_stiger(med_loen):
    # Kommer pengene først senere, kan et senere bånd give mere end det foregående, fordi udjævningen
    # ikke låner (010). Så skal der stå hvorfor.
    for i, v in ((2, "90"), (3, "80"), (4, "70")):
        saet(med_loen, i, v)
    baand = med_loen.evaluate("tilstand.v.forbrug.baand")
    stiger = [b for f, b in zip(baand, baand[1:]) if b["maaned"] > f["maaned"] + 100]
    note = med_loen.locator("#forbrug-note")
    assert note.is_visible() == bool(stiger)
    if stiger:
        assert f"Fra {stiger[0]['fra']} år" in note.inner_text()
        assert "Find bedste plan med denne fordeling" in note.inner_text()
    assert "Med din fordeling over tid er beløbet" in med_loen.inner_text("#hovedtal-forklaring")


def test_axe(med_loen):
    med_loen.add_script_tag(url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.1/axe.min.js")
    fejl = med_loen.evaluate("async () => (await axe.run('#forbrug', {runOnly: "
                             "['wcag2a','wcag2aa','wcag21aa','wcag22aa']})).violations.map(v => v.id)")
    assert fejl == []
    assert med_loen.fejl == []


def test_kolonnerne_flugter_og_har_et_beloeb(med_loen):
    # Set i browseren: første kolonne rykkede ned, når beløbet manglede.
    saet(med_loen, 2, "90")
    toppe = med_loen.evaluate("[...document.querySelectorAll('.forbrug__kolonne')].map(k => k.getBoundingClientRect().top)")
    assert max(toppe) - min(toppe) < 1
    assert all(t.strip() for t in med_loen.locator(".forbrug__kr").all_inner_texts())


def test_beloebene_er_altid_i_dagens_kroner(med_loen):
    saet(med_loen, 4, "80")
    dagens = med_loen.locator(".forbrug__kr").all_inner_texts()
    med_loen.check("input[name=kroner][value=aarets]")
    med_loen.wait_for_function("() => tilstand.kroner === 'aarets'")
    assert med_loen.locator(".forbrug__kr").all_inner_texts() == dagens
