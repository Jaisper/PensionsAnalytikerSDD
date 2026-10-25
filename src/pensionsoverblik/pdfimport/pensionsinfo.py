"""Lokal, deterministisk aflæsning af en PensionsInfo-rapport (Princip XI: intet til AI).

Rapportens tre sider med pensionsdata læses ud fra tekst og placering (pdfplumber):

- "Dine aftaler": saldo, årlig indbetaling og "Kun forsikring" pr. aftalenummer.
  Kolonnerne er højrestillede under overskrifterne "Årlig indbetaling" og "Opsparing".
- "Hvis du går på pension som X-årig får du" (tabellen): ét produkt pr. linje med
  skattekode, selskab, beløb pr. aldersperiode, aftalenummer, produkttype og evt.
  "Udbetales i N år". Kun det første (laveste) scenarie bruges.
- "Pension - flere oplysninger": tidligste og aftalt udbetalingsalder pr. produkt. Venstre
  kolonne (selskab / aftalenr. / type) læses med lav linjetolerance, fordi linjerne ligger
  meget tæt.

Formatet er udledt af en rigtig rapport (2026). Afvigende layout giver AflaesningFejl, så
brugeren kan indtaste selv.
"""
from __future__ import annotations

import io
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field

import pdfplumber

from .aflaeser import AflaesningFejl, Aflaesning, AflaestOrdning, Periode

logging.getLogger("pdfminer").setLevel(logging.ERROR)

BELOEB = re.compile(r"^(\d{1,3}(?:\.\d{3})*)\s?kr\.?$")
AFTALENR = re.compile(r"^\d[\d\s-]*\d$")
SCENARIE = re.compile(r"Hvis du går på pension som (\d+)-årig")
KOLONNE = re.compile(r"(Fra \d+ år|\d+-\d+ år|\d+ år)")
PRODUKTLINJE = re.compile(r"^([SAF]) (.+?) ((?:\d{1,3}(?:\.\d{3})* kr\. ?)+)(.*)$")
TIDLIGST = re.compile(r"tidligst udbetales (?:fra|ved) (\d+) år")
AFTALT = re.compile(r"kommer til udbetaling (?:fra|ved) (\d+) år")
PERIODE = re.compile(r"Udbetales i (\d+) år")
GRUPPER = {
    "Folkepension": "folkepension",
    "På én gang": "engang",
    "Om året i en årrække": "aarraekke",
    "Om året, så længe du lever": "livsvarig",
}

# Fordeling af én saldo på flere produkter under samme aftale (kun når rapporten ikke oplyser
# saldo pr. produkt) — overtaget fra legacy (`pdf_parser._fv_fra_payout`): hvert produkts
# udbetalingsprognose omregnes til en nutidsværdi med en fast, forsigtig rente og antal år.
# Uafhængig af brugerens egen afkastantagelse. Resultatet markeres altid som skøn.
FORDELING_RENTE = 0.04
FORDELING_LIVSVARIG_AAR = 25


# Sektionerne, parseren skal bruge — slås op i rapportens indholdsfortegnelse, så kun 3–5 af
# rapportens typisk ~30 sider læses (pdfminer bruger ~0,1 s pr. side).
SEKTIONER = {
    "aftaler": "Dine aftaler",
    "scenarie": "Hvis du går på pension som",
    "flere": "Pension - flere oplysninger",
}
_TEKST: dict[int, str] = {}


def _tekst(side) -> str:
    """Sidens tekst, udtrukket højst én gang pr. aflæsning (cachen nulstilles i aflaes)."""
    if id(side) not in _TEKST:
        _TEKST[id(side)] = side.extract_text() or ""
    return _TEKST[id(side)]


