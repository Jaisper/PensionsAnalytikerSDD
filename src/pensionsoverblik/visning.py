"""Fremskrivning → visningsmodel (data-model.md).

Ren omformatering (FR-001): grupperer kernens kilder i kort, summerer, dividerer årsbeløb
med 12 og ganger med kernens `realfaktor`. Ingen skat, ydelser eller satser beregnes her.
"""
from __future__ import annotations

from dataclasses import asdict

from pensionskerne import Fremskrivning, register

from .katalog import ADVARSLER, DELAAR_FOERST, ENGANGSKORT, KILDE_TITLER, KORT, KORT_FOR_KILDETYPE, UKENDT_ADVARSEL

MAANEDER = 12
# Grafens og tidslinjens akse starter ved en fast alder (eller borgerens alder, hvis den er højere),
# så aksen ikke hopper, når en ordning trækkes tidligere. 60 år er den tidligste
# pensionsudbetalingsalder for ordninger i dag. Ren præsentation.
AKSE_START_ALDER = 60
BUFFER_NUL_KR = 1.0
# "Dit år" (020) nævner årsagen til en ændring fra året før, når en kilde ændrer sig mindst så
# meget (kr./md., dagens kroner). Ren præsentation.
AENDRING_TAERSKEL_MAANED = 100
DRIVERE = 3  # hovedtallets forklaring nævner de største kilder


def _advarsel(a) -> dict:
    info = ADVARSLER.get(a.kode, UKENDT_ADVARSEL)
    return {"kode": a.kode, "titel": info["titel"], "ikon": info["ikon"], "besked": a.besked,
            "aldre": list(a.aldre) if a.aldre else None}


def _hovedtal(res: Fremskrivning) -> dict:
    if res.jaevn:
        # Hovedtallet er det faste beløb hele perioden: det laveste jævne beløb (feature 008) — det
        # samme, som "Find bedste plan" bruger. Niveauet stiger kun, når et engangsbeløb lander
        # (det lånes ikke på forhånd); et senere spring oplyses som "senere". Med løn tæller kun
        # årene fra stopalderen (017).
        fra = res.jaevn_fra_alder or res.aar[0].alder
        par = [(j, a) for j, a in zip(res.jaevn.aar, res.aar) if a.alder >= fra]
        real = [j.jaevn * a.realfaktor / MAANEDER for j, a in par]
        ref = max([0] + [i for i in range(1, len(real)) if real[i] > real[i - 1] + 1])
        senere = {"maaned": round(real[ref], -2), "fra_alder": par[ref][1].alder} if ref else None
        return {"type": "jaevn", "maaned": round(min(real), -2), "fra_alder": fra, "senere": senere}
    foerste_hele = next((a for a in res.aar if a.alder > res.folkepensionsalder), res.aar[-1])
    return {"type": "foerste_fp_aar", "maaned": round(foerste_hele.netto_real / MAANEDER, -2),
            "fra_alder": foerste_hele.alder, "senere": None}


def _loen(res: Fremskrivning, hovedtal: dict) -> dict | None:
    """Lønnen efter skat og pensionsindbetaling pr. måned i dagens kroner, til sammenligning med
    hovedtallet (017b): gennemsnittet af lønkildens netto i årene før stopalderen."""
    til = res.jaevn_fra_alder
    netto = [k.netto * a.realfaktor for a in res.aar if til is not None and a.alder < til
             for k in a.kilder if k.type == "loen"]
    if not netto:
        return None
    maaned = round(sum(netto) / len(netto) / MAANEDER, -2)
    return {"maaned": maaned, "til_alder": til,
            "andel_pct": round(100 * hovedtal["maaned"] / maaned) if maaned > 0 else None}


def _formue(res: Fremskrivning) -> dict | None:
    """Opsparingen uden for pension år for år fra i dag, i dagens kroner (feature 013, US4).
    Restformuen er opsparingen ved udgangen af beregningens sidste år."""
    if not any(f.i_plan + f.uden_for_plan >= BUFFER_NUL_KR for f in res.formue):
        return None
    i_plan = [0.0 if (x := f.i_plan * f.realfaktor) < BUFFER_NUL_KR else x for f in res.formue]
    uden = [f.uden_for_plan * f.realfaktor for f in res.formue]
    return {"aldre": [f.alder for f in res.formue], "i_plan": i_plan, "uden_for_plan": uden,
            "realfaktor": [f.realfaktor for f in res.formue],
            "rest": i_plan[-1] + uden[-1], "rest_alder": res.formue[-1].alder}


