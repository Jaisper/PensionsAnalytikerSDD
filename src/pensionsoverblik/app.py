"""Indgangspunkt for brugerfladen (feature 005, D1). Kaldes af browserens worker i Pyodide.

Rene funktioner uden I/O: input kommer kun som argumenter, og dagens dato gives af browseren
(Princip VI). Svar og fejl er data — {"ok": True, "data": ...} eller {"ok": False, "fejl":
{"kode", "felt", "besked"}} — med samme indhold som de tidligere HTTP-endpoints. Intet gemmes
eller logges, og intet forlader browseren (Princip VII og XI).
"""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import date

from pensionskerne import UgyldigtInput, beregn as kerne_beregn, register

from .oversaet import til_husstand, til_kerne
from .pdfimport.aflaeser import AflaesningFejl, vaelg_aflaeser
from .pdfimport.omsaet import til_guide
from .visning import byg_visning, graenser

MAKS_PDF_BYTES = 25 * 1024 * 1024
# Den lokale parser (Princip XI). Oprettes først ved første PDF, så beregningen kan starte uden
# pdfplumber, pdfminer og cryptography, som browseren henter senere (research R005).
AFLAESER = None


def _satsaar() -> int:
    return max(register.satsaar())


def _ok(data) -> dict:
    return {"ok": True, "data": data}


def _fejl(kode: str, besked: str, felt: str | None = None) -> dict:
    return {"ok": False, "fejl": {"kode": kode, "felt": felt, "besked": besked}}


def forklaringer() -> dict:
    """Forklaringskataloget (feature 020): ord og pladsholdere, aldrig borgerens tal."""
    from .forklaring import katalog

    return katalog()


def kommuner() -> list[dict]:
    navne = register.kommunenavne(_satsaar())
    return sorted(({"noegle": k, "navn": v} for k, v in navne.items()), key=lambda k: k["navn"].casefold())


def _data(guide_json: str, idag: str) -> tuple[dict, date]:
    try:
        data = json.loads(guide_json)
    except ValueError:
        raise UgyldigtInput("body", "Forespørgslen kunne ikke læses") from None
    try:
        dato = date.fromisoformat(idag)
    except ValueError:
        raise UgyldigtInput("idag", "Ugyldig dato fra browseren") from None
    return data, dato


def _input(guide_json: str, idag: str):
    data, dato = _data(guide_json, idag)
    profil, antagelser = til_kerne(data)
    return profil, antagelser, dato


# Kernens feltnavne for partnerens profil → guidens felter (ordninger har unikke id'er i forvejen).
PARTNER_FELTER = {
    "foedselsdato": "person.partner.foedselsdato",
    "atp_aarlig": "person.partner.profil.atp_aarlig",
    "antagelser.folkepension_opsaettelse_aar": "person.partner.profil.folkepension_opsaettelse_aar",
    "loen.aarlig": "person.partner.profil.loen.aarlig",
    "loen.deltid_aarlig": "person.partner.profil.loen.deltid_aarlig",
    "loen.deltid_til_alder": "person.partner.profil.loen.deltid_til_alder",
}


def _husstand(data: dict, dato: date):
    """(profil_a, antagelser_a, profil_b, antagelser_b, husstand) for en fuld partner, ellers None."""
    from pensionskerne.husstand import beregn_husstand
    from pensionskerne.validering import valider

    hus = til_husstand(data)
    if hus is None:
        return None
    profil_a, antagelser_a, profil_b, antagelser_b = hus
    try:
        valider(profil_b, antagelser_b, _satsaar(), dato)
    except UgyldigtInput as e:
        raise UgyldigtInput(PARTNER_FELTER.get(e.felt, e.felt), e.besked) from None
    return profil_a, antagelser_a, profil_b, antagelser_b, beregn_husstand(
        profil_a, antagelser_a, profil_b, antagelser_b, _satsaar(), dato)


