"""Find bedste plan (feature 007) — portering af legacy/sekventering.py til den nye kerne.

Optimeringen er en søgning over kernens egne beregninger (Princip I): hver kandidat er et
fuldt kald af `beregn` med skat, modregning i pensionstillæg og ældrecheck. Der er ingen
tilfældighed — samme input giver altid samme forslag.

**Mål** (som legacy): det faste månedsbeløb efter skat i dagens kroner, som borgeren kan leve
af HELE perioden — det laveste jævne beløb fra udgangspunktets første udbetaling (år uden
udbetaling tæller som 0). Ikke den samlede nutidsværdi, der belønner skæve, bagtunge forløb, og
heller ikke hovedtallet alene: det er niveauet efter det sidste engangsbeløb og ville belønne
at skubbe engangsbeløb sent, så de første år bliver lavere (opdaget i T003).

**Værn** i forhold til borgerens nuværende plan (legacy's fire tjek plus gulvet, tilpasset
kernens jævne model, hvor tidlige år kan "låne" af senere udbetalinger via en negativ buffer).
Alle regnes på årene fra udgangspunktets første udbetaling, i dagens kroner. "Rå" udbetaling er
den løbende nettoudbetaling uden udjævning; direkte engangsbeløb (ikke buffer) flyttes ikke og
er ens i alle kandidater, så de holdes ude af sammenligningen.

1. GULV: det faste beløb må ikke være under GULV_ANDEL af udgangspunktets.
2. DYBDE: laveste rå udbetaling må ikke være under DYBDE_TOLERANCE af udgangspunktets laveste.
3. VARIGHED: antallet af år med rå udbetaling under HARDSHIP_ANDEL af kandidatens eget faste
   beløb må ikke overstige udgangspunktets antal.
4. BUFFERDÆKNING: den dybeste negative buffer må højst være én måneds fast beløb dybere end
   udgangspunktets.
5. BUFFER-VARIGHED: antallet af år med negativ buffer må ikke overstige udgangspunktets.

Konstanterne er modelvalg fra legacy (se dens docstring for hvorfor hvert værn er nødvendigt),
ikke lovsatser — derfor står de her og ikke i registret.

**Søgerum**: startalder pr. ordning (fra pensionsalderen, dog tidligst den lovlige alder, til
folkepensionsalderen plus den maksimale opsættelse; feature 007b), ratepensionens varighed, folkepensionens opsættelse og — for
kapitalpension (feature 009) — udbetalingsformen: engangsbeløb, portioner over 2–20 år (PBL
§ 26) eller omlægning til ratepension (10–30 år) eller livrente (PBL § 41; ikke når afgiften er
betalt). Alle grænser fra registret og kernens regler (Princip II); kombinationer, kernen
afviser (fx portioner ud over fristen), tæller som ikke gennemførlige. Engangsbeløb, der ikke
er buffer, er faste.

**Søgning**: udtømmende, hvis søgerummet er lille nok; ellers multi-start grådig
koordinatsøgning fra udgangspunktet og fra kvantilerne 0, ¼, ½, ¾ og 1 af hver dimension.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from datetime import date
from itertools import product
from typing import Callable

from .fremskrivning import beregn
from .model import Antagelser, Fremskrivning, Pensionsprofil, UgyldigtInput
from .register.opslag import Regelopslag
from .regler.folkepension import folkepensionsalder
from .regler.udbetalingsalder import tidligste_udbetalingsalder

MAANEDER = 12
MAKS_EVALUERINGER = 1500
KOORDINAT_RUNDER = 3
STARTKVANTILER = (0.0, 0.25, 0.5, 0.75, 1.0)
FORM_AAR_GITTER = (2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30)  # antal år for portioner og omlagt ratepension

GULV_ANDEL = 0.70
DYBDE_TOLERANCE = 0.97
HARDSHIP_ANDEL = 0.85
BUFFER_TOLERANCE_MAANEDER = 1.0
# Bufferen går op i nul i sidste år; om det bliver -1e-9 eller +1e-9 afhænger af platformens
# regnefejl (CPython 3.11/3.12 og WebAssembly). Under 1 kr. tæller derfor som nul.
BUFFER_NUL_KR = 1.0

ENGANGSTYPER = ("aldersopsparing", "kapitalpension")


@dataclass(frozen=True)
class Plan:
    starter: dict[str, int]      # ordnings-id → startalder (kun ordninger i søgerummet)
    varighed: dict[str, int]     # ratepension-id → udbetalingsår
    opsaettelse: int             # folkepensionens opsættelse i år
    form: dict[str, tuple[str, int | None]] = field(default_factory=dict)  # kapitalpension → (udbetalingsform, år)

    def noegle(self) -> tuple:
        return (tuple(sorted(self.starter.items())), tuple(sorted(self.varighed.items())), self.opsaettelse,
                tuple(sorted(self.form.items())))


@dataclass(frozen=True)
class Optimering:
    udgangspunkt: Plan
    udgangspunkt_maaned: float   # fast beløb hele perioden (kr./md., dagens kroner)
    bedste: Plan | None          # None = ingen bedre gennemførlig plan fundet
    bedste_maaned: float | None
    evalueret: int
    mulige: int
    udtoemmende: bool


# ── Mål ─────────────────────────────────────────────────────────────────────────────────────────

def _jaevn_real(res: Fremskrivning) -> list[float]:
    return [j.jaevn * a.realfaktor for j, a in zip(res.jaevn.aar, res.aar)]


def fast_niveau(res: Fremskrivning, vindue: range) -> float:
    """Det faste beløb hele perioden (kr./md., dagens kroner): det laveste jævne beløb i vinduet."""
    if res.jaevn:
        pr_alder = dict(zip((a.alder for a in res.aar), _jaevn_real(res)))
    else:
        pr_alder = {a.alder: a.netto_real for a in res.aar}
    return min(pr_alder.get(alder, 0.0) for alder in vindue) / MAANEDER


def vindue(res: Fremskrivning) -> range:
    """Aldrene fra udjævningens første år (første udbetaling, eller stopalderen med løn, 017) til
    tabellens slutning."""
    return range(res.jaevn_fra_alder or res.aar[0].alder, res.aar[-1].alder + 1)


def slutniveau(res: Fremskrivning) -> float:
    """Det jævne niveau efter det sidste spring (kr./md., dagens kroner) — visningens "senere"
    niveau. Bruges kun ved uafgjort; uden jævn udbetaling det første hele folkepensionsår."""
    if res.jaevn:
        fra = vindue(res).start  # arbejdsår (017) tæller ikke med
        real = [x for x, a in zip(_jaevn_real(res), res.aar) if a.alder >= fra]
        ref = max([0] + [i for i in range(1, len(real)) if real[i] > real[i - 1] + MAANEDER])
        return real[ref] / MAANEDER
    foerste_hele = next((a for a in res.aar if a.alder > res.folkepensionsalder), res.aar[-1])
    return foerste_hele.netto_real / MAANEDER


def pensionsalder(profil: Pensionsprofil, fp_alder: int) -> int:
    """Alderen, borgeren går på pension (007b): stopalderen med løn, ellers folkepensionsalderen.
    Den bedste plan starter ingen ordning før, og målet regnes fra den."""
    if profil.loen is not None and profil.loen.stop_alder is not None:
        return profil.loen.stop_alder
    return fp_alder


def maalvindue(res: Fremskrivning, profil: Pensionsprofil) -> range:
    """Aldrene, målet regnes over (007b): fra pensionsalderen, hvis den er senere end vinduet."""
    v = vindue(res)
    return range(max(v.start, pensionsalder(profil, res.folkepensionsalder)), v.stop)


# ── Plan ↔ profil ───────────────────────────────────────────────────────────────────────────────

def _i_soegerum(o) -> bool:
    return not (o.type in ENGANGSTYPER and not o.i_buffer)


def _udgangspunkt(profil: Pensionsprofil, antagelser: Antagelser, satsaar: int | None = None) -> Plan:
    from . import register

    o = Regelopslag(satsaar or max(register.satsaar()), satsaar or max(register.satsaar()), 0.0)
    min_aar = int(o.v("ordning.ratepension.min_aar"))
    return Plan(
        starter={x.id: x.udbetaling_start_alder for x in profil.ordninger if _i_soegerum(x)},
        varighed={x.id: x.udbetaling_aar or min_aar for x in profil.ordninger if x.type == "ratepension"},
        opsaettelse=antagelser.folkepension_opsaettelse_aar,
        form={x.id: _form(x) for x in profil.ordninger if x.type == "kapitalpension" and _i_soegerum(x)},
    )


def _form(o) -> tuple[str, int | None]:
    return o.udbetalingsform, (o.udbetaling_aar if o.udbetalingsform in ("portioner", "ratepension") else None)


def anvend(profil: Pensionsprofil, antagelser: Antagelser, plan: Plan) -> tuple[Pensionsprofil, Antagelser]:
    def ny(o):
        o = replace(o, udbetaling_start_alder=plan.starter.get(o.id, o.udbetaling_start_alder),
                    udbetaling_aar=plan.varighed.get(o.id, o.udbetaling_aar))
        if o.id in plan.form:
            form, aar = plan.form[o.id]
            o = replace(o, udbetalingsform=form, udbetaling_aar=aar)
        return o

    ordninger = tuple(ny(o) for o in profil.ordninger)
    return replace(profil, ordninger=ordninger), replace(antagelser, folkepension_opsaettelse_aar=plan.opsaettelse)


# ── Søgerum ─────────────────────────────────────────────────────────────────────────────────────

def soegerum(profil: Pensionsprofil, antagelser: Antagelser, satsaar: int,
             beregningsdato: date | None = None) -> tuple[Plan, list[list[tuple]]]:
    """(udgangspunkt, dimensioner) — én dimension pr. beslutning: ("start", id, alder),
    ("varighed", id, år), ("form", id, (udbetalingsform, år)) eller ("opsaet", None, år).
    Ingen ordning starter før pensionsalderen (007b); en ordning, der allerede udbetaler, flyttes ikke."""
    o = Regelopslag(satsaar, satsaar, 0.0)
    fp_alder = folkepensionsalder(profil.foedselsdato, o)
    pension = pensionsalder(profil, fp_alder)
    alder_nu = beregningsdato.year - profil.foedselsdato.year if beregningsdato else None
    opsat_maks = int(o.v("opsat.maks_aar"))
    min_aar, maks_aar = int(o.v("ordning.ratepension.min_aar")), int(o.v("ordning.ratepension.maks_aar_efter_udbetalingsalder"))
    udgangspunkt = _udgangspunkt(profil, antagelser, satsaar)

    dimensioner: list[list[tuple]] = []
    for x in profil.ordninger:
        if not _i_soegerum(x):
            continue
        if x.tidligste_udbetalingsalder is not None:
            tidligste = x.tidligste_udbetalingsalder
        else:
            tidligste, _ = tidligste_udbetalingsalder(profil.foedselsdato, x.oprettet, fp_alder, o)
        lo, hi = max(math.ceil(tidligste), pension), fp_alder + opsat_maks
        if alder_nu is not None and x.udbetaling_start_alder < alder_nu:
            aldre = {x.udbetaling_start_alder}  # udbetaler allerede
        else:
            aldre = set(range(lo, hi + 1))
            if pension <= x.udbetaling_start_alder <= hi and x.udbetaling_start_alder >= math.ceil(tidligste):
                aldre.add(x.udbetaling_start_alder)
        dimensioner.append([("start", x.id, a) for a in sorted(aldre)])
        if x.type == "ratepension":
            dimensioner.append([("varighed", x.id, n) for n in range(min_aar, maks_aar + 1)])
        if x.type == "kapitalpension":
            # Et groft gitter af år er nok til at finde den rigtige udbetalingsform; borgeren
            # finjusterer antallet af år på tidslinjen bagefter.
            seneste = int(o.v("ordning.kapitalpension.seneste_aar_efter_udbetalingsalder"))
            former = [("engangs", None)] + [("portioner", n) for n in FORM_AAR_GITTER if 2 <= n <= seneste]
            if not x.afgift_betalt:
                former += [("ratepension", n) for n in FORM_AAR_GITTER if min_aar <= n <= maks_aar] + [("livsvarig", None)]
            dimensioner.append([("form", x.id, f) for f in former])
    dimensioner.append([("opsaet", None, n) for n in range(0, opsat_maks + 1)])
    return udgangspunkt, dimensioner


def _plan(vektor: tuple, udgangspunkt: Plan) -> Plan:
    starter, varighed, opsaettelse = dict(udgangspunkt.starter), dict(udgangspunkt.varighed), udgangspunkt.opsaettelse
    form = dict(udgangspunkt.form)
    for slag, oid, v in vektor:
        if slag == "start":
            starter[oid] = v
        elif slag == "varighed":
            varighed[oid] = v
        elif slag == "form":
            form[oid] = v
        else:
            opsaettelse = v
    return Plan(starter, varighed, opsaettelse, form)


def _vektor(plan: Plan, dimensioner: list[list[tuple]]) -> tuple:
    """Udgangspunktets placering i søgerummet (nærmeste værdi, hvis det ligger uden for)."""
    ud = []
    for dim in dimensioner:
        slag, oid, _ = dim[0]
        if slag == "form":
            nu = plan.form.get(oid)
            ud.append(next((t for t in dim if t[2] == nu), dim[0]))
            continue
        nu = plan.starter.get(oid) if slag == "start" else plan.varighed.get(oid) if slag == "varighed" else plan.opsaettelse
        ud.append(min(dim, key=lambda t: (abs(t[2] - nu), t[2])))
    return tuple(ud)


# ── Værn ────────────────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class _Reference:
    vindue: range                # aldre fra udgangspunktets første udbetaling
    maaned: float
    laveste_raa: float
    hardship_aar: int
    laveste_buffer: float
    buffer_hul_aar: int


def _raa(res: Fremskrivning, vindue: range) -> dict[int, float]:
    pr_alder = {a.alder: a.netto_real for a in res.aar}
    return {alder: pr_alder.get(alder, 0.0) for alder in vindue}


def _buffer_real(res: Fremskrivning) -> list[float]:
    if not res.jaevn:
        return []
    return [j.buffer_rest * a.realfaktor for j, a in zip(res.jaevn.aar, res.aar)]


def _reference(res: Fremskrivning, profil: Pensionsprofil) -> _Reference:
    v = maalvindue(res, profil)
    m = fast_niveau(res, v)
    raa = _raa(res, v)
    buffer = _buffer_real(res)
    return _Reference(
        vindue=v, maaned=m, laveste_raa=min(raa.values()),
        hardship_aar=sum(1 for v in raa.values() if v < HARDSHIP_ANDEL * m * MAANEDER),
        laveste_buffer=min(buffer, default=0.0), buffer_hul_aar=sum(1 for b in buffer if b < -BUFFER_NUL_KR),
    )


def _gennemfoerlig(res: Fremskrivning, ref: _Reference) -> float | None:
    """Kandidatens faste beløb hele perioden, eller None hvis et værn brydes."""
    m = fast_niveau(res, ref.vindue)
    if m < GULV_ANDEL * ref.maaned:
        return None
    raa = _raa(res, ref.vindue)
    if min(raa.values()) < DYBDE_TOLERANCE * ref.laveste_raa:
        return None
    if sum(1 for v in raa.values() if v < HARDSHIP_ANDEL * m * MAANEDER) > ref.hardship_aar:
        return None
    buffer = _buffer_real(res)
    if min(buffer, default=0.0) < ref.laveste_buffer - BUFFER_TOLERANCE_MAANEDER * m:
        return None
    if sum(1 for b in buffer if b < -BUFFER_NUL_KR) > ref.buffer_hul_aar:
        return None
    return m


def _evaluer_plan(plan: Plan, profil: Pensionsprofil, antagelser: Antagelser, satsaar: int,
                  beregningsdato: date, ref: _Reference, varm: dict | None = None) -> tuple[float, float] | None:
    """(fast beløb, slutniveau, samlet real netto) for en gennemførlig kandidat, ellers None.
    `varm` holder den forrige kandidats resultat som startgæt for bufferens fastpunkt."""
    p, a = anvend(profil, antagelser, plan)
    try:
        res = beregn(p, a, satsaar, beregningsdato, buffer_start=(varm or {}).get("res"))
    except UgyldigtInput:
        return None
    if varm is not None:
        varm["res"] = res
    m = _gennemfoerlig(res, ref)
    if m is None:
        return None
    return m, slutniveau(res), sum(x.netto_real for x in res.aar)


# ── Søgning ─────────────────────────────────────────────────────────────────────────────────────

def _ordensnoegle(v) -> tuple:
    """Deterministisk orden for værdier i søgerummet (tal eller (form, år) med år = None)."""
    if isinstance(v, tuple):
        return (v[0], v[1] if v[1] is not None else -1)
    return ("", v)


def optimer(
    profil: Pensionsprofil,
    antagelser: Antagelser,
    satsaar: int,
    beregningsdato: date,
    *,
    maks_evalueringer: int = MAKS_EVALUERINGER,
    fremdrift: Callable[[int, int], None] | None = None,
) -> Optimering:
    udgangspunkt, dimensioner = soegerum(profil, antagelser, satsaar, beregningsdato)
    basis = beregn(profil, antagelser, satsaar, beregningsdato)
    ref = _reference(basis, profil)
    mulige = math.prod(len(d) for d in dimensioner)
    udtoemmende = mulige <= maks_evalueringer
    budget = mulige if udtoemmende else maks_evalueringer

    score: dict[tuple, tuple | None] = {}
    # Naboplaner har næsten samme buffer: den forrige kandidat (i en koordinatsøgning typisk
    # nabo-værdien i samme dimension) er startgæt for bufferens fastpunkt — samme deterministiske
    # rækkefølge i CPython og browseren. Det bedste forslag regnes til sidst uden startgæt.
    varm: dict = {"res": basis}

    def evaluer(vektor: tuple) -> tuple | None:
        if vektor not in score:
            r = _evaluer_plan(_plan(vektor, udgangspunkt), profil, antagelser, satsaar, beregningsdato, ref, varm)
            # Rangering: fast beløb hele perioden (= hovedtallet), så det senere niveau, så samlet real netto — i hele
            # kroner. Uafrundede tal ville lade forskelle i sidste decimal mellem CPython og
            # WebAssembly (research R001) afgøre uafgjorte og sende søgningen ad en anden vej.
            score[vektor] = None if r is None else (round(r[0]), round(r[1]), round(r[2]))
            if fremdrift:
                fremdrift(min(len(score), budget), budget)
        return score[vektor]

    def bedre(a: tuple | None, b: tuple | None) -> bool:
        return a is not None and (b is None or a > b)

    start = _vektor(udgangspunkt, dimensioner)
    if udtoemmende:
        for vektor in product(*dimensioner):
            evaluer(vektor)
    else:
        startpunkter = [start] + [
            tuple(d[min(len(d) - 1, round(k * (len(d) - 1)))] for d in dimensioner) for k in STARTKVANTILER
        ]
        for sp in dict.fromkeys(startpunkter):
            if len(score) >= budget:
                break
            bedste_v, bedste_s = sp, evaluer(sp)
            for _ in range(KOORDINAT_RUNDER):
                forbedret = False
                for i, dim in enumerate(dimensioner):
                    for vaerdi in dim:
                        if len(score) >= budget:
                            break
                        kandidat = bedste_v[:i] + (vaerdi,) + bedste_v[i + 1:]
                        s = evaluer(kandidat)
                        if bedre(s, bedste_s):
                            bedste_v, bedste_s, forbedret = kandidat, s, True
                if not forbedret or len(score) >= budget:
                    break
    if fremdrift:
        fremdrift(budget, budget)

    udgangspunkt_maaned = ref.maaned
    gennemfoerlige = [(s, v) for v, s in score.items() if s is not None]
    if not gennemfoerlige:
        return Optimering(udgangspunkt, udgangspunkt_maaned, None, None, len(score), mulige, udtoemmende)
    (bedste_s, bedste_v) = max(gennemfoerlige, key=lambda sv: (sv[0], tuple(_ordensnoegle(t[2]) for t in sv[1])))
    bedste_plan = _plan(bedste_v, udgangspunkt)
    if bedste_s[0] <= round(udgangspunkt_maaned) or bedste_plan.noegle() == udgangspunkt.noegle():
        return Optimering(udgangspunkt, udgangspunkt_maaned, None, None, len(score), mulige, udtoemmende)
    p, a = anvend(profil, antagelser, bedste_plan)
    return Optimering(udgangspunkt, udgangspunkt_maaned, bedste_plan,
                      fast_niveau(beregn(p, a, satsaar, beregningsdato), ref.vindue), len(score), mulige, udtoemmende)
