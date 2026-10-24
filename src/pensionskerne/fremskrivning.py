"""År-for-år-fremskrivning — orkestrerer regelmodulerne (data-model: "Rækkefølge i et år").

Pr. kalenderår:
  1. aktive private udbetalinger (§ 11 A-rater, livsvarig, engangsbeløb)
  2. indtægtsgrundlag (private S-udbetalinger, ATP, kapitalindkomst, partnerandel)
  3. pensionstillæg × ventefaktor
  4. tillægsprocent → ældrecheck og mediecheck (kræver folkepension pr. 1. januar)
  5. personlig indkomst = alle skattepligtige kilder (intet AM-bidrag)
  6. skat samlet, fordelt forholdsmæssigt på kilderne
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .model import (
    Aarsresultat, Advarsel, Antagelser, Fremskrivning, Indkomstkilde, Ordning,
    Partner, PartnerIndkomst, Pensionsprofil,
)
from .register.opslag import Regelopslag
from .regler.folkepension import (
    folkepensionsalder, foerste_aar_andel, indtaegtsgrundlag, pensionstillaeg, tillaegsregel,
)
from .regler.opsat import ventefaktor
from .regler.ordninger import engangs_netto, indbetalingsloft, livsvarig_ydelse, rateplan
from .regler.skat import beregn_skat, fordel
from .regler.udbetalingsalder import tidligste_udbetalingsalder
from .regler.ydelser import aeldrecheck, mediecheck, tillaegsprocent
from .jaevn import beregn_jaevn
from .validering import valider

OVERSKUD_ID = "ratepension_overskud_livsvarig"


@dataclass
class _Plan:
    id: str
    type: str
    start: int
    rater: dict[int, float] = field(default_factory=dict)   # alder → brutto (ratepension)
    livsvarig: float = 0.0                                  # årlig ydelse fra start (livsvarig)
    engangs_netto: float = 0.0                              # netto i startåret (engangsbeløb)
    i_buffer: bool = True


def _kr(beloeb: float) -> str:
    return f"{beloeb:,.0f}".replace(",", ".")


def _intervaller(aldre: list[int]) -> list[tuple[int, int]]:
    intervaller: list[tuple[int, int]] = []
    for alder in aldre:
        if intervaller and alder == intervaller[-1][1] + 1:
            intervaller[-1] = (intervaller[-1][0], alder)
        else:
            intervaller.append((alder, alder))
    return intervaller


def _partner_indkomst(partner: Partner | None, kalenderaar: int, o: Regelopslag) -> PartnerIndkomst | None:
    if partner is None:
        return None
    pr_aar = partner.indkomst_pr_aar
    if not pr_aar:
        return PartnerIndkomst()
    if kalenderaar in pr_aar:
        return pr_aar[kalenderaar]
    o.marker("forenkling:partnerindkomst_naermeste_aar")
    return pr_aar[max(pr_aar) if kalenderaar > max(pr_aar) else min(pr_aar)]


def beregn(
    profil: Pensionsprofil,
    antagelser: Antagelser,
    satsaar: int,
    beregningsdato: date,
    streng: bool = False,
) -> Fremskrivning:
    valider(profil, antagelser, satsaar, beregningsdato)

    ordninger: list[Ordning] = list(profil.ordninger)
    satsregulering = antagelser.effektiv_satsregulering
    afkast = antagelser.afkast_efter_pal
    foedselsaar = profil.foedselsdato.year
    alder_nu = beregningsdato.year - foedselsaar

    def opslag(alder: int) -> Regelopslag:
        return Regelopslag(satsaar, foedselsaar + alder, satsregulering, streng)

    samlet = opslag(alder_nu)
    fp_alder = folkepensionsalder(profil.foedselsdato, samlet)
    advarsler: list[Advarsel] = []

    # ── 1. Opsparing frem til udbetalingsstart ───────────────────────────────
    start = {o.id: max(o.udbetaling_start_alder, alder_nu) for o in ordninger}
    saldo = {o.id: o.saldo for o in ordninger}
    rate_ids = [o.id for o in ordninger if o.type == "ratepension"]
    overskud_start = max((start[i] for i in rate_ids), default=alder_nu)
    overskud_saldo = 0.0
    foerste_overskud: tuple[int, float] | None = None

    for alder in range(alder_nu, max(start.values(), default=alder_nu)):
        o = opslag(alder)
        aar_frem = alder - alder_nu
        indbetaling: dict[str, float] = {}
        for ordning in ordninger:
            if alder >= start[ordning.id] or ordning.aarlig_indbetaling <= 0:
                continue
            beloeb = o.antagelse("loenvaekst", ordning.aarlig_indbetaling * (1 + antagelser.loenvaekst) ** aar_frem)
            if ordning.type == "aldersopsparing":
                beloeb = min(beloeb, indbetalingsloft(ordning.type, alder, fp_alder, o))
            indbetaling[ordning.id] = beloeb

        overskud = 0.0
        rate_sum = sum(indbetaling.get(i, 0.0) for i in rate_ids)
        if rate_sum > 0:
            loft = indbetalingsloft("ratepension", alder, fp_alder, o)
            if rate_sum > loft:
                for i in rate_ids:
                    if i in indbetaling:
                        indbetaling[i] *= loft / rate_sum
                overskud = rate_sum - loft
                foerste_overskud = foerste_overskud or (alder, overskud)

        for ordning in ordninger:
            if alder < start[ordning.id]:
                saldo[ordning.id] = saldo[ordning.id] * (1 + afkast) + indbetaling.get(ordning.id, 0.0)
        if alder < overskud_start:
            overskud_saldo = overskud_saldo * (1 + afkast) + overskud
        o.antagelse("afkast_efter_pal", afkast)
        samlet.overtag(o)

    if overskud_saldo > 0:
        ordninger.append(Ordning(OVERSKUD_ID, "livsvarig", 0.0, overskud_start))
        start[OVERSKUD_ID] = overskud_start
        saldo[OVERSKUD_ID] = overskud_saldo
        alder_o, beloeb_o = foerste_overskud
        advarsler.append(Advarsel(
            "RATEPENSION_LOFT",
            f"Indbetalingerne til ratepension overstiger loftet ({_kr(beloeb_o)} kr. for meget som "
            f"{alder_o}-årig). Det overskydende er regnet som indbetaling til livsvarig pension.",
            registerposter=("ordning.ratepension.indbetalingsloft",),
        ))

    # ── 2. Udbetalingsplaner ─────────────────────────────────────────────────
    opsaettelse = antagelser.folkepension_opsaettelse_aar
    fp_start = fp_alder + opsaettelse
    planer: list[_Plan] = []
    for ordning in ordninger:
        s = start[ordning.id]
        o = opslag(s)
        plan = _Plan(ordning.id, ordning.type, s, i_buffer=ordning.i_buffer)
        if ordning.type == "ratepension":
            aar = ordning.udbetaling_aar or o.v("ordning.ratepension.min_aar")
            resterende = aar - (alder_nu - ordning.udbetaling_start_alder) if ordning.udbetaling_start_alder < alder_nu else aar
            for i, rate in enumerate(rateplan(saldo[ordning.id], max(0, resterende), afkast)):
                plan.rater[s + i] = rate
        elif ordning.type == "livsvarig":
            horisont = max(antagelser.livsvarig_min_aar, antagelser.livsvarig_horisont_alder - s)
            plan.livsvarig = livsvarig_ydelse(saldo[ordning.id], horisont, afkast)
        else:
            plan.engangs_netto = engangs_netto(ordning.type, saldo[ordning.id], o)
        samlet.overtag(o)
        planer.append(plan)

    tabel_start = max(alder_nu, min([fp_alder] + [p.start for p in planer]))
    tabel_slut = max(
        [antagelser.livsvarig_horisont_alder, fp_start]
        + [max(p.rater) for p in planer if p.rater]
    )

    # ── 3. År for år ─────────────────────────────────────────────────────────
    gift = profil.civilstand == "gift_samlevende"
    partner_fp_alder = folkepensionsalder(profil.partner.foedselsdato, samlet) if profil.partner else None
    vente = ventefaktor(fp_alder, opsaettelse, samlet)
    foerste_andel = foerste_aar_andel(profil.foedselsdato)
    kirkeskat = profil.kirkeskat or 0.0
    atp_skoennet = False
    mellemskat_aldre: list[int] = []
    aar: list[Aarsresultat] = []

    for alder in range(tabel_start, tabel_slut + 1):
        kalenderaar = foedselsaar + alder
        o = opslag(alder)
        kommuneskat = o.kommuneskat(profil.kommune)
        if kalenderaar > satsaar:
            o.antagelse("satsregulering", satsregulering)

        # 1. private udbetalinger
        brutto: dict[str, tuple[str, float]] = {}
        engangs = 0.0
        for plan in planer:
            if plan.rater.get(alder):
                brutto[plan.id] = ("ratepension", plan.rater[alder])
                o.antagelse("afkast_efter_pal", afkast)
            elif plan.livsvarig and alder >= plan.start:
                brutto[plan.id] = ("livsvarig", plan.livsvarig)
                o.antagelse("afkast_efter_pal", afkast)
                o.antagelse("livsvarig_horisont_alder", antagelser.livsvarig_horisont_alder)
            elif plan.engangs_netto and alder == plan.start:
                engangs += plan.engangs_netto
        privat_s = sum(b for _, b in brutto.values())

        # ATP fra folkepensionsalderen (påvirkes ikke af opsættelse)
        atp_aar = 0.0
        if alder >= fp_alder:
            if profil.atp_aarlig is None:
                atp_aar = o.v("atp.fallback")
                o.marker("skoennet_atp")
                atp_skoennet = True
            else:
                atp_aar = profil.atp_aarlig * o.reguleringsfaktor
            andel = foerste_andel if alder == fp_alder else 1.0
            if atp_aar * andel > 0:
                brutto["atp"] = ("atp", atp_aar * andel)

        # 2.–4. folkepension og tillægsstyrede ydelser
        partner_er_pensionist = (
            partner_fp_alder is not None
            and kalenderaar - profil.partner.foedselsdato.year >= partner_fp_alder
        )
        grundlag = indtaegtsgrundlag(
            privat_s, atp_aar, profil.anden_kapitalindkomst,
            _partner_indkomst(profil.partner, kalenderaar, o), partner_er_pensionist, o,
        )
        tp = 0
        if alder >= fp_start:
            andel = foerste_andel if alder == fp_start else 1.0
            brutto["grundbeloeb"] = ("grundbeloeb", o.v("fp.grundbeloeb") * vente * andel)
            tillaeg = pensionstillaeg(grundlag, tillaegsregel(gift, partner_er_pensionist), o) * vente * andel
            if tillaeg > 0:
                brutto["pensionstillaeg"] = ("pensionstillaeg", tillaeg)
            tp = tillaegsprocent(grundlag, gift, o)
            if alder > fp_start:
                for navn, beloeb in (("aeldrecheck", aeldrecheck(tp, profil.likvid_formue, o)),
                                     ("mediecheck", mediecheck(tp, o))):
                    if beloeb > 0:
                        brutto[navn] = (navn, beloeb)
            if profil.anden_kapitalindkomst > 0:
                o.marker("forenkling:kapitalindkomst_ikke_beskattet")

        # 5.–6. personlig indkomst og skat
        pi_pr_kilde = {k: b for k, (_, b) in brutto.items()}
        pi = sum(pi_pr_kilde.values())
        skat = beregn_skat(pi, kommuneskat, kirkeskat, o)
        andele = fordel(skat.total, pi_pr_kilde)
        kilder = tuple(
            Indkomstkilde(k, type_, b, andele[k], b - andele[k]) for k, (type_, b) in brutto.items()
        )
        netto = pi - skat.total
        aar_frem = kalenderaar - beregningsdato.year
        netto_real = netto / (1 + o.antagelse("inflation", antagelser.inflation)) ** aar_frem

        if pi > o.v("skat.mellemskat.graense"):
            mellemskat_aldre.append(alder)

        aar.append(Aarsresultat(
            alder=alder, kalenderaar=kalenderaar, kilder=kilder, personlig_indkomst=pi,
            skat_i_alt=skat.total, indtaegtsgrundlag=grundlag, tillaegsprocent=tp,
            netto_i_alt=netto, netto_real=netto_real, engangsbeloeb_netto=engangs,
            sporing=tuple(o.brugt), flag=tuple(o.flag),
        ))
        samlet.overtag(o)

    # ── 4. Advarsler ─────────────────────────────────────────────────────────
    for fra, til in _intervaller(mellemskat_aldre):
        advarsler.append(Advarsel(
            "MELLEMSKAT_INTERVAL",
            f"Som {fra}–{til}-årig er din personlige indkomst over mellemskattegrænsen. "
            "Hver ekstra krone beskattes derfor hårdere.",
            aldre=(fra, til), registerposter=("skat.mellemskat.graense",),
        ))
    if atp_skoennet:
        advarsler.append(Advarsel(
            "ATP_SKOENNET",
            "Din ATP er ikke oplyst. Vi har brugt ATP's gennemsnitlige udbetaling.",
            registerposter=("atp.fallback",),
        ))
    for ordning in profil.ordninger:
        if ordning.oprettet is None:
            tidligste, _ = tidligste_udbetalingsalder(profil.foedselsdato, None, fp_alder, samlet)
            if ordning.udbetaling_start_alder < tidligste:
                advarsler.append(Advarsel(
                    "UDBETALING_FOER_LOVLIG_ALDER",
                    f"Vi kender ikke oprettelsesdatoen for '{ordning.id}'. Afhængigt af den kan "
                    f"ordningen tidligst udbetales som {tidligste:g}-årig — tjek med dit pensionsselskab.",
                    registerposter=("ordning.udbetalingsalder.fra_2018",),
                ))
    if opsaettelse > 0:
        advarsler.append(Advarsel(
            "750_TIMER",
            "Opsat folkepension kræver, at du arbejder mindst 750 timer om året i opsættelsesperioden.",
            registerposter=("opsat.maks_aar",),
        ))
        advarsler.append(Advarsel(
            "OPSAT_ANDRE_FORMER",
            "Ventetillægget er regnet som et livsvarigt tillæg. Du kan også vælge et forhøjet tillæg i "
            "10 år eller et engangsbeløb — det er ikke beregnet her.",
        ))

    # ── 5. Jævn udbetaling (US7) ─────────────────────────────────────────────
    engangs_i_buffer: dict[int, float] = {}
    for plan in planer:
        if plan.engangs_netto and plan.i_buffer:
            engangs_i_buffer[plan.start] = engangs_i_buffer.get(plan.start, 0.0) + plan.engangs_netto
    jaevn = beregn_jaevn(
        tuple(aar), engangs_i_buffer, afkast, antagelser.buffer_kapitalskat, antagelser.inflation,
        beregningsdato.year,
    )
    if engangs_i_buffer:
        samlet.antagelse("buffer_kapitalskat", antagelser.buffer_kapitalskat)
        advarsler.append(Advarsel(
            "BUFFER_YDELSE_FORENKLING",
            "Den jævne udbetaling forudsætter, at engangsbeløb placeres som opsparing uden for "
            "pension. Afkastet af den opsparing kan nedsætte pensionstillæg og ældrecheck — det "
            "er ikke regnet med.",
        ))
    if jaevn and min(a.buffer_rest for a in jaevn.aar) < 0:
        advarsler.append(Advarsel(
            "JAEVN_FORUDSAETTER_SENERE_UDBETALINGER",
            "Den jævne udbetaling er et gennemsnit. I nogle år forudsætter den penge fra udbetalinger, "
            "du først får senere.",
        ))

    return Fremskrivning(
        satsaar=satsaar, beregningsdato=beregningsdato, folkepensionsalder=fp_alder,
        aar=tuple(aar), advarsler=tuple(advarsler), antagelser=antagelser,
        sporing_samlet=tuple(samlet.brugt), jaevn=jaevn,
    )