def _fra_indhold(sider, indhold: str) -> dict[str, list] | None:
    """Sektionernes sider ud fra indholdsfortegnelsen. Teksten er ofte flettet med en nabokolonne,
    så sidetal + titel søges hvor som helst i teksten."""
    start: dict[str, int] = {}
    for noegle, titel in SEKTIONER.items():
        if m := re.search(rf"(\d{{1,3}})\s+{re.escape(titel)}", indhold):
            start[noegle] = int(m.group(1)) - 1
    if len(start) != len(SEKTIONER) or max(start.values()) >= len(sider):
        return None
    # Alle sektionsstarter i fortegnelsen (sidetal efterfulgt af en titel med stort bogstav) giver
    # hver sektions sidste side, så nabosider aldrig læses.
    starter = sorted({int(n) - 1 for n in re.findall(r"(\d{1,3})\s+[A-ZÆØÅ]", indhold)} | set(start.values()))
    def sider_for(noegle: str) -> list:
        s = start[noegle]
        slut = min((x for x in starter if x > s), default=s + 1)
        return list(sider[s:min(slut, len(sider))])
    fundet = {noegle: sider_for(noegle) for noegle in SEKTIONER}
    # Kontrol (kun sektionernes første side, som alligevel skal læses): ellers bruges fallback.
    if all(fundet[k] and SEKTIONER[k] in _tekst(fundet[k][0]) for k in fundet):
        return fundet
    return None


def _relevante_sider(sider) -> dict[str, list]:
    """Sider pr. sektion. Bruger indholdsfortegnelsen (side 2-3); falder ellers tilbage til at
    gennemløbe siderne (uden indholdsfortegnelsen) og stopper, når alle sektioner er fundet."""
    for side in sider[1:3]:  # forsiden (side 1) har API'et allerede læst
        if "Indhold" in (tekst := _tekst(side)):
            if fundet := _fra_indhold(sider, tekst):
                return fundet
            break
    fundet: dict[str, list] = {}
    for side in sider:
        tekst = _tekst(side)
        if "Indhold" in tekst:
            continue
        for noegle, titel in SEKTIONER.items():
            if titel in tekst:
                fundet.setdefault(noegle, []).append(side)
        if "flere" in fundet and SEKTIONER["flere"] not in tekst:
            break  # efter sidste side med "flere oplysninger" er der intet mere at hente
    return fundet


def _kr(tekst: str) -> int:
    return int(tekst.replace(".", "").replace("kr", "").strip())


@dataclass
class _Aftale:
    nr: str
    indbetaling: int | None = None
    saldo: int | None = None
    kun_forsikring: bool = False


@dataclass
class _Produkt:
    skat: str
    selskab: str
    gruppe: str
    beloeb: list[int]
    aftalenr: str | None = None
    type_tekst: str = ""
    periode_aar: int | None = None
    tidligste: int | None = None
    aftalt: int | None = None
    saldo: int | None = None
    indbetaling: int | None = None
    noter: list[str] = field(default_factory=list)


def _normaliser_nr(nr: str) -> str:
    return re.sub(r"\s+", "", nr)


# ── "Dine aftaler" ───────────────────────────────────────────────────────────

def _dine_aftaler(side) -> dict[str, _Aftale]:
    # Dokumentets egen tekstrækkefølge: tætte linjer i nabokolonner kædes ellers sammen til én
    # linje, og bogstaverne flettes.
    ord_ = side.extract_words(use_text_flow=True)
    hoved: dict[str, dict] = {}
    for w in sorted(ord_, key=lambda w: w["top"]):  # overskriften er den øverste forekomst
        if w["text"] in ("Aftalenr.", "indbetaling", "Opsparing", "Bemærkninger"):
            hoved.setdefault(w["text"], w)
    if not {"Aftalenr.", "indbetaling", "Opsparing", "Bemærkninger"} <= hoved.keys():
        raise AflaesningFejl("ukendt_format", "Siden 'Dine aftaler' havde ikke det forventede format.")
    nr_x0, bem_x0 = hoved["Aftalenr."]["x0"], hoved["Bemærkninger"]["x0"]
    ind_x1, ops_x1 = hoved["indbetaling"]["x1"], hoved["Opsparing"]["x1"]
    hoved_bund = max(w["bottom"] for w in hoved.values())

    kolonne = [w for w in ord_ if nr_x0 - 3 <= w["x0"] < bem_x0 - 3 and w["top"] > hoved_bund]
    linjer: dict[int, list] = defaultdict(list)
    for w in kolonne:
        linjer[round(w["top"])].append(w)
    starter = sorted(t for t, ws in linjer.items() if ws[0]["text"][0].isdigit() or ws[0]["text"] == "ATP")
    aftaler: dict[str, _Aftale] = {}
    for i, top in enumerate(starter):
        nr = " ".join(w["text"] for w in sorted(linjer[top], key=lambda w: w["x0"]))
        if not AFTALENR.match(nr):
            continue  # fx ATP Livslang Pension
        bund = starter[i + 1] - 6 if i + 1 < len(starter) else side.height
        aftale = _Aftale(_normaliser_nr(nr))
        for w in ord_:
            if not top - 6 <= w["top"] < bund:
                continue
            if BELOEB.match(w["text"]):
                beloeb = _kr(w["text"])
                if abs(w["x1"] - ind_x1) < abs(w["x1"] - ops_x1):
                    aftale.indbetaling = beloeb
                else:
                    aftale.saldo = beloeb
            elif w["text"] == "forsikring" and abs(w["x1"] - ops_x1) < 15:
                aftale.kun_forsikring = True
        aftaler[aftale.nr] = aftale
    return aftaler


