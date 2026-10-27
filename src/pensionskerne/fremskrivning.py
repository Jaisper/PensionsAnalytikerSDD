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
    AKTIVLAG, Engangsbeloeb, FormueAar, JaevnAar, JaevnUdbetaling, Aarsdetaljer, SkatDetaljer,
    Aarsresultat, Advarsel, Antagelser, Fremskrivning, Indkomstkilde, Ordning,
    Partner, PartnerIndkomst, Pensionsprofil,
)
from .register.opslag import Regelopslag
from .regler.aktier import aktieindkomst_skat, ask_skat
from .regler.loen import ligningsmaessige_fradrag
from .regler.folkepension import (
    folkepensionsalder, foerste_aar_andel, indtaegtsgrundlag, pensionstillaeg, tillaegsregel,
)
from .regler.opsat import ventefaktor
from .regler.ordninger import engangs_netto, indbetalingsloft, livsvarig_ydelse, portioner, rateplan
from .regler.skat import beregn_skat, fordel
from .regler.udbetalingsalder import tidligste_udbetalingsalder
from .regler.ydelser import aeldrecheck, mediecheck, tillaegsprocent
from .jaevn import BUFFER_MAKS_ITERATIONER, BUFFER_TOLERANCE_KR, beregn_jaevn
from .validering import valider

OVERSKUD_ID = "ratepension_overskud_livsvarig"


@dataclass
class _Plan:
    id: str
    type: str
    start: int
    rater: dict[int, float] = field(default_factory=dict)   # alder → brutto (ratepension)
    livsvarig: float = 0.0                                  # årlig ydelse fra start (livsvarig)
    engangs: dict[int, float] = field(default_factory=dict)  # alder → netto (engangsbeløb og portioner)
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


@dataclass
class _Lag:
    """Opsparing uden for pension fordelt på skattekasser (013b): bank (kapitalindkomst), frit depot
    (værdi og anskaffelsessum; gevinsten er aktieindkomst ved salg) og aktiesparekonto (lager)."""
    bank: float = 0.0
    depot: float = 0.0
    anskaffelse: float = 0.0
    ask: float = 0.0

    @property
    def total(self) -> float:
        return self.bank + self.depot + self.ask

    def indsaet(self, type_: str, beloeb: float, anskaffelse: float | None = None) -> None:
        if type_ == "depot":
            self.depot += beloeb
            self.anskaffelse += beloeb if anskaffelse is None else anskaffelse
        else:
            setattr(self, type_, getattr(self, type_) + beloeb)

    def tilfoej(self, andet: "_Lag") -> None:
        self.bank += andet.bank
        self.depot += andet.depot
        self.anskaffelse += andet.anskaffelse
        self.ask += andet.ask

    def traek(self, beloeb: float, raekkefoelge: tuple[str, ...]) -> float:
        """Træk i rækkefølgen; returnerer den realiserede gevinst fra depotet (forholdsmæssigt)."""
        gevinst = 0.0
        for type_ in raekkefoelge:
            if beloeb <= 0:
                break
            tag = min(beloeb, getattr(self, type_))
            if tag <= 0:
                continue
            if type_ == "depot":
                andel = tag / self.depot
                gevinst += tag - self.anskaffelse * andel
                self.anskaffelse -= self.anskaffelse * andel
            setattr(self, type_, getattr(self, type_) - tag)
            beloeb -= tag
        return max(0.0, gevinst)

    def vaekst(self, bank: float, depot: float, ask: float) -> None:
        self.bank *= bank
        self.depot *= depot
        self.ask *= ask


@dataclass(frozen=True)
class _Opsparingsskat:
    """Bufferens bidrag til skat og formue pr. alder (fastpunktets tilstand, 009 og 013b)."""
    ki: dict[int, float] = field(default_factory=dict)              # bankens afkast (kapitalindkomst)
    formue: dict[int, float] = field(default_factory=dict)          # pr. 1. januar
    aktieindkomst: dict[int, float] = field(default_factory=dict)   # realiseret gevinst fra depotet
    ask_afkast: dict[int, float] = field(default_factory=dict)      # aktiesparekontoens afkast