def _samlet(h, profil_a, profil_b, v_a: dict, v_b: dict) -> dict:
    """Parrets samlede oversigt pr. kalenderår (feature 012): hvert faste beløb og summen,
    netto pr. person og den samlede jævne udbetaling (kr./md., dagens kroner)."""
    def pr_aar(res):
        aar = {a.kalenderaar: a.netto_real / 12 for a in res.aar}
        fra = res.jaevn_fra_alder or res.aar[0].alder  # arbejdsår (017) er ikke et fast beløb
        jaevn = {a.kalenderaar: j.jaevn * a.realfaktor / 12 for j, a in zip(res.jaevn.aar, res.aar)
                 if a.alder >= fra} if res.jaevn else {}
        return aar, jaevn

    def formue(res, profil):
        foedt = profil.foedselsdato.year
        return {foedt + f.alder: (f.i_plan + f.uden_for_plan) * f.realfaktor for f in res.formue}

    netto_a, jaevn_a = pr_aar(h.a)
    netto_b, jaevn_b = pr_aar(h.b)
    alle = netto_a.keys() | netto_b.keys()
    kalenderaar = list(range(min(alle), max(alle) + 1))
    return {
        "maaned": v_a["hovedtal"]["maaned"] + v_b["hovedtal"]["maaned"],
        "dig": {"maaned": v_a["hovedtal"]["maaned"]},
        "partner": {"maaned": v_b["hovedtal"]["maaned"]},
        "kalenderaar": kalenderaar,
        "netto_dig": [netto_a.get(k, 0.0) for k in kalenderaar],
        "netto_partner": [netto_b.get(k, 0.0) for k in kalenderaar],
        "jaevn": [jaevn_a.get(k, 0.0) + jaevn_b.get(k, 0.0) for k in kalenderaar],
        "alder_dig": [k - profil_a.foedselsdato.year for k in kalenderaar],
        "alder_partner": [k - profil_b.foedselsdato.year for k in kalenderaar],
        "formue": _samlet_formue(formue(h.a, profil_a), formue(h.b, profil_b), v_a["formue"], v_b["formue"]),
    }


def _samlet_formue(a: dict[int, float], b: dict[int, float], v_a: dict | None, v_b: dict | None) -> dict | None:
    """Husstandens opsparing pr. kalenderår (dagens kroner, feature 013). Efter en persons sidste
    beregningsår tælles vedkommendes restformue med uændret."""
    if v_a is None and v_b is None:
        return None
    kalenderaar = list(range(min(a.keys() | b.keys()), max(a.keys() | b.keys()) + 1))

    def vaerdi(d, k):
        return d[k] if k in d else (d[max(d)] if d and k > max(d) else 0.0)

    return {"kalenderaar": kalenderaar, "i_alt": [vaerdi(a, k) + vaerdi(b, k) for k in kalenderaar],
            "rest": (v_a["rest"] if v_a else 0.0) + (v_b["rest"] if v_b else 0.0)}


def beregn(guide_json: str, idag: str) -> dict:
    try:
        data, dato = _data(guide_json, idag)
        hus = _husstand(data, dato)
        if hus is None:
            profil, antagelser = til_kerne(data)
            visning = byg_visning(kerne_beregn(profil, antagelser, _satsaar(), dato))
        else:
            profil, _, profil_b, _, h = hus
            visning = byg_visning(h.a)
    except UgyldigtInput as e:
        return _fejl("ugyldigt_input", e.besked, e.felt)
    visning["graenser"] = graenser(profil, _satsaar())
    if hus is not None:
        partner = byg_visning(h.b)
        partner["graenser"] = graenser(profil_b, _satsaar())
        visning["husstand"] = {"partner": partner, "samlet": _samlet(h, profil, profil_b, visning, partner)}
    return _ok(visning)


def stopalder(guide_json: str, idag: str, maaned: float) -> dict:
    """"Hvornår kan jeg stoppe?" (feature 017, US3): afprøver hver stopalder fra i dag til
    folkepensionsalderen med den nuværende plan og giver den tidligste, hvor det faste beløb
    (hovedtallet) når ønsket — ellers den bedste. Alle aldre afprøves (Princip V)."""
    from pensionskerne.register.opslag import Regelopslag
    from pensionskerne.regler.folkepension import folkepensionsalder

    try:
        data, dato = _data(guide_json, idag)
        profil, _ = til_kerne(data)
        if profil.loen is None or profil.loen.aarlig <= 0:
            raise UgyldigtInput("loen.aarlig", "Skriv din løn, så vi kan finde ud af, hvornår du kan stoppe")
        fra = dato.year - profil.foedselsdato.year
        til = folkepensionsalder(profil.foedselsdato, Regelopslag(_satsaar(), dato.year, 0.0))
        resultater = []
        for alder in range(fra, til + 1):
            data["person"]["loen"] = {**data["person"]["loen"], "stop_alder": alder}
            r = beregn(json.dumps(data), idag)
            if not r["ok"]:
                return r
            resultater.append({"alder": alder, "maaned": r["data"]["hovedtal"]["maaned"]})
    except UgyldigtInput as e:
        return _fejl("ugyldigt_input", e.besked, e.felt)
    tidligste = next((x for x in resultater if x["maaned"] >= maaned), None)
    bedste = max(resultater, key=lambda x: (x["maaned"], -x["alder"]))
    return _ok({"kunne": tidligste is not None, **(tidligste or {"alder": None, "maaned": None}),
                "bedste": bedste, "fra": fra, "til": til, "afproevet": len(resultater), "alle": resultater})