def _forenklinger(res: Fremskrivning) -> list[dict]:
    """Forenklingerne fra registret (feature 020): de markerede, der er brugt i beregningen, først,
    derefter dem, der altid gælder."""
    brugt = {f.removeprefix("forenkling:") for a in res.aar for f in a.flag if f.startswith("forenkling:")}
    poster = [{**asdict(f), "anvendt": f.id in brugt} for f in register.forenklinger()
              if f.omfang == "altid" or f.id in brugt]
    return sorted(poster, key=lambda f: not f["anvendt"])


def _satser(res: Fremskrivning) -> list[dict]:
    satser = []
    kommuner = register.kommuneregister(res.satsaar)
    for id in res.sporing_samlet:
        if id.startswith(("kommune.", "kirkeskat.")):
            noegle = id.split(".", 1)[1]
            tabel = kommuner.satser if id.startswith("kommune.") else kommuner.kirkeskat
            satser.append({"id": id, "vaerdi": tabel[noegle], "enhed": "brok",
                           "kilde": kommuner.kilde, "status": kommuner.status})
        elif not id.startswith("antagelse."):
            p = register.post(res.satsaar, id)
            satser.append({"id": p.id, "vaerdi": p.vaerdi if p.enhed != "tabel" else None, "enhed": p.enhed,
                           "kilde": p.kilde, "status": p.status})
    return satser