# ── Udbetalingstabellen ──────────────────────────────────────────────────────

def _udbetalingstabel(sider) -> tuple[int, list[str], list[_Produkt]]:
    alder = None
    kolonner: list[str] = []
    produkter: list[_Produkt] = []
    gruppe = None
    aktuel: _Produkt | None = None
    for side in sider:
        tekst = _tekst(side)
        m = SCENARIE.search(tekst)
        if not m or "Pensioner" not in tekst:
            continue
        if alder is not None and int(m.group(1)) != alder:
            break  # kun det første scenarie
        alder = int(m.group(1))
        tabel_slut = False
        for linje in tekst.splitlines():
            linje = linje.strip()
            if linje.startswith("Pensioner") or (not kolonner and KOLONNE.search(linje) and "kr." not in linje):
                if len(KOLONNE.findall(linje)) >= 2:
                    kolonner = KOLONNE.findall(linje)
                continue
            if linje.startswith("I alt"):
                aktuel = None
                tabel_slut = True
                continue
            ny_gruppe = next((g for navn, g in GRUPPER.items() if linje.startswith(navn) and "kr." in linje
                              and not linje.startswith(("S ", "A ", "F "))), None)
            if ny_gruppe:
                gruppe, aktuel = ny_gruppe, None
                continue
            if (m := PRODUKTLINJE.match(linje)) and gruppe:
                beloeb = [_kr(b) for b in re.findall(r"\d{1,3}(?:\.\d{3})* kr\.", m.group(3))]
                aktuel = _Produkt(m.group(1), m.group(2).strip(), gruppe, beloeb)
                produkter.append(aktuel)
                continue
            if aktuel is None:
                continue
            if AFTALENR.match(linje) and aktuel.aftalenr is None:
                aktuel.aftalenr = _normaliser_nr(linje)
            elif linje:
                if p := PERIODE.search(linje):
                    aktuel.periode_aar = int(p.group(1))
                aktuel.type_tekst = (aktuel.type_tekst + " " + re.sub(r"\s*(Udbetales|·).*$", "", linje)).strip()
        if tabel_slut:
            break  # "I alt årligt" — resten af sektionen (forklaringer) skal ikke læses
    if alder is None or not kolonner:
        raise AflaesningFejl("ukendt_format", "Udbetalingstabellen i rapporten blev ikke fundet.")
    return alder, kolonner, produkter


# ── "Pension - flere oplysninger" ────────────────────────────────────────────

