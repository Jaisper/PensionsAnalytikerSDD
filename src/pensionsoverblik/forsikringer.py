"""Forsikringerne fra rapporten som kort (feature 034). Kun omformatering og summer: beløbene efter
skat kommer fra kernen (`pensionskerne.forsikring`)."""
from __future__ import annotations

from datetime import date

from pensionskerne.forsikring import efter_skat

# (id, titel, typer, hovedtal): hovedtallet er engangsbeløbet eller den løbende ydelse.
GRUPPER = (
    ("doed", "Hvis du dør", ("doed", "doed_boern"), "engang"),
    ("erhvervsevne", "Hvis du mister arbejdsevnen", ("erhvervsevne",), "loebende"),
    ("kritisk_sygdom", "Hvis du får en kritisk sygdom", ("kritisk_sygdom", "kritisk_sygdom_boern"), "engang"),
    ("sundhed", "Sundhedsforsikring", ("sundhed", "sundhed_boern"), None),
)
LOEBENDE = ("aarraekke", "livsvarig")


def _summer(poster: list[dict]) -> dict | None:
    if not poster:
        return None
    return {
        "efter_skat": sum(p["netto"] for p in poster if p["netto"] is not None),
        "foer_skat": sum(p["beloeb"] for p in poster),
        "hos_modtager": sum(p["beloeb"] for p in poster if p["beskatning"] == "modtager"),
        "ukendt": sum(p["beloeb"] for p in poster if p["netto"] is None and p["beskatning"] != "modtager"),
    }


def _selskaber(poster: list[dict]) -> list[dict]:
    """Én bjælke pr. selskab: beløbet efter skat, hvor det kendes, ellers før skat."""
    pr: dict[str, dict] = {}
    for p in poster:
        s = pr.setdefault(p["selskab"], {"selskab": p["selskab"], "beloeb": 0.0, "efter_skat": True})
        s["beloeb"] += p["beloeb"] if p["netto"] is None else p["netto"]
        s["efter_skat"] = s["efter_skat"] and p["netto"] is not None
    return sorted(pr.values(), key=lambda s: -s["beloeb"])


def forsikringskort(daekninger: list[dict], kommune: str, folkekirkemedlem: bool, satsaar: int,
                    beregningsdato: date) -> list[dict]:
    def regn(d: dict, beloeb=None) -> dict:
        b = d["beloeb"] if beloeb is None else beloeb
        es = efter_skat(d["type"], d["skat"], d["form"], b, kommune, folkekirkemedlem, satsaar, beregningsdato)
        return {**d, "boern": d["type"].endswith("_boern"), "netto": es.netto, "beskatning": es.beskatning}

    kort = []
    for id_, titel, typer, hoved in GRUPPER:
        egne = [d for d in daekninger if d["type"] in typer]
        if not egne:
            continue
        poster = [regn(d) for d in egne]
        # Tab af arbejdsevne: skatten er progressiv, så skattepligtige løbende dækninger beskattes samlet,
        # og nettoen fordeles efter beløbene.
        samlet = [p for p in poster if p["type"] == "erhvervsevne" and p["skat"] == "S" and p["form"] in LOEBENDE
                  and p["beloeb"]]
        if len(samlet) > 1:
            i_alt = sum(p["beloeb"] for p in samlet)
            netto = regn(samlet[0], i_alt)["netto"]
            for p in samlet:
                p["netto"] = netto * p["beloeb"] / i_alt
        med_beloeb = [p for p in poster if p["beloeb"]]
        engang = [p for p in med_beloeb if p["form"] not in LOEBENDE and not p["boern"]]
        loebende = [p for p in med_beloeb if p["form"] in LOEBENDE and not p["boern"]]
        aldre = [p["til_alder"] for p in poster if p["til_alder"]]
        kort.append({
            "id": id_, "titel": titel, "hoved": hoved,
            "engang": _summer(engang), "loebende": _summer(loebende),
            "boern": _summer([p for p in med_beloeb if p["boern"]]),
            "selskaber": _selskaber(engang if hoved == "engang" else loebende) if hoved else [],
            "ophoer": {"tidligst": min(aldre), "alle_ens": len(set(aldre)) == 1} if aldre else None,
            "daekninger": poster,
        })
    return kort
