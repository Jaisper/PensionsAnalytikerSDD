"""Forsikringerne i en PensionsInfo-rapport (feature 031): død, tab af arbejdsevne, kritisk sygdom og
sundhed. Lokal og deterministisk som resten af parseren (Princip XI).

Hvert afsnit har en "Overblik"-side med en tabel og en "Detaljer"-side med bemærkninger (layoutet er
udledt af PensionsInfos demorapport, 2026):

- Tabellen: en række begynder med skattekoden (A, F eller S) til venstre for selskabet. Derefter
  følger aftalenumret og evt. en bemærkning ("Dækker indtil 80 år"). Beløbene er højrestillede under
  kolonneoverskrifterne. Grupperne (modtager ved død, form ellers) står lidt til venstre for rækkerne.
- Detaljerne: selskabet i venstre kolonne, bemærkningerne til højre ("Dækningen ophører ved 68 år",
  "tegnet med ret til præmiefritagelse").
- Sundhedsforsikringen har kun detaljer: selskab, aftalenr. og "Dækningsbeløb – op til".

Et afsnit, der ikke kan læses, giver en bemærkning og ingen dækninger. Det stopper aldrig importen.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .aflaeser import AflaestDaekning, Periode

# Indholdsfortegnelsens titler (afsnittets første side).
AFSNIT = {
    "doed": re.compile(r"Udbetaling(?:er)? ved død"),
    "erhvervsevne": re.compile(r"Udbetaling ved (?:tabt|tab af) arbejdsevne"),
    "kritisk_sygdom": re.compile(r"Visse kritiske sygdomme"),
    "sundhed": re.compile(r"Sundhedsforsikring"),
}
AFSNIT_NAVN = {"doed": "Udbetaling ved død", "erhvervsevne": "Udbetaling ved tab af arbejdsevne",
               "kritisk_sygdom": "Visse kritiske sygdomme", "sundhed": "Sundhedsforsikring"}
FORMER = {"På én gang": "engang", "Om året i en årrække": "aarraekke", "Om året, så længe du lever": "livsvarig"}
SKATTEKODER = ("A", "F", "S")
AFTALENR = re.compile(r"^\d[\d\s-]*\d$")
BELOEB = re.compile(r"^(\d{1,3}(?:\.\d{3})*)(kr\.)?$")
DAEKKER_INDTIL = re.compile(r"Dækker indtil (\d+) år")
OPHOERER = re.compile(r"Dækningen ophører ved (\d+) år")
OPHOERER_SENEST = re.compile(r"ophører senest ved (\d+) år")
INDTIL_KOLONNE = re.compile(r"Indtil (\d+) år")
BOERN_UNDER = re.compile(r"Udbetales, hvis under (\d+) år")
# Bemærkninger, der vises ved dækningen. Resten (fx "Yderligere oplysninger hos ...") er standardtekst.
NOTER = [
    (re.compile(r"nedtrappes"), "Dækningsbeløbet nedtrappes."),
    (re.compile(r"procentdel af din løn"), "Dækningen er en procentdel af din løn, så beløbet følger lønnen."),
    (re.compile(r"indtil pensionen er udbetalt"), "Dækker, indtil pensionen er udbetalt."),
]

# Kolonner (x i punkter, liggende A4): skattekoden står ved x ≈ 87–91, rækkernes tekst fra x ≈ 99,
# beløbene til højre for midten. Forklaringen nederst ("A Afgiftspligtig") står ved x = 60.
KODE_X = (80, 97)
BELOEB_X = 500
DETALJE_X = 300


def _linjer(ord_: list[dict], tolerance: float = 3.5) -> list[list[dict]]:
    """Ord samlet i linjer efter lodret placering. Skattekoden står 1–2 pt under selskabet."""
    linjer: list[list[dict]] = []
    for w in sorted(ord_, key=lambda w: (w["top"], w["x0"])):
        if linjer and w["top"] - linjer[-1][0]["top"] <= tolerance:
            linjer[-1].append(w)
        else:
            linjer.append([w])
    return [sorted(l, key=lambda w: w["x0"]) for l in linjer]


def _tekst(ord_: list[dict]) -> str:
    return " ".join(w["text"] for w in ord_)


def _beloeb(ord_: list[dict]) -> list[tuple[int, float]]:
    """(beløb, højre kant) for '75.000 kr.' eller '75.000kr.'."""
    ud = []
    for i, w in enumerate(ord_):
        if m := BELOEB.match(w["text"]):
            if m.group(2):
                ud.append((int(m.group(1).replace(".", "")), w["x1"]))
            elif i + 1 < len(ord_) and ord_[i + 1]["text"] == "kr.":
                ud.append((int(m.group(1).replace(".", "")), ord_[i + 1]["x1"]))
    return ud


def _kolonner(ord_: list[dict]) -> list[tuple[str, float]]:
    """Kolonneoverskrifter til højre (fx 'Mistet arbejdsevne', 'Indtil 68 år') med højre kant."""
    grupper: list[list[dict]] = []
    for w in sorted(ord_, key=lambda w: w["x0"]):
        if grupper and w["x0"] - grupper[-1][-1]["x1"] < 6:
            grupper[-1].append(w)
        else:
            grupper.append([w])
    return [(_tekst(g), g[-1]["x1"]) for g in grupper]


def _noter(tekst: str) -> list[str]:
    noter = [note for m, note in NOTER if m.search(tekst)]
    if b := BOERN_UNDER.search(tekst):
        noter.append(f"Udbetales til børn under {b.group(1)} år.")
    return noter


def _praemiefritagelse(tekst: str) -> bool | None:
    if "ikke tegnet med ret til præmiefritagelse" in tekst:
        return False
    if "tegnet med ret til præmiefritagelse" in tekst:
        return True
    return None


def _sidehoved(ord_: list[dict]) -> tuple[str, str]:
    """(titel, undertitel), fx ('Udbetaling ved død - børn (4 | 5)', 'Hvis du har børn ...')."""
    titel = _tekst([w for w in ord_ if w["top"] < 42])
    under = _tekst([w for w in ord_ if 42 <= w["top"] < 58])
    return titel, under


@dataclass
class _Raekke:
    daekning: AflaestDaekning
    tekst: str = ""
    detaljer: list[str] = field(default_factory=list)


def _tabel(ord_: list[dict], type_: str) -> list[_Raekke]:
    """Rækkerne i en oversigtstabel (død, tab af arbejdsevne, kritisk sygdom)."""
    linjer = [l for l in _linjer(ord_) if l[0]["top"] > 58]
    def kode(l):  # skattekoden i rækkens venstre side
        return next((w for w in l if w["text"] in SKATTEKODER and KODE_X[0] <= w["x0"] < KODE_X[1]), None)
    def gruppe(l):
        venstre = [w for w in l if w["x0"] < BELOEB_X]
        hoejre = [w for w in l if w["x0"] >= BELOEB_X]
        overskrift = hoejre and not _beloeb(hoejre)  # "Pensioner | Mistet arbejdsevne | Indtil 68 år"
        return (venstre and KODE_X[0] <= venstre[0]["x0"] < KODE_X[1] and not kode(l) and not overskrift
                and not _tekst(venstre).startswith("I alt"))
    foerste = next((i for i, l in enumerate(linjer) if kode(l) or gruppe(l)), None)
    if foerste is None or not any(kode(l) for l in linjer):
        return []
    # Kolonneoverskrifterne står over første gruppe eller række (ingen hos kritisk sygdom).
    overskrift = [w for l in linjer[:foerste] for w in l if w["x0"] >= BELOEB_X and not _beloeb([w])]
    kolonner = _kolonner(overskrift)
    raekker: list[_Raekke] = []
    gruppenavn = None
    aktuel: _Raekke | None = None
    for l in linjer[foerste:]:
        venstre = [w for w in l if w["x0"] < BELOEB_X]
        if _tekst(venstre).startswith("I alt") or venstre and venstre[0]["x0"] < KODE_X[0]:
            aktuel = None  # "I alt" og forklaringen nederst
            continue
        if gruppe(l):
            gruppenavn, aktuel = _tekst(venstre), None
            continue
        if k := kode(l):
            selskab = _tekst([w for w in venstre if w is not k])
            aktuel = _Raekke(AflaestDaekning(type=type_, selskab=selskab, aftalenr=None, skat=k["text"],
                                             modtager=None if gruppenavn in FORMER else gruppenavn,
                                             form=FORMER.get(gruppenavn), beloeb=None, kolonner=[]))
            raekker.append(aktuel)
        elif aktuel is None:
            continue
        else:
            linje = _tekst(venstre)
            if AFTALENR.match(linje) and aktuel.daekning.aftalenr is None:
                aktuel.daekning.aftalenr = re.sub(r"\s+", "", linje)
            elif linje:
                aktuel.tekst = f"{aktuel.tekst} {linje}".strip()
        for beloeb, x1 in _beloeb([w for w in l if w["x0"] >= BELOEB_X]):
            etiket = min(kolonner, key=lambda k: abs(k[1] - x1))[0] if kolonner else gruppenavn or ""
            aktuel.daekning.kolonner.append(Periode(etiket=etiket, aarligt_beloeb=beloeb))
    for r in raekker:
        d = r.daekning
        betalt = [k for k in d.kolonner if k.aarligt_beloeb]
        d.beloeb = (betalt or d.kolonner or [Periode("", None)])[0].aarligt_beloeb
        if d.form is None and betalt:
            d.form = FORMER.get(betalt[0].etiket)
        if m := DAEKKER_INDTIL.search(r.tekst):
            d.til_alder = int(m.group(1))
        elif d.type == "erhvervsevne" and kolonner and (m := INDTIL_KOLONNE.search(kolonner[-1][0])):
            d.til_alder = int(m.group(1))
    return raekker


def _detaljer(ord_: list[dict], selskaber: set[str]) -> list[tuple[str, str | None, str]]:
    """(selskab, aftalenr, bemærkninger) pr. dækning på en detaljeside. En blok begynder ved et selskab
    fra tabellen og slutter ved det næste."""
    linjer = [l for l in _linjer(ord_, tolerance=2) if l[0]["top"] > 95]
    blokke: list[list] = []
    for l in linjer:
        venstre = _tekst([w for w in l if w["x0"] < DETALJE_X])
        hoejre = _tekst([w for w in l if w["x0"] >= DETALJE_X])
        if venstre in selskaber:
            blokke.append([venstre, None, hoejre])
        elif blokke:
            if AFTALENR.match(venstre) and blokke[-1][1] is None:
                blokke[-1][1] = re.sub(r"\s+", "", venstre)
            elif venstre and not hoejre:
                continue  # næste modtager-gruppe ("Børn", "Forsikringstager")
            blokke[-1][2] += " " + hoejre
    return [tuple(b) for b in blokke]


def _sundhed(ord_: list[dict], type_: str) -> list[AflaestDaekning]:
    """Rækkerne på en detaljeside for sundhedsforsikring. Bemærkningerne står lodret centreret om
    rækken, så hver bemærkning hører til den nærmeste række."""
    linjer = [l for l in _linjer(ord_, tolerance=2) if l[0]["top"] > 95]
    venstre = [(l[0]["top"], t) for l in linjer if (t := _tekst([w for w in l if 150 <= w["x0"] < DETALJE_X]))]
    raekker = []
    for (top_s, selskab), (top, nr) in zip(venstre, venstre[1:]):
        if AFTALENR.match(nr) and not AFTALENR.match(selskab):
            raekker.append({"selskab": selskab, "aftalenr": re.sub(r"\s+", "", nr),
                            "midte": (top_s + top) / 2, "beloeb": None, "tekst": ""})
    if not raekker:
        return []
    for l in linjer:
        if _tekst(l).startswith("I alt"):
            continue
        naermeste = min(raekker, key=lambda r: abs(r["midte"] - l[0]["top"]))
        naermeste["tekst"] += " " + _tekst([w for w in l if DETALJE_X <= w["x0"] < 700])
        if (b := _beloeb([w for w in l if w["x0"] >= 700])) and abs(naermeste["midte"] - l[0]["top"]) < 15:
            naermeste["beloeb"] = b[0][0]
    ud = []
    for r in raekker:
        m = OPHOERER.search(r["tekst"])
        ud.append(AflaestDaekning(type=type_, selskab=r["selskab"], aftalenr=r["aftalenr"], skat=None, modtager=None,
                                  form="engang", beloeb=r["beloeb"], kolonner=[],
                                  til_alder=int(m.group(1)) if m else None,
                                  praemiefritagelse=_praemiefritagelse(r["tekst"])))
    return ud


def afsnit_sider(sider, indhold: str | None) -> dict[str, list[tuple[str, list[dict]]]]:
    """(type, ord) for hver side i forsikringsafsnittene. Indholdsfortegnelsen giver et vindue af sider
    (dens sidetal kan være en side forskudt), og sidehovedet afgør, hvilket afsnit siden hører til.
    Uden fortegnelse eller forsikringsafsnit: ingen sider læses."""
    if not indhold:
        return {}
    starter = sorted({int(n) - 1 for n in re.findall(r"(\d{1,3})\s+[A-ZÆØÅ]", indhold)})
    afsnit = {noegle: int(m.group(1)) - 1 for noegle, titel in AFSNIT.items()
              if (m := re.search(rf"(\d{{1,3}})\s+{titel.pattern}", indhold))}
    if not afsnit:
        return {}
    fra = min(afsnit.values()) - 1
    til = max(min((x for x in starter if x > s), default=s + 1) for s in afsnit.values()) + 1
    ud: dict[str, list] = {noegle: [] for noegle in afsnit}
    for side in sider[max(fra, 0):min(til, len(sider))]:
        ord_ = side.extract_words(x_tolerance=1.5)
        titel, under = _sidehoved(ord_)
        noegle = next((n for n, t in AFSNIT.items() if t.match(titel)), None)
        if noegle in ud:
            # "Udbetaling ved død - børn", "Visse kritiske sygdomme - børn": dækninger for dine børn.
            boern = noegle != "erhvervsevne" and ("børn" in titel or under.startswith("Hvis du har børn"))
            ud[noegle].append((noegle + ("_boern" if boern else ""), under, ord_))
    return ud


def aflaes_daekninger(sider, indhold: str | None) -> tuple[list[AflaestDaekning], list[str]]:
    """Alle forsikringer i rapporten og bemærkninger om afsnit, der ikke kunne læses."""
    daekninger: list[AflaestDaekning] = []
    bemaerkninger: list[str] = []
    for noegle, afsnit in afsnit_sider(sider, indhold).items():
        try:
            fundet = _afsnit(noegle, afsnit)
        except Exception:
            fundet = []
        if not fundet:
            bemaerkninger.append(f"Afsnittet \"{AFSNIT_NAVN[noegle]}\" kunne ikke aflæses. "
                                 "Se dine forsikringer på pensionsinfo.dk.")
        daekninger += fundet
    return daekninger, bemaerkninger


def _afsnit(noegle: str, sider: list[tuple[str, str, list[dict]]]) -> list[AflaestDaekning]:
    if noegle == "sundhed":
        return [d for type_, _, ord_ in sider for d in _sundhed(ord_, type_)]
    raekker = [r for type_, under, ord_ in sider if not under.startswith("Detaljer") for r in _tabel(ord_, type_)]
    selskaber = {r.daekning.selskab for r in raekker}
    detaljer = [(type_, *blok) for type_, under, ord_ in sider if under.startswith("Detaljer")
                for blok in _detaljer(ord_, selskaber)]
    # Detaljerne følger tabellens rækkefølge: hver række får den første ubrugte blok af samme type med
    # samme selskab (og aftalenr., når begge kendes).
    brugt = [False] * len(detaljer)
    for r in raekker:
        d = r.daekning
        for i, (type_, selskab, nr, tekst) in enumerate(detaljer):
            if brugt[i] or type_ != d.type or selskab != d.selskab or (nr and d.aftalenr and nr != d.aftalenr):
                continue
            brugt[i] = True
            r.detaljer.append(tekst)
            break
        alt = " ".join([r.tekst] + r.detaljer)
        if d.til_alder is None and (m := OPHOERER.search(alt) or OPHOERER_SENEST.search(alt)):
            # Ved død: kun hvis tabellen ikke siger andet ("Dækker, indtil pensionen er udbetalt").
            if not (d.type.startswith("doed") and "indtil pensionen er udbetalt" in alt):
                d.til_alder = int(m.group(1))
        d.praemiefritagelse = _praemiefritagelse(alt)
        d.noter = _noter(alt)
    return [r.daekning for r in raekker]