def _flere_oplysninger(sider) -> list[dict]:
    blokke: list[dict] = []
    for side in sider:
        if "Pension - flere oplysninger" not in _tekst(side):
            continue
        ord_ = side.extract_words()
        udb = next((w for w in ord_ if w["text"] == "Udbetaling"), None)
        ind = next((w for w in ord_ if w["text"] == "Indbetaling"), None)
        if not udb or not ind:
            continue
        venstre = side.crop((0, udb["bottom"] + 2, udb["x0"] - 2, side.height)).extract_text_lines(y_tolerance=1)
        nr_idx = [i for i, l in enumerate(venstre) if AFTALENR.match(re.sub(r"\s+[SAF]$", "", l["text"].strip()))]
        for k, i in enumerate(nr_idx):
            if i == 0:
                continue
            top = venstre[i - 1]["top"]
            slut_i = nr_idx[k + 1] - 1 if k + 1 < len(nr_idx) else len(venstre)
            bund = venstre[slut_i]["top"] if slut_i < len(venstre) else side.height
            type_linjer = [l["text"].strip() for l in venstre[i + 1:slut_i] if l["text"].strip() not in ("S", "A", "F")]
            udbetaling = side.crop((udb["x0"] - 2, top - 2, ind["x0"] - 2, bund - 2)).extract_text(y_tolerance=1) or ""
            udbetaling = re.sub(r"\s+", " ", udbetaling)
            t, a = TIDLIGST.search(udbetaling), AFTALT.search(udbetaling)
            blokke.append({
                "selskab": venstre[i - 1]["text"].strip(),
                "aftalenr": _normaliser_nr(re.sub(r"\s+[SAF]$", "", venstre[i]["text"].strip())),
                "type": " ".join(type_linjer).replace("Ophørende", "").strip(),
                "tidligste": int(t.group(1)) if t else None,
                "aftalt": int(a.group(1)) if a else None,
            })
    return blokke


# ── Samling ──────────────────────────────────────────────────────────────────

def _kategori(p: _Produkt) -> str:
    t = p.type_tekst.lower()
    if "ratepension" in t:
        return "ratepension"
    if "aldersopsparing" in t:
        return "aldersopsparing"
    if "kapitalpension" in t:
        return "kapitalpension"
    if "livsvarig" in t or "livrente" in t:
        return "livsvarig"
    return {"aarraekke": "ratepension", "livsvarig": "livsvarig"}.get(p.gruppe, "ukendt")


def _type_noegle(tekst: str) -> str:
    t = tekst.lower()
    for navn in ("ratepension", "aldersopsparing", "kapitalpension", "livsvarig", "livrente"):
        if navn in t:
            return "livsvarig" if navn == "livrente" else navn
    return t


def _annuitetsfaktor(aar: int) -> float:
    return (1 - (1 + FORDELING_RENTE) ** -aar) / FORDELING_RENTE


def _vaegt(p: _Produkt) -> float:
    """Nutidsværdi af produktets udbetalingsprognose (som legacy)."""
    aarligt = next((b for b in p.beloeb if b), 0)
    if p.gruppe == "engang":
        return aarligt
    if p.gruppe == "aarraekke":
        return aarligt * _annuitetsfaktor(p.periode_aar or 1)
    return aarligt * _annuitetsfaktor(FORDELING_LIVSVARIG_AAR)


def _fordel(aftale: _Aftale, produkter: list[_Produkt], scenariealder: int, rateloft: int, am_bidrag: float) -> None:
    """Fordeler aftalens saldo og indbetaling på produkterne. Skøn markeres på produktet."""
    indbetaling = None if aftale.indbetaling is None else round(aftale.indbetaling * (1 - am_bidrag))
    if len(produkter) == 1:
        p = produkter[0]
        p.saldo, p.indbetaling = aftale.saldo, indbetaling
        if indbetaling:
            p.noter.append("Indbetalingen er omregnet til beløbet efter arbejdsmarkedsbidrag (8 %).")
        return
    vaegte = [_vaegt(p) for p in produkter]
    total = sum(vaegte)
    for p, v in zip(produkter, vaegte):
        p.saldo = None if aftale.saldo is None or not total else round(aftale.saldo * v / total)
        p.indbetaling = 0
        if aftale.saldo is not None:
            p.noter.append("Aftalens saldo er fordelt skønsmæssigt mellem produkterne efter udbetalingsprognosen – "
                           "tjek beløbet hos selskabet.")
    if indbetaling:
        rest = indbetaling
        for p in sorted(produkter, key=lambda p: {"ratepension": 0, "livsvarig": 1}.get(_kategori(p), 2)):
            k = _kategori(p)
            andel = min(rest, rateloft) if k == "ratepension" else (rest if k == "livsvarig" else 0)
            p.indbetaling, rest = andel, rest - andel
            p.noter.append("Indbetalingen er fordelt skønsmæssigt (ratepension op til loftet, resten til livsvarig).")