# Usikkerhed (feature 018): afkast og inflation afprøves hver for sig og sammen omkring borgerens
# eget valg, som i legacy (`generer_scenarier`). Spændene er antagelser, ikke lov. Ingen sats
# sættes under 0 (som legacy).
AFKAST_SPAEND = 0.01
INFLATION_SPAEND = 0.005
SCENARIER = (  # nøgle, titel, retning for afkast, retning for inflation
    ("lavere_afkast", "Lavere afkast", -1, 0),
    ("hoejere_afkast", "Højere afkast", 1, 0),
    ("hoejere_inflation", "Højere inflation", 0, 1),
    ("lavere_inflation", "Lavere inflation", 0, -1),
    ("ugunstigt", "Lavere afkast og højere inflation", -1, 1),
    ("gunstigt", "Højere afkast og lavere inflation", 1, -1),
)
# Levetid (feature 019): planen rækker kortere eller længere end livrentens horisont (90 år).
LEVETIDER = (85, 95)


def scenarier(guide_json: str) -> list[dict]:
    """De seks scenarier omkring borgerens antagelser (afkast og inflation som brøker)."""
    from pensionskerne import Antagelser

    a = json.loads(guide_json).get("antagelser") or {}
    standard = Antagelser()
    afkast = float(a.get("afkast_efter_pal", standard.afkast_efter_pal))
    inflation = float(a.get("inflation", standard.inflation))
    return [{"noegle": noegle, "titel": titel,
             "afkast": round(max(0.0, afkast + ra * AFKAST_SPAEND), 6),
             "inflation": round(max(0.0, inflation + ri * INFLATION_SPAEND), 6), "plan_slut_alder": None}
            for noegle, titel, ra, ri in SCENARIER] + [
        {"noegle": f"levetid_{alder}", "titel": f"Planen rækker til {alder} år", "afkast": afkast,
         "inflation": inflation, "plan_slut_alder": alder}
        for alder in LEVETIDER]


def scenarie(guide_json: str, idag: str, afkast: float, inflation: float, plan_slut_alder: int | None = None) -> dict:
    """Hovedtallet med ændret afkast og inflation — præcis som `beregn` (feature 018). For et par
    også partnerens og jeres samlede. Med en planhorisont længere end den normale (019) også
    indkomsten i året efter den normale plans slutning (`efter_plan`, kr./md., dagens kroner)."""
    from pensionskerne import Antagelser

    data = json.loads(guide_json)
    data["antagelser"] = {**(data.get("antagelser") or {}), "afkast_efter_pal": afkast, "inflation": inflation,
                          "plan_slut_alder": plan_slut_alder}
    r = beregn(json.dumps(data), idag)
    if not r["ok"]:
        return r
    v = r["data"]
    h = v.get("husstand")
    svar = {"dig": v["hovedtal"]["maaned"],
            "partner": h["partner"]["hovedtal"]["maaned"] if h else None,
            "samlet": h["samlet"]["maaned"] if h else None}
    normal_slut = Antagelser().livsvarig_horisont_alder
    if plan_slut_alder is not None and plan_slut_alder > normal_slut:
        def efter(visning):
            raekke = next((a for a in visning["aar"] if a["alder"] == normal_slut + 1), None)
            return round(raekke["netto_real"] / 12, -2) if raekke else None
        svar["efter_plan"] = {"dig": efter(v), "partner": efter(h["partner"]) if h else None}
    return _ok(svar)


