"""Fremskrivning → visningsmodel (data-model.md).

Ren omformatering (FR-001): grupperer kernens kilder i kort, summerer, dividerer årsbeløb
med 12 og ganger med kernens `realfaktor`. Ingen skat, ydelser eller satser beregnes her.
"""
from __future__ import annotations

from dataclasses import asdict

from pensionskerne import Fremskrivning, register

from .katalog import ADVARSLER, DELAAR_FOERST, ENGANGSKORT, KORT, KORT_FOR_KILDETYPE, UKENDT_ADVARSEL

MAANEDER = 12


def _advarsel(a) -> dict:
    info = ADVARSLER.get(a.kode, UKENDT_ADVARSEL)
    return {"kode": a.kode, "titel": info["titel"], "ikon": info["ikon"], "besked": a.besked,
            "aldre": list(a.aldre) if a.aldre else None}


def _hovedtal(res: Fremskrivning) -> dict:
    if res.jaevn:
        # Det jævne niveau stiger kun, når et engangsbeløb lander (det lånes ikke på forhånd).
        # Hovedtallet er niveauet efter det sidste skridt — det gælder i de fleste år.
        real = [j.jaevn * a.realfaktor / MAANEDER for j, a in zip(res.jaevn.aar, res.aar)]
        ref = max([0] + [i for i in range(1, len(real)) if real[i] > real[i - 1] + 1])
        foer = {"maaned": round(real[0], -2), "fra_alder": res.aar[0].alder} if ref else None
        return {"type": "jaevn", "maaned": round(real[ref], -2), "fra_alder": res.aar[ref].alder, "foer": foer}
    foerste_hele = next((a for a in res.aar if a.alder > res.folkepensionsalder), res.aar[-1])
    return {"type": "foerste_fp_aar", "maaned": round(foerste_hele.netto_real / MAANEDER, -2),
            "fra_alder": foerste_hele.alder, "foer": None}


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

    engangs = [{"alder": a.alder, "netto": a.engangsbeloeb_netto, "netto_real": a.engangsbeloeb_netto * a.realfaktor}
               for a in res.aar if a.engangsbeloeb_netto > 0]
    if engangs:
        kort.append({"noegle": "engangsbeloeb", **ENGANGSKORT, "netto_maaned": None, "repraesentativ_alder": None,
                     "fra_alder": engangs[0]["alder"], "til_alder": engangs[-1]["alder"],
                     "advarsler": [], "detaljer": [], "engangs": engangs})

    jaevn = None
    if res.jaevn:
        jaevn = [j.jaevn * a.realfaktor / MAANEDER for j, a in zip(res.jaevn.aar, res.aar)]

    return {
        "hovedtal": _hovedtal(res),
        "hovedtal_advarsler": hovedtal_advarsler,
        "folkepensionsalder": res.folkepensionsalder,
        "kort": kort,
        "graf": {
            "aldre": aldre,
            "serier": [{"noegle": n, "titel": KORT[n]["titel"], "farve": KORT[n]["farve"], "vaerdier": serier[n]}
                       for n in KORT if any(serier[n])],
            "markeringer": markeringer,
            "jaevn": jaevn,
        },
        "generelle_advarsler": generelle,
        "antagelser": {**asdict(res.antagelser), "satsregulering": res.antagelser.effektiv_satsregulering},
        "aar": [{
            "alder": a.alder, "kalenderaar": a.kalenderaar, "personlig_indkomst": a.personlig_indkomst,
            "skat": a.skat_i_alt, "netto": a.netto_i_alt, "netto_real": a.netto_real,
            "indtaegtsgrundlag": a.indtaegtsgrundlag, "tillaegsprocent": a.tillaegsprocent,
            "engangsbeloeb": a.engangsbeloeb_netto,
        } for a in res.aar],
        "satser": _satser(res),
    }