class PensionsInfoAflaeser:
    """Aflæser PDF-bytes fra pensionsinfo.dk. Ingen netværk, ingen AI."""

    def __init__(self, rateloft: int, am_bidrag: float):
        self.rateloft = rateloft
        self.am_bidrag = am_bidrag

    def aflaes(self, data: bytes) -> Aflaesning:
        _TEKST.clear()
        try:
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                sektioner = _relevante_sider(pdf.pages)
                aftaleside = next((s for s in sektioner.get("aftaler", []) if "Aftalenr." in _tekst(s)), None)
                if aftaleside is None or "scenarie" not in sektioner:
                    raise AflaesningFejl("ukendt_format", "Det ligner ikke en rapport fra PensionsInfo.")
                aftaler = _dine_aftaler(aftaleside)
                scenariealder, kolonner, produkter = _udbetalingstabel(sektioner["scenarie"])
                detaljer = _flere_oplysninger(sektioner.get("flere", []))
        except AflaesningFejl:
            raise
        except Exception:
            raise AflaesningFejl("ulaeselig", "Rapporten kunne ikke læses.") from None
        finally:
            _TEKST.clear()

        atp = next((b for p in produkter if p.selskab == "ATP" for b in p.beloeb if b), None)
        private = [p for p in produkter if p.selskab != "ATP" and not p.selskab.startswith("Folkepension")]
        for p in private:
            d = next((d for d in detaljer if d["aftalenr"] == p.aftalenr and _type_noegle(d["type"]) == _type_noegle(p.type_tekst)), None)
            if d:
                p.tidligste, p.aftalt = d["tidligste"], d["aftalt"]

        pr_aftale: dict[str, list[_Produkt]] = defaultdict(list)
        for p in private:
            pr_aftale[p.aftalenr or ""].append(p)
        for nr, ps in pr_aftale.items():
            _fordel(aftaler.get(nr, _Aftale(nr)), ps, scenariealder, self.rateloft, self.am_bidrag)

        ordninger = []
        for p in private:
            kategori = _kategori(p)
            perioder = []
            if p.periode_aar:
                start = p.aftalt or scenariealder
                perioder = [Periode(etiket=f"{start}-{start + p.periode_aar - 1} år", aarligt_beloeb=next((b for b in p.beloeb if b), None))]
            ordninger.append(AflaestOrdning(
                selskab=p.selskab, aftalenr=p.aftalenr, produkttype=p.type_tekst or kategori, kategori=kategori,
                saldo=p.saldo, aarlig_indbetaling=p.indbetaling, tidligste_udbetalingsalder=p.tidligste,
                aftalt_udbetalingsalder=p.aftalt, udbetalingsperioder=perioder,
                afgift_betalt=(p.skat == "F") if kategori == "kapitalpension" else None, noter=p.noter,
            ))
        daekket = {p.aftalenr for p in private}
        for nr, a in aftaler.items():
            if nr not in daekket and not a.kun_forsikring and a.saldo:
                ordninger.append(AflaestOrdning(
                    selskab=None, aftalenr=nr, produkttype="Ukendt", kategori="ukendt", saldo=a.saldo,
                    aarlig_indbetaling=a.indbetaling, tidligste_udbetalingsalder=None, aftalt_udbetalingsalder=None,
                    udbetalingsperioder=[], afgift_betalt=None,
                    noter=["Aftalen har en opsparing, men ingen udbetalingsprognose i rapporten."]))
        if not ordninger and atp is None:
            raise AflaesningFejl("ingen_ordninger", "Vi fandt ingen pensionsordninger i rapporten.")
        return Aflaesning(atp_aarlig=atp, ordninger=ordninger)