def optimer(guide_json: str, idag: str, fremdrift=None, hvem: str = "dig") -> dict:
    """Find bedste plan (feature 007). Beløb er det faste beløb hele perioden (kr./md., dagens
    kroner), afrundet som hovedtallet. `plan` er forslaget — eller den nuværende plan, hvis
    intet er bedre. For et par optimeres én person ad gangen (`hvem`), mens den andens plan
    holdes fast og indgår som partner (feature 012)."""
    from pensionskerne.husstand import partner_fra
    from pensionskerne.optimering import optimer as kerne_optimer

    try:
        data, dato = _data(guide_json, idag)
        hus = _husstand(data, dato)
        if hus is None:
            profil, antagelser = til_kerne(data)
        else:
            profil_a, antagelser_a, profil_b, antagelser_b, h = hus
            if hvem == "partner":
                profil, antagelser = replace(profil_b, partner=partner_fra(h.a, profil_a, antagelser_a)), antagelser_b
            else:
                profil, antagelser = replace(profil_a, partner=partner_fra(h.b, profil_b, antagelser_b)), antagelser_a
        r = kerne_optimer(profil, antagelser, _satsaar(), dato, fremdrift=fremdrift)
    except UgyldigtInput as e:
        return _fejl("ugyldigt_input", e.besked, e.felt)
    foer = int(round(r.udgangspunkt_maaned, -2))
    efter = int(round(r.bedste_maaned, -2)) if r.bedste else foer
    forbedret = efter > foer  # en forbedring, der forsvinder i afrundingen, er ingen forbedring for borgeren
    plan = r.bedste if forbedret else r.udgangspunkt
    aendringer = []
    if forbedret:
        for oid, til in plan.starter.items():
            if til != r.udgangspunkt.starter[oid]:
                aendringer.append({"id": oid, "felt": "start", "fra": r.udgangspunkt.starter[oid], "til": til})
            if oid in plan.varighed and plan.varighed[oid] != r.udgangspunkt.varighed[oid]:
                aendringer.append({"id": oid, "felt": "varighed", "fra": r.udgangspunkt.varighed[oid], "til": plan.varighed[oid]})
        for oid, til in plan.form.items():
            fra = r.udgangspunkt.form.get(oid)
            if til != fra:
                aendringer.append({"id": oid, "felt": "form", "fra": {"form": fra[0], "aar": fra[1]},
                                   "til": {"form": til[0], "aar": til[1]}})
        if plan.opsaettelse != r.udgangspunkt.opsaettelse:
            aendringer.append({"id": "folkepension", "felt": "opsaettelse", "fra": r.udgangspunkt.opsaettelse, "til": plan.opsaettelse})
    ordninger = {oid: {"udbetaling_start_alder": start} for oid, start in plan.starter.items()}
    for oid, aar in plan.varighed.items():
        ordninger.setdefault(oid, {})["udbetaling_aar"] = aar
    for oid, (form, aar) in plan.form.items():
        ordninger.setdefault(oid, {}).update({"udbetalingsform": form, "udbetaling_aar": aar})
    return _ok({
        "forbedret": forbedret, "foer": foer, "efter": efter if forbedret else foer,
        "aendringer": aendringer,
        "plan": {"ordninger": ordninger, "folkepension_opsaettelse_aar": plan.opsaettelse},
        "evalueret": r.evalueret, "mulige": r.mulige, "udtoemmende": r.udtoemmende,
    })


def pdf(data: bytes) -> dict:
    """Aflæser en PensionsInfo-rapport lokalt til guidedata."""
    global AFLAESER
    from .pdfimport.tekst import PdfFejl, foedselsdato_fra_rapport, udtraek_forside

    if len(data) > MAKS_PDF_BYTES:
        return _fejl("for_stor", f"Filen er for stor. Den må højst fylde {MAKS_PDF_BYTES // 1024 // 1024} MB.")
    try:
        forside = udtraek_forside(data)
    except PdfFejl as e:
        return _fejl(e.kode, e.besked)
    try:
        AFLAESER = AFLAESER or vaelg_aflaeser()
        aflaesning = AFLAESER.aflaes(data)
    except AflaesningFejl as e:
        return _fejl(e.kode, f"{e.besked} Du kan i stedet indtaste dine oplysninger selv.")
    return _ok(til_guide(aflaesning, foedselsdato_fra_rapport(forside), _satsaar()))