def beregn(
    profil: Pensionsprofil,
    antagelser: Antagelser,
    satsaar: int,
    beregningsdato: date,
    streng: bool = False,
    *,
    buffer_start: Fremskrivning | None = None,
) -> Fremskrivning:
    """Fremskrivningen år for år. `buffer_start` er et gæt på bufferen (en nabos resultat) til
    fastpunktets første iteration; det ændrer kun, hvor hurtigt fastpunktet findes, ikke hvilket
    (inden for tolerancen). Optimeringen bruger det til at regne naboplaner hurtigere (009)."""
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

    # ── 0. Løn (feature 017) ─────────────────────────────────────────────────
    # Med løn begynder tabellen i dag, og udjævningen begynder ved stopalderen. Lønnen er i dagens
    # kroner og reguleres som satserne. Uden løn er alt som før.
    loen = profil.loen
    har_loen = loen is not None and (loen.aarlig > 0 or loen.deltid_aarlig > 0)
    stop = (loen.stop_alder or fp_alder) if loen is not None else fp_alder
    deltid_til = (loen.deltid_til_alder or stop) if loen is not None else stop

    def loen_i_aar(alder: int) -> float:
        if not har_loen:
            return 0.0
        if alder < stop:
            return loen.aarlig
        return loen.deltid_aarlig if alder < deltid_til else 0.0

    # ── 1. Opsparing frem til udbetalingsstart ───────────────────────────────
    start = {o.id: max(o.udbetaling_start_alder, alder_nu) for o in ordninger}
    # Med løn stopper pensionsindbetalingerne, når lønnen stopper (017).
    bidrag_slut = stop if har_loen else None
    fradragsberettiget: dict[int, float] = {}  # indbetaling til rate og livsvarig pr. alder (PI-fradrag)
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
            if bidrag_slut is not None and alder >= bidrag_slut:
                continue
            # Indbetalingen er i dagens kroner og reguleres som lønnen (017b); `loenvaekst` er
            # realvækst oven i.
            beloeb = ordning.aarlig_indbetaling * o.reguleringsfaktor * (
                1 + o.antagelse("loenvaekst", antagelser.loenvaekst)) ** aar_frem
            if ordning.type == "aldersopsparing":
                beloeb = min(beloeb, indbetalingsloft(ordning.type, alder, fp_alder, o))
            indbetaling[ordning.id] = beloeb

        fradragsberettiget[alder] = sum(b for i, b in indbetaling.items()
                                        if next(x.type for x in ordninger if x.id == i) in ("ratepension", "livsvarig"))
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
        # Kapitalpension omlagt til rate eller livrente (PBL § 41) regnes som den ordning (009).
        form = ordning.udbetalingsform if ordning.type == "kapitalpension" else "engangs"
        beregnet_type = form if form in ("ratepension", "livsvarig") else ordning.type
        plan = _Plan(ordning.id, beregnet_type, s, i_buffer=ordning.i_buffer)
        if beregnet_type == "ratepension":
            aar = ordning.udbetaling_aar or o.v("ordning.ratepension.min_aar")
            resterende = aar - (alder_nu - ordning.udbetaling_start_alder) if ordning.udbetaling_start_alder < alder_nu else aar
            for i, rate in enumerate(rateplan(saldo[ordning.id], max(0, resterende), afkast)):
                plan.rater[s + i] = rate
        elif beregnet_type == "livsvarig":
            horisont = max(antagelser.livsvarig_min_aar, antagelser.livsvarig_horisont_alder - s)
            plan.livsvarig = livsvarig_ydelse(saldo[ordning.id], horisont, afkast)
        elif form == "portioner":
            for i, brutto_portion in enumerate(portioner(saldo[ordning.id], ordning.udbetaling_aar, afkast)):
                plan.engangs[s + i] = engangs_netto(ordning.type, brutto_portion, o, ordning.afgift_betalt)
            o.v("ordning.kapitalpension.seneste_aar_efter_udbetalingsalder")
        else:
            plan.engangs[s] = engangs_netto(ordning.type, saldo[ordning.id], o, ordning.afgift_betalt)
        samlet.overtag(o)
        planer.append(plan)
    if any(o.type == "kapitalpension" and o.udbetalingsform == "portioner" for o in ordninger):
        advarsler.append(Advarsel(
            "PORTIONER_KRAEVER_AFTALE",
            "Kapitalpensionen er regnet udbetalt i portioner. Loven giver adgang til delvis udbetaling "
            "(pensionsbeskatningsloven § 26), og resten bliver i ordningen med lav skat af afkastet. "
            "Spørg dit pensionsselskab, hvordan de udbetaler i portioner.",
            registerposter=("ordning.kapitalpension.seneste_aar_efter_udbetalingsalder",),
        ))
    if any(o.type == "kapitalpension" and o.udbetalingsform in ("ratepension", "livsvarig") for o in ordninger):
        advarsler.append(Advarsel(
            "OMLAEGNING_KRAEVER_OVERFOERSEL",
            "Kapitalpensionen er regnet omlagt til ratepension eller livrente. Det sker ved en overførsel "
            "(pensionsbeskatningsloven § 41), som skal aftales med pensionsselskabet, før udbetalingen "
            "begynder. Udbetalingen beskattes derefter som personlig indkomst og nedsætter pensionstillægget.",
        ))

    tabel_start = alder_nu if har_loen else max(alder_nu, min([fp_alder] + [p.start for p in planer]))
    # Planens sidste år (019): levetidsscenarier ændrer det uden at ændre livrentens ydelse.
    plan_slut = antagelser.plan_slut_alder or antagelser.livsvarig_horisont_alder
    if antagelser.plan_slut_alder is not None:
        samlet.antagelse("plan_slut_alder", plan_slut)
    tabel_slut = max(
        [plan_slut, fp_start]
        + [max(p.rater) for p in planer if p.rater]
    )
    # Første år i udjævningen: stopalderen med løn (017), ellers første række.
    jaevn_fra = min(max(tabel_start, stop), tabel_slut) if har_loen else tabel_start

    # ── 3. År for år ─────────────────────────────────────────────────────────
    gift = profil.civilstand != "enlig"         # par: ydelserne behandler gifte og samlevende ens
    aegtefaelle = profil.civilstand == "gift"    # kun ægtefæller: skatteoverførsler (PSL § 10, stk. 3; § 7, stk. 5)
    partner_fp_alder = folkepensionsalder(profil.partner.foedselsdato, samlet) if profil.partner else None
    vente = ventefaktor(fp_alder, opsaettelse, samlet)
    foerste_andel = foerste_aar_andel(profil.foedselsdato)

    aarets_opslag: dict[int, Regelopslag] = {}  # genbruges på tværs af bufferens iterationer

    # ── 3a. Opsparing uden for pension (feature 013 og 013b) ─────────────────
    # Al opsparing forrentes som bufferen (pensionens afkast før PAL-skat); skatten afhænger af
    # typen. Bankens afkast er kapitalindkomst, depotets er kursgevinst, der beskattes som
    # aktieindkomst ved salg (PSL § 8 a), og aktiesparekontoens lagerbeskattes. Før første
    # udbetalingsår vokser banken brutto (skatten betales af lønnen, som kernen ikke kender:
    # forenkling), depotet uden skat (der sælges ikke) og aktiesparekontoen efter lagerskat (banken
    # trækker den på kontoen). Opsparing i planen indsættes i bufferen primo første udbetalingsår i
    # sit eget lag; urørt opsparing vokser videre, og skatten af dens afkast betales af udbetalingen.
    rente_buffer = afkast / (1 - samlet.v("pal.sats"))
    samlet.antagelse("buffer_afkast_som_pension", rente_buffer)
    ask_sats = samlet.v("ask.sats") if any(a.type == "ask" for a in profil.opsparing) else 0.0
    vaekst_foer = (1 + rente_buffer, 1 + rente_buffer, 1 + rente_buffer * (1 - ask_sats))
    vaekst_efter = (1 + rente_buffer,) * len(AKTIVLAG)

    def lag_i_dag(i_plan: bool) -> _Lag:
        lag = _Lag()
        for a in profil.opsparing:
            if a.i_plan != i_plan or a.saldo <= 0:
                continue
            if a.type == "depot":
                gevinst = a.urealiseret_gevinst
                if gevinst is None:
                    gevinst = a.saldo * samlet.antagelse("depot_urealiseret_andel", antagelser.depot_urealiseret_andel)
                lag.indsaet("depot", a.saldo, a.saldo - min(max(0.0, gevinst), a.saldo))
            else:
                lag.indsaet(a.type, a.saldo)
        return lag

    # Løbende indskud på aktiesparekontoen, mens der er løn (013b). De hidtidige indskud regnes lig
    # saldoen (forenkling); indskud over loftet står i frit depot.
    indskud_plan: dict[int, _Lag] = {}
    indskud_uroert: dict[int, _Lag] = {}
    indskud_i_alt: dict[int, float] = {}
    ask_over_loft: int | None = None
    ask_med_indskud = [a for a in profil.opsparing if a.type == "ask" and a.aarligt_indskud > 0] if har_loen else []
    if ask_med_indskud:
        indskudt = sum(a.saldo for a in profil.opsparing if a.type == "ask")
        for alder in range(alder_nu, stop):
            o = opslag(alder)
            plads = max(0.0, o.v("ask.indskudsloft") - indskudt)
            for a in ask_med_indskud:
                beloeb = a.aarligt_indskud * o.reguleringsfaktor
                til_ask = min(beloeb, plads)
                plads -= til_ask
                indskudt += til_ask
                maal = (indskud_plan if a.i_plan else indskud_uroert).setdefault(alder, _Lag())
                maal.indsaet("ask", til_ask)
                if beloeb > til_ask:
                    maal.indsaet("depot", beloeb - til_ask)
                    ask_over_loft = alder if ask_over_loft is None else ask_over_loft
                indskud_i_alt[alder] = indskud_i_alt.get(alder, 0.0) + beloeb
            samlet.overtag(o)
    har_depot = any(a.type == "depot" for a in profil.opsparing) or ask_over_loft is not None
    bank_foer_udbetaling = tabel_start > alder_nu and any(a.type == "bank" and a.saldo > 0 for a in profil.opsparing)

    # Opsparingen i planen frem til første udbetalingsår (ultimo hvert år).
    plan_lag = lag_i_dag(True)
    i_plan_start = plan_lag.total
    plan_foer_ultimo: dict[int, float] = {}
    for alder in range(alder_nu, tabel_start):
        plan_lag.vaekst(*vaekst_foer)
        plan_foer_ultimo[alder] = plan_lag.total
    i_plan_indskud = plan_lag.total
    if i_plan_indskud:
        indskud_plan.setdefault(tabel_start, _Lag()).tilfoej(plan_lag)

    # Den urørte opsparing: deterministisk, uafhængig af udjævningen.
    uroert = lag_i_dag(False)
    uroert_start = uroert.total
    uroert_primo: dict[int, float] = {}
    uroert_ultimo: dict[int, float] = {}
    uroert_ki: dict[int, float] = {}
    uroert_ask: dict[int, float] = {}
    if uroert_start > 0 or indskud_uroert:
        for alder in range(alder_nu, tabel_slut + 1):
            uroert_primo[alder] = uroert.total
            if alder in indskud_uroert:
                uroert.tilfoej(indskud_uroert[alder])
            if alder >= tabel_start:
                uroert_ki[alder] = uroert.bank * rente_buffer
                uroert_ask[alder] = uroert.ask * rente_buffer
                uroert.vaekst(*vaekst_efter)
            else:
                uroert.vaekst(*vaekst_foer)
            uroert_ultimo[alder] = uroert.total

    def husstandens_formue(alder: int, kalenderaar: int, egen_buffer: dict[int, float]) -> float:
        """Likvid formue pr. 1. januar (§ 72 d, stk. 2): den faste formue, egen buffer, egen opsparing
        og — kendes partneren som fuld profil — partnerens opsparing. Banken står der 1. januar i
        første udbetalingsår; engangsbeløb udbetales i løbet af året og tæller først året efter."""
        partner = profil.partner.formue_pr_aar.get(kalenderaar, 0.0) if profil.partner else 0.0
        egen = egen_buffer.get(alder, 0.0) + uroert_primo.get(alder, 0.0)
        if alder == tabel_start:
            egen += i_plan_indskud
        return profil.likvid_formue + egen + partner

    def _samme_buffer(gl: _Opsparingsskat, ny: _Opsparingsskat) -> bool:
        """Kapitalindkomsten, aktieindkomsten og ASK-afkastet, årene blev regnet med, er inden for
        12 × tolerancen pr. år af dem, bufferen giver, og intet år skifter side af ældrechecks
        formuegrænse. Så ændrer en ny iteration ikke den jævne udbetaling mere end tolerancen — også
        efter blot én iteration med et godt startgæt."""
        for x, y in ((gl.ki, ny.ki), (gl.aktieindkomst, ny.aktieindkomst), (gl.ask_afkast, ny.ask_afkast)):
            if max((abs(y.get(k, 0.0) - x.get(k, 0.0)) for k in y.keys() | x.keys()), default=0.0)                     >= BUFFER_TOLERANCE_KR * 12:
                return False
        formue, nye_formue = gl.formue, ny.formue
        for alder in nye_formue.keys() | formue.keys():
            o = aarets_opslag.get(alder)
            if o is None:
                continue
            graense = o.v("yd.aeldrecheck.formuegraense")
            kalenderaar = foedselsaar + alder
            if (husstandens_formue(alder, kalenderaar, formue) > graense) != (husstandens_formue(alder, kalenderaar, nye_formue) > graense):
                return False
        return True

    def aar_for_aar(bufferen: _Opsparingsskat):
        """Årene for givne kapitalindkomster, aktieindkomster, ASK-afkast og formuer fra bufferen
        (fastpunktet nedenfor)."""
        kapitalindkomst, formue = bufferen.ki, bufferen.formue
        atp_skoennet = False
        mellemskat_aldre: list[int] = []
        aktie_over_aldre: list[int] = []
        aar: list[Aarsresultat] = []

        for alder in range(tabel_start, tabel_slut + 1):
            kalenderaar = foedselsaar + alder
            o = aarets_opslag.get(alder) or aarets_opslag.setdefault(alder, opslag(alder))
            kommuneskat = o.kommuneskat(profil.kommune)
            kirkeskat = o.kirkeskat(profil.kommune) if profil.folkekirkemedlem else 0.0
            if kalenderaar > satsaar:
                o.antagelse("satsregulering", satsregulering)
            if alder == tabel_start and bank_foer_udbetaling:
                o.marker("forenkling:opsparing_skat_foer_udbetaling")
            if alder == tabel_start and har_depot:
                o.marker("forenkling:aktieafkast_som_kursgevinst")
            if alder == tabel_start and ask_med_indskud:
                o.marker("forenkling:ask_indskud_lig_saldo")
            if alder == tabel_start and not har_loen and alder_nu < fp_alder:
                o.marker("forenkling:ingen_loen")

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
                elif alder in plan.engangs:
                    engangs += plan.engangs[alder]
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

            # Løn (017): AM-bidrag af hele lønnen; pensionsindbetaling til rate og livsvarig fradrages
            # i den personlige indkomst (regnet som arbejdsgiverordning).
            loen_aar = loen_i_aar(alder) * o.reguleringsfaktor
            am = lmf = bidrag = 0.0
            if loen_aar > 0:
                am = loen_aar * o.v("skat.am_bidrag")
                bidrag = min(fradragsberettiget.get(alder, 0.0), loen_aar - am)
                if bidrag > 0:
                    o.marker("forenkling:pensionsindbetaling_som_arbejdsgiverordning")
                lmf = ligningsmaessige_fradrag(loen_aar, alder, fp_alder, o)
                brutto["loen"] = ("loen", loen_aar - am - bidrag)

            # 2.–4. folkepension og tillægsstyrede ydelser
            if profil.partner is not None and profil.partner.pensionist_fra_aar is not None:
                partner_er_pensionist = kalenderaar >= profil.partner.pensionist_fra_aar
            else:
                partner_er_pensionist = (
                    partner_fp_alder is not None
                    and kalenderaar - profil.partner.foedselsdato.year >= partner_fp_alder
                )
            buffer_ki = kapitalindkomst.get(alder, 0.0) + uroert_ki.get(alder, 0.0)
            aktieindkomst = bufferen.aktieindkomst.get(alder, 0.0)
            ask_afkast = bufferen.ask_afkast.get(alder, 0.0) + uroert_ask.get(alder, 0.0)
            grundlag = indtaegtsgrundlag(
                privat_s, atp_aar, profil.anden_kapitalindkomst + buffer_ki,
                _partner_indkomst(profil.partner, kalenderaar, o), partner_er_pensionist, o,
                aktieindkomst=aktieindkomst,
            )
            tp = 0
            tillaeg_fuldt = 0.0
            formue_primo = formuegraense = None
            if alder >= fp_start:
                andel = foerste_andel if alder == fp_start else 1.0
                brutto["grundbeloeb"] = ("grundbeloeb", o.v("fp.grundbeloeb") * vente * andel)
                regel = tillaegsregel(gift, partner_er_pensionist)
                tillaeg_fuldt = pensionstillaeg(0.0, regel, o) * vente * andel
                tillaeg = pensionstillaeg(grundlag, regel, o) * vente * andel
                if tillaeg > 0:
                    brutto["pensionstillaeg"] = ("pensionstillaeg", tillaeg)
                # Egen løn indgår ikke i pensionstillægget (L 117), men over bundfradraget i den
                # personlige tillægsprocent (017).
                arbejde = max(0.0, loen_aar - o.v("tp.arbejdsindkomst.bundfradrag")) if loen_aar > 0 else 0.0
                tp = tillaegsprocent(grundlag + arbejde, gift, o)
                if alder > fp_start:
                    formue_primo = husstandens_formue(alder, kalenderaar, formue)
                    formuegraense = o.v("yd.aeldrecheck.formuegraense")
                    for navn, beloeb in (("aeldrecheck", aeldrecheck(tp, formue_primo, o)),
                                         ("mediecheck", mediecheck(tp, o))):
                        if beloeb > 0:
                            brutto[navn] = (navn, beloeb)
                if profil.anden_kapitalindkomst > 0:
                    o.marker("forenkling:kapitalindkomst_ikke_beskattet")

            # 5.–6. personlig indkomst og skat
            pi_pr_kilde = {k: b for k, (_, b) in brutto.items()}
            pi = sum(pi_pr_kilde.values())
            overfoert = ekstra_bundfradrag = 0.0
            if aegtefaelle and profil.partner is not None:
                overfoert = profil.partner.uudnyttet_personfradrag_pr_aar.get(kalenderaar, 0.0)
                if kalenderaar in profil.partner.kapitalindkomst_pr_aar:
                    ekstra_bundfradrag = max(0.0, o.v("skat.kapitalindkomst.bundfradrag")
                                             - profil.partner.kapitalindkomst_pr_aar[kalenderaar])
            skat = beregn_skat(pi, kommuneskat, kirkeskat, o, kapitalindkomst=buffer_ki,
                               overfoert_personfradrag=overfoert, ekstra_ki_bundfradrag=ekstra_bundfradrag,
                               ligningsmaessige_fradrag=lmf)
            skat_pi = skat.total - skat.skat_kapitalindkomst
            andele = fordel(skat_pi, pi_pr_kilde)
            kilder = tuple(
                # Løn: brutto er lønnen efter pensionsindbetaling, skatten omfatter AM-bidraget.
                Indkomstkilde(k, type_, b + am, andele[k] + am, b - andele[k]) if k == "loen"
                else Indkomstkilde(k, type_, b, andele[k], b - andele[k])
                for k, (type_, b) in brutto.items()
            )
            netto = pi - skat_pi
            # Aktieindkomst (PSL § 8 a) beskattes særskilt; en ægtefælles uudnyttede
            # progressionsgrænse forhøjer grænsen (stk. 4). ASK-afkastet lagerbeskattes (013b).
            skat_aktier = skat_ask = 0.0
            if aktieindkomst > 0:
                graense = o.v("skat.aktieindkomst.progressionsgraense")
                ekstra = 0.0
                if aegtefaelle and profil.partner is not None and kalenderaar in profil.partner.aktieindkomst_pr_aar:
                    ekstra = max(0.0, graense - profil.partner.aktieindkomst_pr_aar[kalenderaar])
                skat_aktier = aktieindkomst_skat(aktieindkomst, o, ekstra)
                if aktieindkomst > graense + min(ekstra, graense):
                    aktie_over_aldre.append(alder)
            if ask_afkast > 0:
                skat_ask = ask_skat(ask_afkast, o)
            aar_frem = kalenderaar - beregningsdato.year
            realfaktor = 1 / (1 + o.antagelse("inflation", antagelser.inflation)) ** aar_frem
            netto_real = netto * realfaktor

            if pi > o.v("skat.mellemskat.graense"):
                mellemskat_aldre.append(alder)

            aar.append(Aarsresultat(
                alder=alder, kalenderaar=kalenderaar, kilder=kilder, personlig_indkomst=pi,
                skat_i_alt=skat_pi + am, indtaegtsgrundlag=grundlag, tillaegsprocent=tp,
                netto_i_alt=netto, netto_real=netto_real, realfaktor=realfaktor, engangsbeloeb_netto=engangs,
                sporing=tuple(o.brugt), flag=tuple(o.flag),
                kapitalindkomst=buffer_ki, skat_kapitalindkomst=skat.skat_kapitalindkomst,
                uudnyttet_personfradrag=skat.uudnyttet_personfradrag,
                detaljer=Aarsdetaljer(
                    skat=SkatDetaljer(**skat.fordeling), am_bidrag=am, ligningsmaessige_fradrag=lmf,
                    pensionsindbetaling=bidrag, pensionstillaeg_foer_modregning=tillaeg_fuldt,
                    formue_primo=formue_primo, formuegraense=formuegraense,
                ),
                aktieindkomst=aktieindkomst, skat_aktieindkomst=skat_aktier, skat_aktiesparekonto=skat_ask,
                indskud_opsparing=indskud_i_alt.get(alder, 0.0),
            ))
            samlet.overtag(o)
        return aar, mellemskat_aldre, atp_skoennet, aktie_over_aldre

    # ── 3b. Bufferen: kapitalindkomst og formue (feature 009) ────────────────
    # Bufferen (engangsbeløb uden for pension) giver kapitalindkomst og formue, som påvirker skat,
    # pensionstillæg og ældrecheck — og dermed den jævne udbetaling og bufferen selv. Det løses
    # deterministisk ved fastpunkt-iteration med et fast loft.
    engangs_bank: dict[int, float] = {}   # engangsbeløb fra ordninger: bufferens banklag
    for p_ in planer:
        if p_.i_buffer:
            for alder, beloeb in p_.engangs.items():
                engangs_bank[alder] = engangs_bank.get(alder, 0.0) + beloeb
    engangs_i_buffer = dict(engangs_bank)
    for alder, lag in indskud_plan.items():
        engangs_i_buffer[alder] = engangs_i_buffer.get(alder, 0.0) + lag.total

    def opsparingsskat(jaevn: JaevnUdbetaling | None) -> _Opsparingsskat:
        return _lag_forloeb(jaevn, engangs_bank, indskud_plan, rente_buffer, antagelser.traekraekkefoelge)

    def udjaevn(aar: list[Aarsresultat]) -> JaevnUdbetaling | None:
        """Udjævning fra `jaevn_fra` (017). Årene før (arbejdsår) udjævnes ikke: det faste beløb er
        årets nettoindkomst, og opsparing i planen og engangsbeløb samles i bufferen, vokser med
        renten og indsættes ved stopalderen."""
        foer = [a for a in aar if a.alder < jaevn_fra]
        if not foer:
            return beregn_jaevn(tuple(aar), engangs_i_buffer, rente_buffer, antagelser.inflation, beregningsdato.year)
        engangs = dict(engangs_i_buffer)
        b = 0.0
        foer_aar = []
        for a in foer:
            normal = a.disponibel
            b = (b + engangs.pop(a.alder, 0.0)) * (1 + rente_buffer)
            foer_aar.append(JaevnAar(alder=a.alder, jaevn=normal, normal=normal, fra_buffer=0.0, til_buffer=0.0,
                                     buffer_rest=b))
        engangs[jaevn_fra] = engangs.get(jaevn_fra, 0.0) + b
        j = beregn_jaevn(tuple(a for a in aar if a.alder >= jaevn_fra), engangs, rente_buffer,
                         antagelser.inflation, beregningsdato.year)
        return JaevnUdbetaling(j.niveau_foerste_aar, j.niveau_real, tuple(foer_aar) + j.aar)
    # Stopkriterium: den jævne udbetaling ændrer sig i intet år mere end BUFFER_TOLERANCE_KR om
    # måneden fra én iteration til den næste (hovedtallet vises afrundet til 100 kr.).
    tilstand = opsparingsskat(buffer_start.jaevn) if buffer_start else _Opsparingsskat()
    forrige: list[float] | None = None
    iteration = 0
    konvergeret = False
    while True:
        iteration += 1
        aar, mellemskat_aldre, atp_skoennet, aktie_over_aldre = aar_for_aar(tilstand)
        jaevn = udjaevn(aar)
        niveauer = [j.jaevn for j in jaevn.aar] if jaevn else []
        ny = opsparingsskat(jaevn)
        if ny == tilstand or _samme_buffer(tilstand, ny) or (
                forrige is not None and len(forrige) == len(niveauer)
                and max((abs(x - y) for x, y in zip(niveauer, forrige)), default=0.0) < BUFFER_TOLERANCE_KR * 12):
            konvergeret = True
            break
        if iteration >= BUFFER_MAKS_ITERATIONER:
            break
        tilstand, forrige = ny, niveauer

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
        if ordning.oprettet is None and ordning.tidligste_udbetalingsalder is None:
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

    # ── 5. Jævn udbetaling (US7) og bufferen (009) ───────────────────────────
    if any(a.kapitalindkomst > 0 for a in aar):
        advarsler.append(Advarsel(
            "BUFFER_SOM_OPSPARING",
            "Den jævne udbetaling forudsætter, at engangsbeløb og overskud placeres som opsparing uden "
            "for pension (bank eller obligationer) med samme afkast før skat som din pension. Afkastet er "
            "regnet som kapitalindkomst: det beskattes, nedsætter pensionstillægget, og opsparingen tæller "
            "med i ældrechecks formuegrænse.",
            registerposter=("pal.sats", "skat.kapitalindkomst.bundfradrag", "yd.aeldrecheck.formuegraense"),
        ))
    for fra, til in _intervaller(aktie_over_aldre):
        advarsler.append(Advarsel(
            "AKTIEINDKOMST_OVER_GRAENSE",
            f"Som {fra}–{til}-årig sælger du så mange aktier, at gevinsten er over progressionsgrænsen "
            "for aktieindkomst. Gevinsten over grænsen beskattes hårdere. Det kan betale sig at sprede "
            "salget over flere år.",
            aldre=(fra, til),
            registerposter=("skat.aktieindkomst.progressionsgraense", "skat.aktieindkomst.sats_hoej"),
        ))
    if ask_over_loft is not None:
        advarsler.append(Advarsel(
            "ASK_OVER_LOFT",
            f"Dine indskud på aktiesparekontoen når loftet som {ask_over_loft}-årig. Det overskydende er "
            "regnet som indskud i frit depot.",
            registerposter=("ask.indskudsloft",),
        ))
    if bank_foer_udbetaling:
        advarsler.append(Advarsel(
            "OPSPARING_FOER_UDBETALING",
            f"Din opsparing uden for pension er regnet til at vokse med afkastet frem til første "
            f"udbetaling som {tabel_start}-årig. Skatten af afkastet i de år betales af din løn og er "
            "ikke regnet med.",
            registerposter=("pal.sats",),
        ))
    if har_loen and jaevn is not None:
        hul = [j.alder for j in jaevn.aar if j.alder >= jaevn_fra and j.jaevn < BUFFER_TOLERANCE_KR * 12]
        for fra, til in _intervaller(hul):
            advarsler.append(Advarsel(
                "INDKOMSTHUL",
                f"Fra du stopper med at arbejde, har du ingen indkomst som {fra}–{til}-årig. Du kan "
                "bruge opsparing uden for pension, begynde en udbetaling tidligere eller stoppe senere.",
                aldre=(fra, til),
            ))
    if not konvergeret:
        advarsler.append(Advarsel(
            "BUFFER_IKKE_KONVERGERET",
            "Bufferens kapitalindkomst og formue kunne ikke regnes helt præcist (fx fordi formuen ligger "
            "tæt på ældrechecks formuegrænse). Tallene kan afvige lidt.",
        ))

    aldre_i_tabel = {a.alder for a in aar}
    engangsbeloeb = tuple(
        Engangsbeloeb(plan.id, plan.type, alder, beloeb, plan.i_buffer)
        for plan in planer for alder, beloeb in sorted(plan.engangs.items()) if beloeb and alder in aldre_i_tabel
    )
    return Fremskrivning(
        satsaar=satsaar, beregningsdato=beregningsdato, folkepensionsalder=fp_alder,
        aar=tuple(aar), advarsler=tuple(advarsler), antagelser=antagelser,
        sporing_samlet=tuple(samlet.brugt), jaevn=jaevn, engangsbeloeb=engangsbeloeb,
        buffer_iterationer=iteration,
        formue=_formue(alder_nu, tabel_start, aar, jaevn, plan_foer_ultimo, uroert_ultimo,
                       1 + antagelser.inflation),
        formue_start=i_plan_start + uroert_start,
        jaevn_fra_alder=jaevn_fra,
    )