def byg_visning(res: Fremskrivning) -> dict:
    aldre = [a.alder for a in res.aar]
    serier = {noegle: [0.0] * len(res.aar) for noegle in KORT}
    detaljer: dict[str, list[dict]] = {noegle: [] for noegle in KORT}
    for i, a in enumerate(res.aar):
        pr_kort: dict[str, dict[str, float]] = {}
        for k in a.kilder:
            noegle = KORT_FOR_KILDETYPE[k.type]
            serier[noegle][i] += k.netto * a.realfaktor / MAANEDER
            sum_ = pr_kort.setdefault(noegle, {"brutto": 0.0, "skat": 0.0, "netto": 0.0})
            sum_["brutto"] += k.brutto
            sum_["skat"] += k.skat
            sum_["netto"] += k.netto
        for noegle, sum_ in pr_kort.items():
            detaljer[noegle].append({"alder": a.alder, **sum_})

    hovedtal_advarsler, generelle, markeringer = [], [], []
    kort_advarsler: dict[str, list[dict]] = {noegle: [] for noegle in KORT}
    for a in res.advarsler:
        placering = ADVARSLER.get(a.kode, UKENDT_ADVARSEL)["placering"]
        if placering == "hovedtal":
            hovedtal_advarsler.append(_advarsel(a))
        elif placering == "graf":
            if a.aldre:
                markeringer.append({"fra": a.aldre[0], "til": a.aldre[1], "kode": a.kode,
                                    "titel": ADVARSLER[a.kode]["titel"]})
            generelle.append(_advarsel(a))
        elif placering in KORT and detaljer[placering]:
            kort_advarsler[placering].append(_advarsel(a))
        else:
            generelle.append(_advarsel(a))

    kort = []
    for noegle, info in KORT.items():
        vaerdier = serier[noegle]
        med_vaerdi = [i for i, x in enumerate(vaerdier) if x > 0]
        if not med_vaerdi:
            continue
        repr_i = med_vaerdi[1] if noegle in DELAAR_FOERST and len(med_vaerdi) > 1 else med_vaerdi[0]
        kort.append({
            "noegle": noegle, **info,
            "netto_maaned": vaerdier[repr_i], "repraesentativ_alder": aldre[repr_i],
            "fra_alder": aldre[med_vaerdi[0]], "til_alder": aldre[med_vaerdi[-1]],
            "advarsler": kort_advarsler[noegle], "detaljer": detaljer[noegle],
        })

    realfaktor = {a.alder: a.realfaktor for a in res.aar}
    engangs = [{"ordning_id": e.ordning_id, "type": e.type, "alder": e.alder, "i_buffer": e.i_buffer,
                "netto": e.netto, "netto_real": e.netto * realfaktor[e.alder]} for e in res.engangsbeloeb]
    if engangs:
        # Summen pr. ordning (portioner og flere engangsbeløb samlet); de enkelte udbetalinger ligger i
        # `engangs` til "Se år for år".
        pr_ordning: dict[str, dict] = {}
        for e in engangs:
            o = pr_ordning.setdefault(e["ordning_id"], {"ordning_id": e["ordning_id"], "type": e["type"], "netto": 0.0,
                                                        "netto_real": 0.0, "fra_alder": e["alder"], "til_alder": e["alder"],
                                                        "antal": 0, "i_buffer": e["i_buffer"]})
            o["netto"] += e["netto"]
            o["netto_real"] += e["netto_real"]
            o["til_alder"] = e["alder"]
            o["antal"] += 1
        kort.append({"noegle": "engangsbeloeb", **ENGANGSKORT, "netto_maaned": None, "repraesentativ_alder": None,
                     "fra_alder": engangs[0]["alder"], "til_alder": engangs[-1]["alder"],
                     "advarsler": [], "detaljer": [], "engangs": engangs, "pr_ordning": list(pr_ordning.values())})

    jaevn = buffer = fra_buffer = til_side = buffer_ind = None
    if res.jaevn:
        fra = res.jaevn_fra_alder or res.aar[0].alder  # arbejdsår (017) har ingen jævn linje
        jaevn = [j.jaevn * a.realfaktor / MAANEDER if a.alder >= fra else None for j, a in zip(res.jaevn.aar, res.aar)]
        # Bufferen i dagens kroner. Den ender i 0; under 1 kr. er regnestøj (007 R002).
        buffer = [0.0 if abs(b := j.buffer_rest * a.realfaktor) < BUFFER_NUL_KR else b
                  for j, a in zip(res.jaevn.aar, res.aar)]
        # Feature 027: bufferen i søjlerne, pr. måned i dagens kroner. Over linjen ligger det, der
        # sættes til side, og det, udjævningen ikke fordeler (skat af opsparingen og indskud, 013b).
        fra_buffer = [j.fra_buffer * a.realfaktor / MAANEDER if x is not None else None
                      for j, a, x in zip(res.jaevn.aar, res.aar, jaevn)]
        # Feature 029: det, der kommer ind i bufferen (engangsbeløb og opsparing), pr. år i dagens kroner.
        buffer_ind = [j.ind_buffer * a.realfaktor for j, a in zip(res.jaevn.aar, res.aar)]
        til_side = [{"buffer": j.til_buffer * a.realfaktor / MAANEDER, "skat": a.skat_opsparing * a.realfaktor / MAANEDER,
                     "indskud": a.indskud_opsparing * a.realfaktor / MAANEDER} if x is not None else None
                    for j, a, x in zip(res.jaevn.aar, res.aar, jaevn)]

    alder_nu = res.beregningsdato.year - (res.aar[0].kalenderaar - res.aar[0].alder)
    akse_start = min(aldre[0], max(AKSE_START_ALDER, alder_nu))
    foran = aldre[0] - akse_start  # tomme år foran den første udbetaling

    # Forklaringer (020): årsagen til årets største ændring og hovedtallets største kilder.
    def aendring(i: int) -> dict | None:
        if i == 0:
            return None
        forskel = {n: serier[n][i] - serier[n][i - 1] for n in KORT}
        n = max(forskel, key=lambda k: abs(forskel[k]))
        if abs(forskel[n]) < AENDRING_TAERSKEL_MAANED:
            return None
        return {"noegle": n, "titel": KORT[n]["titel"], "maaned": forskel[n]}

    hovedtal = _hovedtal(res)
    fra = res.jaevn_fra_alder or res.aar[0].alder
    i_fra = aldre.index(fra) if fra in aldre else 0
    # De største kilder i perioden med det faste beløb: gennemsnit pr. måned i dagens kroner, afrundet
    # til hele kroner (sum() kan afvige i sidste decimal mellem Python-versioner, SC-006).
    periode = len(aldre) - i_fra
    drivere = sorted(({"noegle": n, "titel": KORT[n]["titel"], "maaned": round(sum(serier[n][i_fra:]) / periode)} for n in KORT
                      if sum(serier[n][i_fra:]) > 0), key=lambda d: -d["maaned"])[:DRIVERE]
    hovedtal["forklaring"] = {"drivere": drivere, "iterationer": res.buffer_iterationer}
    jaevn_aar = {j.alder: j for j in res.jaevn.aar} if res.jaevn else {}

    return {
        "hovedtal": hovedtal,
        "hovedtal_advarsler": hovedtal_advarsler,
        "loen": _loen(res, hovedtal),
        "folkepensionsalder": res.folkepensionsalder,
        "kort": kort,
        "graf": {
            "aldre": list(range(akse_start, aldre[0])) + aldre,
            "serier": [{"noegle": n, "titel": KORT[n]["titel"], "farve": KORT[n]["farve"],
                        "vaerdier": [0.0] * foran + serier[n]} for n in KORT if any(serier[n])],
            "markeringer": markeringer,
            "jaevn": None if jaevn is None else [None] * foran + jaevn,
            "buffer": None if buffer is None else [None] * foran + buffer,
            "fra_buffer": None if fra_buffer is None else [None] * foran + fra_buffer,
            "til_side": None if til_side is None else [None] * foran + til_side,
            "buffer_ind": None if buffer_ind is None else [None] * foran + buffer_ind,
            # Skat af opsparing uden for pension (009, 013b): kapitalindkomst, aktieindkomst og ASK.
            "skat_buffer": [None] * foran + [a.skat_opsparing * a.realfaktor / MAANEDER for a in res.aar]
            if any(a.skat_opsparing for a in res.aar) else None,
            "engangs": engangs,
            # Til skifteren mellem dagens og årets kroner (020b); 1 for årene foran første række.
            "realfaktor": [1.0] * foran + [a.realfaktor for a in res.aar],
        },
        "formue": _formue(res),
        "forenklinger": _forenklinger(res),
        "generelle_advarsler": generelle,
        "antagelser": {**asdict(res.antagelser), "satsregulering": res.antagelser.effektiv_satsregulering,
                       "traekraekkefoelge": list(res.antagelser.traekraekkefoelge)},  # JSON-form (013b)
        "aar": [{
            "alder": a.alder, "kalenderaar": a.kalenderaar, "personlig_indkomst": a.personlig_indkomst,
            "skat": a.skat_i_alt, "netto": a.netto_i_alt, "netto_real": a.netto_real,
            "indtaegtsgrundlag": a.indtaegtsgrundlag, "tillaegsprocent": a.tillaegsprocent,
            "engangsbeloeb": a.engangsbeloeb_netto,
            "kapitalindkomst": a.kapitalindkomst, "skat_kapitalindkomst": a.skat_kapitalindkomst,
            "aktieindkomst": a.aktieindkomst, "skat_aktieindkomst": a.skat_aktieindkomst,  # 013b
            "skat_aktiesparekonto": a.skat_aktiesparekonto, "indskud_opsparing": a.indskud_opsparing,
            # Til "Dit år" (020)
            "realfaktor": a.realfaktor,
            "kilder": [{"id": k.kilde_id, "type": k.type, "titel": KILDE_TITLER[k.type],
                        "brutto": k.brutto, "skat": k.skat, "netto": k.netto} for k in a.kilder],
            "detaljer": asdict(a.detaljer) if a.detaljer else None,
            "jaevn": jaevn_aar[a.alder].jaevn if a.alder in jaevn_aar else None,
            "til_opsparing": jaevn_aar[a.alder].til_buffer if a.alder in jaevn_aar else 0.0,
            "fra_opsparing": jaevn_aar[a.alder].fra_buffer if a.alder in jaevn_aar else 0.0,
            "aendring": aendring(i),
            "sporing": list(a.sporing),
        } for i, a in enumerate(res.aar)],
        "satser": _satser(res),
    }


def graenser(profil, satsaar: int) -> dict:
    """Grænser til tidslinjens skydere — fra kernens regler og registret (Princip II).

    Tidligste lovlige alder pr. ordning (oplyst af selskabet eller udledt efter loven),
    ratepensionens periode og maksimal opsættelse af folkepensionen.
    """
    from pensionskerne.register.opslag import Regelopslag
    from pensionskerne.regler.folkepension import folkepensionsalder
    from pensionskerne.regler.udbetalingsalder import tidligste_udbetalingsalder

    o = Regelopslag(satsaar, satsaar, 0.0)
    fp_alder = folkepensionsalder(profil.foedselsdato, o)
    ordninger = {}
    import math

    for ordning in profil.ordninger:
        if ordning.tidligste_udbetalingsalder is not None:
            ordninger[ordning.id] = {"tidligste": ordning.tidligste_udbetalingsalder, "oplyst": True}
        else:
            alder, _ = tidligste_udbetalingsalder(profil.foedselsdato, ordning.oprettet, fp_alder, o)
            ordninger[ordning.id] = {"tidligste": alder, "oplyst": False}
        if ordning.type == "kapitalpension":
            # Feature 009: seneste udbetaling (PBL § 25, stk. 1, nr. 7) og om omlægning er mulig (§ 41).
            ordninger[ordning.id]["seneste"] = math.ceil(ordninger[ordning.id]["tidligste"]) + \
                o.v("ordning.kapitalpension.seneste_aar_efter_udbetalingsalder")
            ordninger[ordning.id]["kan_omlaegges"] = not ordning.afgift_betalt
    return {
        "folkepensionsalder": fp_alder,
        "ordninger": ordninger,
        "ratepension_aar": {"min": o.v("ordning.ratepension.min_aar"),
                            "maks": o.v("ordning.ratepension.maks_aar_efter_udbetalingsalder")},
        "opsaettelse_maks": o.v("opsat.maks_aar"),
    }