def _formue(alder_nu, tabel_start, aar, jaevn, plan_foer_ultimo, uroert_ultimo, vaekst) -> tuple[FormueAar, ...]:
    """Opsparingen ved årets udgang fra i dag (013): før første udbetalingsår vokser den med renten;
    derefter er opsparingen i planen bufferen, og den urørte vokser videre."""
    buffer = {j.alder: max(0.0, j.buffer_rest) for j in jaevn.aar} if jaevn else {}
    slut = aar[-1].alder if aar else tabel_start - 1
    return tuple(
        FormueAar(
            alder,
            plan_foer_ultimo.get(alder, 0.0) if alder < tabel_start else buffer.get(alder, 0.0),
            uroert_ultimo.get(alder, 0.0),
            1 / vaekst ** (alder - alder_nu),
        )
        for alder in range(alder_nu, slut + 1)
    )



def _lag_forloeb(jaevn: JaevnUdbetaling | None, engangs_bank: dict[int, float], indskud: dict[int, "_Lag"],
                 rente: float, raekkefoelge: tuple[str, ...]) -> _Opsparingsskat:
    """Bufferen fordelt på lag (013b) ud fra udjævningens indsættelser og træk. Hvert år:
    engangsbeløb og overskud går i banken og opsparing i sit eget lag; trækket tages i
    rækkefølgen (depotet realiserer gevinsten forholdsmæssigt); derefter afkastet. Bankens afkast er
    kapitalindkomst (som 009-bufferens), aktiesparekontoens lagerbeskattes. Formuen er bufferen
    ved udgangen af året før. Udjævningen låner aldrig (010), så lagene er ikke negative."""
    if jaevn is None:
        return _Opsparingsskat()
    raekkefoelge = tuple(raekkefoelge) + tuple(t for t in AKTIVLAG if t not in raekkefoelge)
    lag = _Lag()
    ki: dict[int, float] = {}
    aktieindkomst: dict[int, float] = {}
    ask_afkast: dict[int, float] = {}
    formue: dict[int, float] = {}
    for j in jaevn.aar:
        lag.indsaet("bank", engangs_bank.get(j.alder, 0.0) + j.til_buffer)
        if j.alder in indskud:
            lag.tilfoej(indskud[j.alder])
        gevinst = lag.traek(j.fra_buffer, raekkefoelge)
        if gevinst > 0:
            aktieindkomst[j.alder] = gevinst
        if lag.bank * rente > 0:
            ki[j.alder] = lag.bank * rente
        if lag.ask * rente > 0:
            ask_afkast[j.alder] = lag.ask * rente
        lag.vaekst(1 + rente, 1 + rente, 1 + rente)
        if lag.total > 0 and rente > 0:  # som 009: uden afkast tæller bufferen ikke i formuen
            formue[j.alder + 1] = lag.total
    slut = jaevn.aar[-1].alder + 1
    formue.pop(slut, None)
    return _Opsparingsskat(ki, formue, aktieindkomst, ask_afkast)
