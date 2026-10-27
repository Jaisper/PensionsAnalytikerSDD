/* Pensionsoverblik — frontend uden build-trin.
   Alle tal kommer fra Python-kernen i worker.js (Princip I). Her formateres og vises de kun. */
"use strict";

const $ = (sel, rod = document) => rod.querySelector(sel);
const $$ = (sel, rod = document) => [...rod.querySelectorAll(sel)];

const talformat = new Intl.NumberFormat("da-DK", { maximumFractionDigits: 0 });
const kr = (n) => talformat.format(Math.round(n));
const procent = (v) => `${String(+(v * 100).toFixed(2)).replace(".", ",")} %`;
const decimal = (v) => String(v).replace(".", ",");

const TYPER = {
  ratepension: { titel: "Ratepension", farve: "--kilde-rate",
    forklaring: "Udbetales over et fast antal år, typisk 10–25 år." },
  livsvarig: { titel: "Livsvarig pension", farve: "--kilde-livsvarig",
    forklaring: "Kaldes også livrente. Udbetales hver måned resten af livet." },
  aldersopsparing: { titel: "Aldersopsparing", farve: "--kilde-checks",
    forklaring: "Udbetales skattefrit som ét beløb." },
  kapitalpension: { titel: "Kapitalpension", farve: "--kilde-folkepension",
    forklaring: "Ældre ordning, der udbetales som ét beløb med afgift." },
};

const OPRETTET = {
  ved_ikke: { tekst: "Ved ikke", dato: "" },
  foer2007: { tekst: "Før maj 2007", dato: "2000-01-01" },
  "2007_2017": { tekst: "Maj 2007 – 2017", dato: "2010-01-01" },
  fra2018: { tekst: "2018 eller senere", dato: "2020-01-01" },
};

const SATS_NAVNE = {
  "skat.bundskat": "Bundskat", "skat.personfradrag": "Personfradrag",
  "skat.mellemskat.sats": "Mellemskat", "skat.mellemskat.graense": "Grænse for mellemskat",
  "skat.topskat.sats": "Topskat", "skat.topskat.graense": "Grænse for topskat",
  "skat.toptopskat.sats": "Top-topskat", "skat.toptopskat.graense": "Grænse for top-topskat",
  "skat.skatteloft.mellemskat": "Skatteloft (mellemskat)", "skat.skatteloft.topskat": "Skatteloft (topskat)",
  "skat.skatteloft.toptopskat": "Skatteloft (top-topskat)",
  "fp.folkepensionsalder": "Folkepensionsalder", "fp.grundbeloeb": "Folkepension, grundbeløb",
  "fp.tillaeg.enlig.ydelse": "Pensionstillæg, enlige", "fp.tillaeg.enlig.fradrag": "Fradrag før tillægget nedsættes, enlige",
  "fp.tillaeg.enlig.aftrapning": "Nedsættelse af tillægget, enlige",
  "fp.tillaeg.gift.ydelse": "Pensionstillæg, gifte/samlevende", "fp.tillaeg.gift.fradrag": "Fradrag før tillægget nedsættes, par",
  "fp.tillaeg.gift_pensionist.aftrapning": "Nedsættelse, begge pensionister",
  "fp.tillaeg.gift_ikke_pensionist.aftrapning": "Nedsættelse, partner ikke pensionist",
  "fp.partner_ikke_pensionist.medregnet_andel": "Andel af partnerens indkomst, der tæller med",
  "fp.fradrag_forhoejelse.enlig": "Midlertidigt højere fradrag, enlige", "fp.fradrag_forhoejelse.gift": "Midlertidigt højere fradrag, par",
  "fp.fradrag_forhoejelse.nul_aar": "Det højere fradrag udløber", "fp.indtaegtsgrundlag.afrunding": "Indkomst afrundes ned til",
  "tp.enlig.bund": "Tillægsprocent: grænse, enlige", "tp.enlig.trin": "Tillægsprocent: 1 point pr.",
  "tp.gift.bund": "Tillægsprocent: grænse, par", "tp.gift.trin": "Tillægsprocent: 1 point pr. (par)",
  "yd.aeldrecheck": "Ældrecheck", "yd.aeldrecheck.formuegraense": "Formuegrænse for ældrecheck",
  "yd.aeldrecheck.minimum": "Mindste ældrecheck, der udbetales", "yd.mediecheck": "Mediecheck",
  "atp.fallback": "ATP, gennemsnit", "opsat.maks_aar": "Folkepension kan højst udskydes",
  "opsat.middellevetid_livsvarig": "Middellevetider til ventetillæg", "opsat.venteprocent_decimaler": "Ventetillæg afrundes til",
  "ordning.ratepension.indbetalingsloft": "Loft for indbetaling til ratepension",
  "ordning.ratepension.min_aar": "Ratepension, mindst antal år", "ordning.ratepension.maks_aar_efter_udbetalingsalder": "Ratepension, senest antal år efter",
  "ordning.aldersopsparing.indbetalingsloft": "Loft for aldersopsparing", "ordning.aldersopsparing.indbetalingsloft_forhoejet": "Loft for aldersopsparing tæt på pension",
  "ordning.aldersopsparing.forhoejet_aar_foer_fp": "Højere loft, år før folkepension", "ordning.kapitalpension.afgift": "Afgift af kapitalpension",
  "ordning.udbetalingsalder.fra_2018": "Tidligste udbetaling, ordninger fra 2018", "ordning.udbetalingsalder.2007_2017": "Tidligste udbetaling, ordninger 2007–2017",
  "ordning.udbetalingsalder.foer_2007": "Tidligste udbetaling, ordninger før 2007",
};

const ANTAGELSE_NAVNE = {
  afkast_efter_pal: ["Afkast pr. år efter skat på pensionen", procent],
  inflation: ["Prisstigning pr. år", procent],
  satsregulering: ["Årlig regulering af satser", procent],
  loenvaekst: ["Stigning i indbetalinger pr. år", procent],
  livsvarig_horisont_alder: ["Livsvarig pension beregnes, som om du lever til", (v) => `${v} år`],
  livsvarig_min_aar: ["Livsvarig pension mindst", (v) => `${v} år`],
  folkepension_opsaettelse_aar: ["Folkepension udskudt", (v) => (v ? `${v} år` : "nej")],
};

const tilstand = {
  trin: 1, ordninger: [], naesteId: 1,
  partnerOrdninger: [], naestePid: 1,  // partnerens ordninger (012); id'er "p1", "p2", … er unikke på tværs
  hvem: "dig",         // resultatsidens fane: "dig" | "partner" | "samlet" (012)
  vDig: null, husstand: null, samletGraf: null,
  mineSvar: null,      // svarene fra guiden (til "Nulstil")
  aktuelleSvar: null,  // svarene inkl. ændringer fra skyderne
  sidsteGyldige: null,
  panel: false,        // guidens formular står i datapanelet på resultatsiden
  v: null,             // seneste visningsmodel // seneste svar, der kunne beregnes (skydere vender tilbage hertil ved fejl)
  forrigeHovedtal: null, graf: null,
  tlRaekker: null, valgtRaekke: null, prAar: null,  // tidslinjen (006)
  forslag: null,       // forslag fra "Find bedste plan" (007): { d, noegle }
};

/* ── Hjælpere ──────────────────────────────────────────────────────────── */
function beloeb(tekst) {
  const renset = String(tekst ?? "").replace(/\s|\./g, "").replace(",", ".");
  return renset === "" ? null : Number(renset);
}
function css(navn) { return getComputedStyle(document.documentElement).getPropertyValue(navn).trim(); }
function el(tag, attrs = {}, ...boern) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "tekst") e.textContent = v; else if (k === "html") e.innerHTML = v; else e.setAttribute(k, v === true ? "" : v);
  }
  boern.flat().forEach((b) => b !== null && b !== undefined && e.append(b));
  return e;
}

/* ── Beregningsmotor (feature 005) ─────────────────────────────────────── */
/* Kernen kører i browseren (worker.js). Intet sendes til en server. */
const MAKS_PDF_BYTES = 25 * 1024 * 1024;
let motor = null;
let motorKlar = null;
const ventende = new Map();
let naesteKald = 1;

function startMotor() {
  ventende.forEach((v) => v.reject(new Error("genstart")));
  ventende.clear();
  motor?.terminate();
  if (typeof WebAssembly !== "object" || typeof Worker !== "function") {
    motorKlar = Promise.reject(new Error("ingen WebAssembly"));
    motorKlar.catch(() => {});
    visMotor({ fejl: true, tekst: "Din browser kan ikke køre beregningen. Brug en nyere version af Chrome, Edge, Firefox eller Safari." });
    return;
  }
  visMotor({ andel: 0 });
  motor = new Worker("worker.js", { type: "module" });
  motorKlar = new Promise((klar, fejl) => {
    motor.onmessage = ({ data }) => {
      if (data.status) {
        visMotor(data.status);
        if (data.status.klar) klar();
        if (data.status.fejl) fejl(new Error(data.status.fejl));
        return;
      }
      if (data.fremdrift !== undefined) { ventende.get(data.id)?.fremdrift?.(data.fremdrift); return; }
      const v = ventende.get(data.id);
      ventende.delete(data.id);
      if (data.fejl) v?.reject(new Error(data.fejl)); else v?.resolve(data.svar);
    };
    motor.onerror = (e) => { visMotor({ fejl: true }); fejl(new Error(e.message || "worker")); };
    // Pyodide melder ikke altid fejl, hvis en fil ikke kan hentes — den venter bare. Fristen giver
    // langsomme forbindelser tid til de cirka 15 MB og fanger resten (tests sætter en kortere frist).
    const fristMs = globalThis.motorFristMs ?? 120_000;
    const frist = setTimeout(() => { motor.terminate(); visMotor({ fejl: true }); fejl(new Error("frist")); }, fristMs);
    motor.addEventListener("message", ({ data }) => { if (data.status?.klar || data.status?.fejl) clearTimeout(frist); });
  });
  motorKlar.catch(() => {});
}

function visMotor({ andel, klar, fejl, tekst }) {
  const boks = $("#motor");
  if (klar) { boks.hidden = true; return; }
  boks.hidden = false;
  boks.classList.toggle("motor--fejl", !!fejl);
  if (andel !== undefined) $("#motor-fremdrift").value = andel;
  $("#motor-fremdrift").hidden = !!fejl;
  $("#motor-igen").hidden = !fejl || typeof WebAssembly !== "object";
  $("#motor-tekst").textContent = fejl
    ? (tekst || "Beregningen kunne ikke gøres klar. Tjek din forbindelse, og prøv igen.")
    : "Gør beregningen klar … Du kan godt begynde at udfylde imens.";
}

/** Kalder kernen i workeren. Venter selv, til motoren er klar (US3-2). */
function kald(op, ...args) {
  return kaldMedFremdrift(op, args, null);
}

/** Som kald, men vedFremdrift(andel 0–1) kaldes undervejs (optimeringen, feature 007). */
async function kaldMedFremdrift(op, args, vedFremdrift) {
  await motorKlar;
  return new Promise((resolve, reject) => {
    const id = naesteKald++;
    ventende.set(id, { resolve, reject, fremdrift: vedFremdrift });
    motor.postMessage({ id, op, args }, args.filter((a) => a instanceof ArrayBuffer));
  });
}

/** Dagens dato i borgerens tidszone, som kernen regner fra (Princip VI). */
function idag() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/* ── Guide ─────────────────────────────────────────────────────────────── */
async function hentKommuner() {
  try {
    const liste = await kald("kommuner");
    $("#kommuneliste").replaceChildren(...liste.map((k) => el("option", { value: k.navn })));
  } catch { /* feltet virker stadig som fri tekst */ }
}

function visTrin(n, fokus = true) {
  tilstand.trin = n;
  $$(".trin").forEach((f) => (f.hidden = +f.dataset.trin !== n));
  $$(".fremdrift li").forEach((li) => {
    const t = +li.dataset.trin;
    li.toggleAttribute("aria-current", t === n);
    if (t === n) li.setAttribute("aria-current", "step");
    li.classList.toggle("faerdig", t < n);
  });
  $("#tilbage").hidden = n === 1;
  $("#naeste").textContent = n === 5 ? "Se min pension" : "Næste →";
  if (fokus) $(`.trin[data-trin="${n}"] h2`).focus();
}

function ryd(rod = document) {
  $$(".felt--fejl", rod).forEach((f) => f.classList.remove("felt--fejl"));
  $$(".felt__fejl.dynamisk", rod).forEach((p) => p.remove());
  $$("[aria-invalid]", rod).forEach((i) => i.removeAttribute("aria-invalid"));
  $("#fejlboks").hidden = true;
}

function visFejl(felt, besked) {
  if (felt === "person.partner.foedselsdato") felt = fuldPartner() ? "p.foedselsdato" : "partner.foedselsdato";
  const maal = $$("[data-felt]").find((f) => f.dataset.felt.split(" ").includes(felt));
  if (!maal) {
    const boks = $("#fejlboks");
    boks.textContent = besked;
    boks.hidden = false;
    boks.focus?.();
    return;
  }
  const trin = maal.closest(".trin");
  if (trin && !tilstand.panel) visTrin(+trin.dataset.trin, false);
  if (tilstand.panel) aabnPanel("data", true);
  maal.classList.add("felt--fejl");
  const input = $("input, select", maal);
  const id = `${input?.id || "felt"}-fejl`;
  maal.append(el("p", { class: "felt__fejl dynamisk", id, tekst: besked }));
  if (input) {
    input.setAttribute("aria-invalid", "true");
    input.setAttribute("aria-describedby", `${input.getAttribute("aria-describedby") || ""} ${id}`.trim());
    input.focus();
  }
}

function validerTrin(n) {
  ryd();
  if (n === 1) {
    if (!$("#foedselsdato").value) { visFejl("foedselsdato", "Skriv din fødselsdato."); return false; }
    if (!$("#kommune").value.trim()) { visFejl("kommune", "Vælg din kommune."); return false; }
    if (erPar() && !fuldPartner() && !$("#partner-foedselsdato").value) {
      visFejl("partner.foedselsdato", "Skriv din partners fødselsdato."); return false;
    }
  }
  if (n === 3 && fuldPartner() && !$("#p-foedselsdato").value) {
    visFejl("p.foedselsdato", "Skriv din partners fødselsdato – eller indlæs rapporten ovenfor."); return false;
  }
  if (n === 2 || (n === 3 && fuldPartner())) {
    for (const o of n === 2 ? tilstand.ordninger : tilstand.partnerOrdninger) {
      if (beloeb(o.saldo) === null) { visFejl(`ordninger[${o.id}].saldo`, "Skriv opsparingen (0, hvis den er tom)."); return false; }
      if (!o.udbetaling_start_alder) { visFejl(`ordninger[${o.id}].udbetaling_start_alder`, "Skriv hvornår udbetalingen starter."); return false; }
    }
  }
  return true;
}

/* ── Partner (feature 012) ─────────────────────────────────────────────── */
const erPar = () => $("input[name=civilstand]:checked").value !== "enlig";
const fuldPartner = () => erPar() && $("input[name=partnerdata]:checked")?.value === "fuld";
const naesteTrin = (n) => (n === 2 && !fuldPartner() ? 4 : n + 1);
const forrigeTrin = (n) => (n === 4 && !fuldPartner() ? 2 : n - 1);

function opdaterPartnerFelter() {
  const fuld = fuldPartner();
  $("#partner-felter").hidden = !erPar();
  $("#partner-overslag").hidden = fuld;
  $('.fremdrift li[data-trin="3"]').hidden = !fuld;
  $('.fremdrift li[data-trin="4"] span').textContent = fuld ? "4" : "3";
  $('.fremdrift li[data-trin="5"] span').textContent = fuld ? "5" : "4";
  $("#p-opsparing-felter").hidden = !fuld;
  $("#partner-formue-felt").hidden = !erPar() || fuld;
  $("#p-opsaettelse-felt").hidden = !fuld;
  if (tilstand.panel) $('.trin[data-trin="3"]').hidden = !fuld;
}

function tilfoejOrdning(type, hvem = "dig") {
  const partner = hvem === "partner";
  const id = partner ? `p${tilstand.naestePid++}` : `o${tilstand.naesteId++}`;
  (partner ? tilstand.partnerOrdninger : tilstand.ordninger).push({ id, type, saldo: "", aarlig_indbetaling: "",
    udbetaling_start_alder: type === "livsvarig" ? 67 : 65, udbetaling_aar: 10, oprettet: "ved_ikke" });
  tegnOrdninger();
  $(`#${id}-saldo`).focus();
}

function ordningsFelt(o, navn, label, hjaelp, input) {
  const id = `${o.id}-${navn}`;
  input.id = id;
  if (hjaelp) input.setAttribute("aria-describedby", `${id}-hjaelp`);
  input.addEventListener("input", () => { o[navn] = input.value; });
  return el("div", { class: "felt", "data-felt": `ordninger[${o.id}].${navn}` },
    el("label", { for: id, tekst: label }),
    input,
    hjaelp ? el("p", { class: "felt__hjaelp", id: `${id}-hjaelp`, tekst: hjaelp }) : null);
}

function tegnOrdninger() {
  tegnOrdningsliste($("#ordninger"), tilstand.ordninger, (ny) => { tilstand.ordninger = ny; }, "#ny-type");
  tegnOrdningsliste($("#p-ordninger"), tilstand.partnerOrdninger, (ny) => { tilstand.partnerOrdninger = ny; }, "#p-ny-type");
}

function tegnOrdningsliste(rod, liste, saetListe, nyType) {
  rod.replaceChildren(...liste.map((o, i) => {
    const t = TYPER[o.type];
    const tal = (navn, ph = "0") => el("input", { inputmode: "numeric", class: "beloeb", value: o[navn] ?? "", placeholder: ph });
    const oprettet = el("select", {}, ...Object.entries(OPRETTET).map(([k, v]) => el("option", { value: k, selected: o.oprettet === k, tekst: v.tekst })));
    const felter = [
      ordningsFelt(o, "saldo", "Opsparing i dag (kr.)", null, tal("saldo")),
      ordningsFelt(o, "aarlig_indbetaling", "Indbetaling pr. år (kr.)", "Efter arbejdsmarkedsbidrag. 0 hvis du ikke indbetaler mere.", tal("aarlig_indbetaling")),
      ordningsFelt(o, "udbetaling_start_alder", o.type === "aldersopsparing" || o.type === "kapitalpension" ? "Udbetales (alder)" : "Udbetalingen starter (alder)",
        o.tidligste_udbetalingsalder ? `Tidligst udbetaling: ${decimal(o.tidligste_udbetalingsalder)} år (oplyst af selskabet).` : null,
        el("input", { inputmode: "numeric", value: o.udbetaling_start_alder })),
      o.type === "ratepension" ? ordningsFelt(o, "udbetaling_aar", "Udbetales over (antal år)", "Mindst 10 år.", el("input", { inputmode: "numeric", value: o.udbetaling_aar })) : null,
      o.tidligste_udbetalingsalder
        ? null
        : ordningsFelt(o, "oprettet", "Hvornår blev ordningen oprettet?", "Bestemmer, hvornår du tidligst må få pengene.", oprettet),
    ];
    const fjern = el("button", { type: "button", class: "knap knap--tekst", "aria-label": `Fjern ${t.titel.toLowerCase()} ${i + 1}`, tekst: "Fjern" });
    fjern.addEventListener("click", () => { saetListe(liste.filter((x) => x !== o)); tegnOrdninger(); $(nyType).focus(); });
    const infoId = `${o.id}-info`;
    const info = el("button", { type: "button", class: "info-knap", "aria-expanded": "false", "aria-controls": infoId, "aria-label": `Hvad er ${t.titel.toLowerCase()}?`, tekst: "i" });
    const infoTekst = el("p", { id: infoId, class: "felt__hjaelp", hidden: true, tekst: t.forklaring });
    info.addEventListener("click", () => { const aaben = info.getAttribute("aria-expanded") === "true"; info.setAttribute("aria-expanded", String(!aaben)); infoTekst.hidden = aaben; });
    return el("div", { class: "ordning", style: `--farve: var(${t.farve})` },
      el("div", { class: "ordning__top" }, el("h3", {}, `${t.titel} `, info), fjern),
      infoTekst,
      o.kilde ? el("p", { class: "aflaest", tekst: `Aflæst fra rapporten: ${o.kilde}` }) : null,
      o.usikkerheder?.length ? el("ul", { class: "usikkerheder", "aria-label": "Tjek disse oplysninger" }, o.usikkerheder.map((u) => el("li", { tekst: u }))) : null,
      el("div", { class: "ordning__felter" }, felter),
      o.type === "kapitalpension" ? el("div", { class: "ordning__felter" }, kapitalFelter(o)) : null,
      ENGANGSTYPER.has(o.type) ? bufferFelt(o) : null);
  }));
}

const OMLAEGNING = new Set(["ratepension", "livsvarig"]);  // kapitalpension omlagt: ingen buffer
const UDBETALINGSFORMER = {
  engangs: "Som ét beløb",
  portioner: "I portioner over flere år",
  ratepension: "Omlæg til ratepension",
  livsvarig: "Omlæg til livrente",
};

function kapitalFelter(o) {
  // Kapitalpensionens muligheder (feature 009): udbetalingsform, antal år og betalt afgift.
  o.udbetalingsform = o.udbetalingsform || "engangs";
  const formId = `${o.id}-udbetalingsform`;
  const aarId = `${o.id}-udbetaling_aar`;
  const afgiftId = `${o.id}-afgift_betalt`;
  const vaelger = el("select", { id: formId, "aria-describedby": `${formId}-hjaelp` },
    ...Object.entries(UDBETALINGSFORMER).map(([v, tekst]) => el("option", { value: v, selected: o.udbetalingsform === v, tekst })));
  const aar = el("input", { id: aarId, inputmode: "numeric", value: o.udbetaling_aar ?? "", "aria-describedby": `${aarId}-hjaelp` });
  const aarHjaelp = el("p", { class: "felt__hjaelp", id: `${aarId}-hjaelp` });
  const aarFelt = el("div", { class: "felt", "data-felt": `ordninger[${o.id}].udbetaling_aar` },
    el("label", { for: aarId, tekst: "Over hvor mange år?" }), aar, aarHjaelp);
  const formHjaelp = el("p", { class: "felt__hjaelp", id: `${formId}-hjaelp` });
  const afgift = el("input", { type: "checkbox", id: afgiftId, checked: !!o.afgift_betalt, "aria-describedby": `${afgiftId}-hjaelp` });
  const opdaterFelter = () => {
    const form = o.udbetalingsform;
    aarFelt.hidden = !["portioner", "ratepension"].includes(form);
    aarHjaelp.textContent = form === "ratepension"
      ? "10–30 år. Udbetalingen beskattes som personlig indkomst og nedsætter pensionstillægget."
      : "Mindst 2. Den sidste portion skal udbetales senest 20 år efter, at du tidligst kan få pengene.";
    formHjaelp.textContent = {
      engangs: "Der betales 40 % afgift, og beløbet påvirker ikke dit pensionstillæg.",
      portioner: "Hver portion beskattes med 40 % afgift. Resten bliver i pensionen, hvor afkastet beskattes lavt (15,3 %).",
      ratepension: "Kræver en overførsel, som du aftaler med dit pensionsselskab, før udbetalingen begynder.",
      livsvarig: "Kræver en overførsel, som du aftaler med dit pensionsselskab, før udbetalingen begynder.",
    }[form];
    for (const opt of vaelger.options) opt.disabled = o.afgift_betalt && ["ratepension", "livsvarig"].includes(opt.value);
    $$(`#${o.id}-i_buffer`).forEach((b) => (b.closest(".felt").hidden = OMLAEGNING.has(form)));
  };
  vaelger.addEventListener("change", () => {
    o.udbetalingsform = vaelger.value;
    if (o.udbetalingsform === "portioner" && !(o.udbetaling_aar >= 2)) o.udbetaling_aar = 5;
    if (o.udbetalingsform === "ratepension" && !(o.udbetaling_aar >= 10)) o.udbetaling_aar = 10;
    aar.value = o.udbetaling_aar ?? "";
    opdaterFelter();
  });
  aar.addEventListener("input", () => { o.udbetaling_aar = aar.value; });
  afgift.addEventListener("change", () => {
    o.afgift_betalt = afgift.checked;
    if (o.afgift_betalt && ["ratepension", "livsvarig"].includes(o.udbetalingsform)) { o.udbetalingsform = "engangs"; vaelger.value = "engangs"; }
    opdaterFelter();
  });
  opdaterFelter();  // synkront: kortet vises færdigt, uden at layoutet flytter sig bagefter
  return [
    el("div", { class: "felt", "data-felt": `ordninger[${o.id}].udbetalingsform` },
      el("label", { for: formId, tekst: "Hvordan vil du have den udbetalt?" }), vaelger, formHjaelp),
    aarFelt,
    el("div", { class: "felt", "data-felt": `ordninger[${o.id}].afgift_betalt` },
      el("label", { class: "valg", for: afgiftId }, afgift, " Afgiften er allerede betalt"),
      el("p", { class: "felt__hjaelp", id: `${afgiftId}-hjaelp`, tekst: "Fx hvis kapitalpensionen blev omlagt i 2013 eller 2014 mod 37,3 % afgift. Så er udbetalingen skattefri." })),
  ];
}


function bufferFelt(o) {
  // Engangsbeløb som buffer (feature 007, US2): fordeles i det faste beløb eller udbetales direkte.
  const id = `${o.id}-i_buffer`;
  const boks = el("input", { type: "checkbox", id, checked: o.i_buffer !== false, "aria-describedby": `${id}-hjaelp` });
  boks.addEventListener("change", () => { o.i_buffer = boks.checked; });
  return el("div", { class: "felt", "data-felt": `ordninger[${o.id}].i_buffer`, hidden: OMLAEGNING.has(o.udbetalingsform) },
    el("label", { class: "valg", for: id }, boks, " Brug som buffer"),
    el("p", { class: "felt__hjaelp", id: `${id}-hjaelp`, tekst: "Beløbet fordeles over årene i dit faste månedsbeløb. Slår du det fra, får du hele beløbet udbetalt det år." }));
}

function ordningSvar(o) {
  return {
    id: o.id, type: o.type, saldo: beloeb(o.saldo), aarlig_indbetaling: beloeb(o.aarlig_indbetaling) ?? 0,
    udbetaling_start_alder: beloeb(o.udbetaling_start_alder),
    udbetaling_aar: o.type === "ratepension" || (o.type === "kapitalpension" && ["portioner", "ratepension"].includes(o.udbetalingsform))
      ? beloeb(o.udbetaling_aar) : null,
    udbetalingsform: o.type === "kapitalpension" ? (o.udbetalingsform || "engangs") : "engangs",
    afgift_betalt: o.type === "kapitalpension" && !!o.afgift_betalt,
    oprettet: OPRETTET[o.oprettet].dato,
    tidligste_udbetalingsalder: o.tidligste_udbetalingsalder ?? null,
    i_buffer: o.i_buffer !== false,
  };
}

function partnerSvar() {
  if (!erPar()) return null;
  const foedselsdato = $(fuldPartner() ? "#p-foedselsdato" : "#partner-foedselsdato").value;
  if (!fuldPartner()) return { foedselsdato, oevrig_indkomst_aar: beloeb($("#partner-indkomst").value) ?? 0 };
  return { foedselsdato, profil: {
    ordninger: tilstand.partnerOrdninger.map(ordningSvar),
    atp_aarlig: beloeb($("#p-atp").value) || null,
    folkekirkemedlem: $("#p-folkekirke").checked,
    folkepension_opsaettelse_aar: +$("#p-opsaettelse").value,
    opsparing: opsparingSvar("p-"),
    loen: loenSvar("p-"),
  } };
}

/* Løn (feature 017): uden årsløn og deltidsløn sendes ingen løn. */
function loenSvar(pre = "") {
  const aarlig = beloeb($(`#${pre}loen`).value) ?? 0;
  const deltid = pre ? 0 : beloeb($("#deltid-loen").value) ?? 0;
  if (!aarlig && !deltid) return null;
  return {
    aarlig, stop_alder: beloeb($(`#${pre}stop-alder`).value) || null,
    deltid_aarlig: deltid, deltid_til_alder: pre ? null : beloeb($("#deltid-til").value) || null,
  };
}

/* Opsparing uden for pension (feature 013): ét bankaktiv pr. person. */
function opsparingSvar(pre = "") {
  const saldo = beloeb($(`#${pre}bank`).value);
  return saldo ? [{ id: `${pre}bank`, type: "bank", saldo, i_plan: $(`#${pre}bank-i-plan`).checked }] : [];
}

function guideSvar() {
  return {
    person: {
      foedselsdato: $("#foedselsdato").value,
      civilstand: $("input[name=civilstand]:checked").value,
      kommune: $("#kommune").value.trim(),
      folkekirkemedlem: $("#folkekirke").checked,
      likvid_formue: erPar() && !fuldPartner() ? beloeb($("#partner-formue").value) ?? 0 : 0,  // partnerens, ved overslag
      opsparing: opsparingSvar(),
      loen: loenSvar(),
      atp_aarlig: beloeb($("#atp").value) || null,  // tomt eller 0: ATP's gennemsnit (kernens fallback)
      partner: partnerSvar(),
    },
    ordninger: tilstand.ordninger.map(ordningSvar),
    antagelser: {
      afkast_efter_pal: +$("#afkast").value / 100,
      inflation: +$("#inflation").value / 100,
      folkepension_opsaettelse_aar: +$("#opsaettelse").value,
    },
  };
}

/* ── Indlæsning af PensionsInfo-rapport (feature 003) ──────────────────── */
async function aflaesPdf(hvem = "dig") {
  ryd();
  const pre = hvem === "partner" ? "p-" : "";
  const felt = `${pre}pdf`;
  const status = $(`#${pre}pdf-status`);
  const fil = $(`#${pre}pdf-fil`).files[0];
  if (!fil) { visFejl(felt, "Vælg rapporten først."); return; }
  if (fil.size > MAKS_PDF_BYTES) { visFejl(felt, `Filen er for stor. Den må højst fylde ${MAKS_PDF_BYTES / 1024 / 1024} MB.`); return; }
  const input = $(`#${pre}pdf-fil`);
  input.disabled = true;  // aflæsningen starter, når filen er valgt; ingen ny fil imens
  status.textContent = "Aflæser rapporten …";
  try {
    const svar = await kald("pdf", await fil.arrayBuffer());
    if (!svar.ok) {
      status.textContent = "";
      visFejl(svar.fejl.felt && svar.fejl.felt !== "pdf" ? svar.fejl.felt : felt, svar.fejl.besked);
      return;
    }
    udfyldFraRapport(svar.data, hvem);
  } catch {
    status.textContent = "";
    visFejl(felt, "Rapporten kunne ikke aflæses. Prøv igen, eller indtast oplysningerne selv.");
  } finally {
    input.disabled = false;
  }
}

function udfyldFraRapport(d, hvem = "dig") {
  const partner = hvem === "partner";
  if (d.person.foedselsdato) $(partner ? "#p-foedselsdato" : "#foedselsdato").value = d.person.foedselsdato;
  if (d.atp_aarlig) $(partner ? "#p-atp" : "#atp").value = kr(d.atp_aarlig);
  const liste = d.ordninger.map((o) => ({
    id: partner ? `p${tilstand.naestePid++}` : `o${tilstand.naesteId++}`, type: o.type,
    saldo: o.saldo === null ? "" : kr(o.saldo), aarlig_indbetaling: o.aarlig_indbetaling === null ? "" : kr(o.aarlig_indbetaling),
    udbetaling_start_alder: o.udbetaling_start_alder ?? "", udbetaling_aar: o.udbetaling_aar ?? 10,
    oprettet: o.oprettet, kilde: o.kilde, usikkerheder: o.usikkerheder,
    tidligste_udbetalingsalder: o.tidligste_udbetalingsalder,
    afgift_betalt: !!o.afgift_betalt,
  }));
  if (partner) tilstand.partnerOrdninger = liste; else tilstand.ordninger = liste;
  tegnOrdninger();
  const n = d.ordninger.length;
  const usikre = d.ordninger.filter((o) => o.usikkerheder.length).length;
  const hvor = partner ? "nedenfor" : "i trin 2";
  $(partner ? "#p-pdf-status" : "#pdf-status").replaceChildren(...[
    el("p", { tekst: `Vi har aflæst ${n === 1 ? "én ordning" : `${n} ordninger`}${d.atp_aarlig ? (partner ? " og din partners ATP" : " og din ATP") : ""}. `
      + (usikre ? `Tjek tallene ${hvor} – især ved ≈.` : `Tjek tallene ${hvor}.`) }),
    d.bemaerkninger.length ? el("ul", {}, d.bemaerkninger.map((b) => el("li", { tekst: b }))) : null,
  ].filter(Boolean));
}

/* ── Beregning ─────────────────────────────────────────────────────────── */
async function hentBeregning(svar) {
  const r = await kald("beregn", JSON.stringify(svar), idag());
  return r.ok ? { visning: r.data } : { fejl: r.fejl };
}

async function beregnFraGuide() {
  const knap = $("#naeste");
  knap.disabled = true; knap.textContent = "Regner …";
  try {
    const svar = guideSvar();
    const { fejl, visning } = await hentBeregning(svar);
    if (fejl) { visFejl(fejl.felt, fejl.besked); return; }
    tilstand.mineSvar = structuredClone(svar);
    tilstand.aktuelleSvar = structuredClone(svar);
    tilstand.sidsteGyldige = structuredClone(svar);
    tilstand.forrigeHovedtal = null;
    visResultat(visning);
  } catch {
    const boks = $("#fejlboks");
    boks.textContent = "Beregningen kunne ikke gennemføres lige nu. Prøv igen om lidt.";
    boks.hidden = false;
  } finally {
    knap.disabled = false; knap.textContent = tilstand.trin === 5 ? "Se min pension" : "Næste →";
  }
}

let ventetimer = null;
function genberegn(raekkeId = null) {
  clearTimeout(ventetimer);
  ventetimer = setTimeout(async () => {
    $$(".tl-fejl").forEach((p) => p.remove());
    try {
      const { fejl, visning } = await hentBeregning(tilstand.aktuelleSvar);
      if (fejl) {
        tilstand.aktuelleSvar = structuredClone(tilstand.sidsteGyldige);
        synkroniserFormular();
        tegnSkydere();
        tegnTidslinje(tilstand.v);
        const raekke = raekkeId && $(`.tl-raekke[data-id="${raekkeId}"]`);
        const besked = `${fejl.besked}. Vi har sat skyderen tilbage.`;
        if (raekke) raekke.append(el("p", { class: "tl-fejl", role: "alert", tekst: besked }));
        else $("#hovedtal-aendring").textContent = besked;
        return;
      }
      tilstand.sidsteGyldige = structuredClone(tilstand.aktuelleSvar);
      tilstand.forrigeHovedtal = +$("#hovedtal").dataset.vaerdi;
      visResultat(visning, false);
    } catch {
      $("#hovedtal-aendring").textContent = "Kunne ikke regne forfra lige nu.";
    }
  }, 300);
}

/* ── Resultat ──────────────────────────────────────────────────────────── */
function advarselEl(a, klasse = "advarsel") {
  return el("li", { class: klasse },
    el("span", { class: "ikon", "aria-hidden": "true", tekst: a.ikon }),
    el("div", {}, el("strong", { tekst: a.titel }), el("span", { class: "sr-only", tekst: a.ikon === "!" ? " (advarsel) " : " (forudsætning) " }), el("span", { tekst: ` ${a.besked}` })));
}

/* Feature 020b: dagens eller årets kroner. Kernen leverer realfaktoren; her divideres kun med den. */
function gemtKroner() {
  try { return localStorage.getItem("beloebsvisning") === "aarets" ? "aarets" : "dagens"; } catch { return "dagens"; }
}
const kronerTekst = (stort = false) => (tilstand.kroner === "aarets" ? (stort ? "I årets kroner" : "i årets kroner") : (stort ? "I dagens kroner" : "i dagens kroner"));

function iValgteKroner(v) {
  if (tilstand.kroner !== "aarets") return v;
  const f = v.graf.realfaktor;
  const del = (arr) => arr && arr.map((x, i) => (x === null ? null : x / f[i]));
  const graf = { ...v.graf, serier: v.graf.serier.map((s) => ({ ...s, vaerdier: del(s.vaerdier) })), jaevn: del(v.graf.jaevn),
    buffer: del(v.graf.buffer), skat_buffer: del(v.graf.skat_buffer), engangs: v.graf.engangs.map((e) => ({ ...e, netto_real: e.netto })) };
  const formue = v.formue && { ...v.formue, i_plan: v.formue.i_plan.map((x, i) => x / v.formue.realfaktor[i]),
    uden_for_plan: v.formue.uden_for_plan.map((x, i) => x / v.formue.realfaktor[i]) };
  if (formue) formue.rest = formue.i_plan.at(-1) + formue.uden_for_plan.at(-1);
  return { ...v, graf, formue };
}

function tegnGraf(v) {
  v = iValgteKroner(v);
  $("#kroner-tekst").textContent = kronerTekst();
  $$(".kroner-stort").forEach((s) => (s.textContent = kronerTekst(true)));
  const serier = v.graf.serier;
  $("#farveforklaring").replaceChildren(...serier.map((s) => el("li", {}, el("i", { style: `background: var(${s.farve})`, "aria-hidden": "true" }), s.titel)),
    ...(v.graf.jaevn ? [el("li", {}, el("i", { class: "linje", "aria-hidden": "true" }), JAEVN_NAVN)] : []));
  const forklaring = $("#jaevn-forklaring");
  forklaring.hidden = !v.graf.jaevn;
  forklaring.textContent = "Den stiplede linje er det beløb, du kan bruge hver måned, hvis du selv udjævner – uden "
    + "nogensinde at låne. Når søjlen er over linjen, sparer du op. Når den er under, bruger du af opsparingen "
    + "(også dine engangsbeløb). Den nederste graf viser opsparingen. Den går aldrig i minus: Når den er brugt op, "
    + "kan beløbet først stige, når der kommer flere penge. Derfor kan linjen gå op i trin.";
  const engangs = engangsMarkoerer(v);
  $("#graf-markeringer").replaceChildren(
    ...engangs.map((e) => el("li", {}, el("span", { class: "ikon ikon--engangs", "aria-hidden": "true", tekst: "◆" }), e.lang)),
    ...v.graf.markeringer.map((m) =>
      el("li", {}, el("span", { class: "ikon", "aria-hidden": "true", tekst: "!" }), `${m.titel}: som ${m.fra}–${m.til}-årig`)));

  // Tabelalternativ (FR-023)
  const jaevn = v.graf.jaevn;
  const hoved = el("tr", {}, el("th", { scope: "col", tekst: "Alder" }), ...serier.map((s) => el("th", { scope: "col", tekst: s.titel })),
    el("th", { scope: "col", tekst: "I alt" }), jaevn ? el("th", { scope: "col", tekst: JAEVN_NAVN }) : null,
    el("th", { scope: "col", tekst: "Engangsbeløb" }), v.graf.buffer ? el("th", { scope: "col", tekst: "Buffer" }) : null,
    v.graf.skat_buffer ? el("th", { scope: "col", tekst: "Skat af buffer pr. md." }) : null);
  const engangsPrAlder = new Map();
  for (const e of v.graf.engangs) engangsPrAlder.set(e.alder, (engangsPrAlder.get(e.alder) || 0) + e.netto_real);
  const raekker = v.graf.aldre.map((alder, i) => el("tr", {}, el("th", { scope: "row", tekst: `${alder} år` }),
    ...serier.map((s) => el("td", { tekst: s.vaerdier[i] ? `${kr(s.vaerdier[i])} kr.` : "–" })),
    el("td", { tekst: `${kr(serier.reduce((sum, s) => sum + s.vaerdier[i], 0))} kr.` }),
    jaevn ? el("td", { tekst: jaevn[i] === null ? "–" : `${kr(jaevn[i])} kr.` }) : null,
    el("td", { tekst: engangsPrAlder.has(alder) ? `${kr(engangsPrAlder.get(alder))} kr.` : "–" }),
    v.graf.buffer ? el("td", { tekst: v.graf.buffer[i] === null ? "–" : `${kr(v.graf.buffer[i])} kr.` }) : null,
    v.graf.skat_buffer ? el("td", { tekst: v.graf.skat_buffer[i] ? `${kr(v.graf.skat_buffer[i])} kr.` : "–" }) : null));
  $("#graf-tabel").replaceChildren(el("table", {}, el("caption", { class: "sr-only", tekst: `Udbetaling pr. måned efter skat ${kronerTekst()}, pr. alder og kilde` }), el("thead", {}, hoved), el("tbody", {}, raekker)));

  if (typeof Chart === "undefined") {
    $(".graf-ramme").hidden = true;
    $(".tabel-alternativ").open = true;
    return;
  }
  const data = {
    labels: v.graf.aldre.map((a) => `${a}`),
    datasets: [
      ...(jaevn ? [{ type: "line", label: JAEVN_NAVN, data: jaevn.map((x) => (x === null ? null : Math.round(x))), borderColor: css("--jaevn-linje"),
        borderDash: [6, 4], borderWidth: 3, pointRadius: 0, tension: 0, order: 0 }] : []),
      ...serier.map((s) => ({ label: s.titel, data: s.vaerdier.map((x) => Math.round(x)), backgroundColor: css(s.farve),
        borderWidth: 0, borderRadius: 2, stack: "netto", order: 1 })),
    ],
  };
  const valg = {
    responsive: true, maintainAspectRatio: false, animation: { duration: 250 },
    plugins: {
      legend: { display: false },
      tooltip: { callbacks: { title: (t) => `${t[0].label} år`, label: (c) => ` ${c.dataset.label}: ${kr(c.raw)} kr.`,
        footer: (t) => `I alt: ${kr(t.filter((x) => x.dataset.type !== "line").reduce((s, x) => s + x.raw, 0))} kr. om måneden` } },
    },
    onResize: () => requestAnimationFrame(placerBjaelker),
    // Feature 020: klik på et år åbner "Dit år".
    onClick: (_e, elementer, chart) => {
      if (!elementer.length) return;
      const alder = +chart.data.labels[elementer[0].index];
      if (tilstand.v.aar.some((a) => a.alder === alder)) visAar(alder);
    },
    scales: {
      x: { stacked: true, grid: { display: false }, title: { display: true, text: "Alder" }, ticks: { maxRotation: 0, autoSkipPadding: 8 } },
      y: { stacked: true, ticks: { callback: (x) => `${kr(x)} kr.` }, grid: { color: css("--graa-200") }, afterFit: fastYAkse },
    },
  };
  if (tilstand.graf) { tilstand.graf.$engangs = engangs; tilstand.graf.data = data; tilstand.graf.update(); }
  else {
    tilstand.graf = new Chart($("#graf"), { type: "bar", data, options: valg, plugins: [ENGANGS_PLUGIN] });
    tilstand.graf.$engangs = engangs;
    tilstand.graf.update();
  }
  tegnBuffergraf(v);
  tegnFormue(v);
}

/* ── Feature 008: engangsbeløb og buffer i grafen ────────────────────── */
const JAEVN_NAVN = "Fast beløb, hvis du udjævner";
const Y_AKSE_PX = 84;  // samme y-aksebredde i begge grafer, så aldrene flugter
const fastYAkse = (skala) => { skala.width = Y_AKSE_PX; };

function engangsMarkoerer(v) {
  // Ét punkt pr. ordning; portioner (009) samles til én markør ved første portion.
  const pr = new Map();
  for (const e of v.graf.engangs) pr.set(e.ordning_id, [...(pr.get(e.ordning_id) || []), e]);
  const ca = (x) => kr(Math.round(x / 1000) * 1000);
  return [...pr.values()].map((liste) => {
    const e = liste[0];
    const o = aktivSvar()?.ordninger.find((x) => x.id === e.ordning_id);
    const navn = TYPER[e.type]?.titel ?? "Engangsbeløb";
    const titel = o ? ordningstitel(o) : navn;
    const hvor = e.i_buffer ? "→ buffer" : "→ udbetales";
    const sum = liste.reduce((s, x) => s + x.netto_real, 0);
    const farve = css(TYPER[e.type]?.farve ?? "--kilde-engangs");
    if (liste.length === 1) {
      return { alder: e.alder, farve,
        kort: `${navn} ca. ${ca(sum)} kr. ${hvor}`,  // kort tekst i grafen; præcist beløb i listen
        lang: `${titel}: ${kr(sum)} kr. som ${e.alder}-årig ${hvor}` };
    }
    const sidste = liste.at(-1).alder;
    return { alder: e.alder, farve,
      kort: `${navn} ${liste.length} portioner ca. ${ca(sum)} kr. ${hvor}`,
      lang: `${titel}: ${liste.length} portioner som ${e.alder}–${sidste}-årig, i alt ${kr(sum)} kr. ${hvor}` };
  });
}

const ENGANGS_PLUGIN = {
  // Tegner engangsbeløb som en rombe med tekst øverst i plotområdet ved udbetalingsåret. Teksterne
  // lægges i den første række, hvor de ikke overlapper en anden markør, og får en hvid kant, så de
  // kan læses oven på søjlerne. De placerede felter gemmes i chart.$engangsBokse (tests).
  id: "engangs",
  afterDatasetsDraw(chart) {
    const liste = chart.$engangs || [];
    const aldre = tilstand.v?.graf.aldre || [];
    chart.$engangsBokse = [];
    if (!liste.length) return;
    const { ctx, chartArea, scales } = chart;
    const RAEKKE_PX = 18;
    const midt = (chartArea.left + chartArea.right) / 2;
    ctx.save();
    ctx.font = "600 12px system-ui, sans-serif";
    ctx.textBaseline = "middle";
    const optaget = [];  // [{x0, x1, raekke}]
    for (const e of liste) {
      const i = aldre.indexOf(e.alder);
      if (i < 0) continue;
      const x = scales.x.getPixelForValue(i);
      const hoejre = x > midt;
      const bredde = ctx.measureText(e.kort).width + 16;  // rombe, mellemrum og tekst
      const x0 = hoejre ? x - bredde : x - 7;
      const x1 = hoejre ? x + 7 : x + bredde;
      let raekke = 0;
      while (optaget.some((o) => o.raekke === raekke && x0 < o.x1 + 6 && o.x0 < x1 + 6)) raekke += 1;
      optaget.push({ x0, x1, raekke });
      const y = chartArea.top + 10 + raekke * RAEKKE_PX;
      chart.$engangsBokse.push({ x0, x1, y0: y - RAEKKE_PX / 2, y1: y + RAEKKE_PX / 2 });
      ctx.fillStyle = e.farve;
      ctx.beginPath();
      ctx.moveTo(x, y - 6); ctx.lineTo(x + 6, y); ctx.lineTo(x, y + 6); ctx.lineTo(x - 6, y);
      ctx.closePath();
      ctx.fill();
      ctx.textAlign = hoejre ? "right" : "left";
      const tx = hoejre ? x - 10 : x + 10;
      ctx.lineWidth = 4;
      ctx.lineJoin = "round";
      ctx.strokeStyle = css("--hvid") || "#fff";
      ctx.strokeText(e.kort, tx, y);
      ctx.fillStyle = css("--petrol-900");
      ctx.fillText(e.kort, tx, y);
    }
    ctx.restore();
  },
};

function tegnBuffergraf(v) {
  const ramme = $("#buffergraf-ramme");
  const buffer = v.graf.buffer;
  if (!buffer || typeof Chart === "undefined") {
    ramme.hidden = true;
    return;
  }
  ramme.hidden = false;
  const farve = css("--kilde-engangs");
  const roed = css("--fejl");
  const data = {
    labels: v.graf.aldre.map((a) => `${a}`),
    datasets: [{
      label: "Buffer", data: buffer.map((x) => (x === null ? null : Math.round(x))), borderColor: farve, borderWidth: 2, pointRadius: 0, tension: 0,
      fill: { target: "origin", above: `${farve}33`, below: `${roed}33` },
      segment: { borderColor: (c) => (c.p0.parsed.y < 0 || c.p1.parsed.y < 0 ? roed : farve) },
    }],
  };
  const valg = {
    responsive: true, maintainAspectRatio: false, animation: { duration: 250 },
    plugins: {
      legend: { display: false },
      title: { display: true, text: `Opsparing uden for pension, som bruges i din faste udbetaling, ${kronerTekst()}`, align: "start", color: css("--petrol-900") },
      tooltip: { callbacks: { title: (t) => `${t[0].label} år`, label: (c) => ` Opsparing: ${kr(c.raw)} kr.` } },
    },
    scales: {
      x: { offset: true, grid: { display: false }, ticks: { display: false } },  // samme kolonner som søjlegrafen
      y: { ticks: { callback: (x) => `${kr(x)} kr.`, maxTicksLimit: 4 }, grid: { color: css("--graa-200") }, afterFit: fastYAkse },
    },
  };
  if (tilstand.buffergraf) { tilstand.buffergraf.data = data; tilstand.buffergraf.update(); }
  else tilstand.buffergraf = new Chart($("#buffergraf"), { type: "line", data, options: valg });
}

function tegnFormue(v) {
  // Feature 013 (US4): opsparingen uden for pension år for år og restformuen.
  const f = v.formue;
  $("#formue-fold").hidden = !f;
  if (!f) return;
  $("#formue-titel").textContent = `Din opsparing uden for pension over tid: ${kr(f.rest)} kr. tilbage som ${f.rest_alder}-årig`;
  $("#formue-tabel").replaceChildren(el("table", {},
    el("caption", { class: "sr-only", tekst: "Opsparing uden for pension ved årets udgang i dagens kroner, pr. alder" }),
    el("thead", {}, el("tr", {}, ...["Alder", "Bruges i udbetalingen", "Urørt", "I alt"].map((x) => el("th", { scope: "col", tekst: x })))),
    el("tbody", {}, f.aldre.map((alder, i) => el("tr", {}, el("th", { scope: "row", tekst: `${alder} år` }),
      ...[f.i_plan[i], f.uden_for_plan[i], f.i_plan[i] + f.uden_for_plan[i]].map((x) => el("td", { tekst: `${kr(x)} kr.` })))))));
}

function tegnKort(v) {
  const sidsteAlder = v.graf.aldre.at(-1);
  $("#kort").replaceChildren(...v.kort.map((k) => {
    const detaljeId = `detaljer-${k.noegle}`;
    const infoId = `info-${k.noegle}`;
    const periode = k.til_alder === sidsteAlder ? `Fra du er ${k.fra_alder} år og resten af livet` : `Fra du er ${k.fra_alder} til ${k.til_alder} år`;
    const info = el("button", { type: "button", class: "info-knap", "aria-expanded": "false", "aria-controls": infoId, "aria-label": `Hvad er ${k.titel.toLowerCase()}?`, tekst: "i" });
    const infoTekst = el("div", { class: "kort__forklaring", id: infoId, hidden: true, "data-kort-forklaring": k.noegle },
      el("p", { tekst: k.forklaring }));
    info.addEventListener("click", () => { const aaben = info.getAttribute("aria-expanded") === "true"; info.setAttribute("aria-expanded", String(!aaben)); infoTekst.hidden = aaben; });

    const knap = el("button", { type: "button", class: "kort__knap pil-link", "aria-expanded": "false", "aria-controls": detaljeId },
      "Se år for år ", el("span", { "aria-hidden": "true", tekst: "→" }));
    const tabel = el("div", { class: "tabel-rul", id: detaljeId, hidden: true },
      el("table", {},
        el("thead", {}, el("tr", {}, ...["Alder", "Før skat pr. år", "Skat pr. år", "Efter skat pr. md."].map((t) => el("th", { scope: "col", tekst: t })))),
        el("tbody", {}, k.detaljer.map((d) => el("tr", {}, el("th", { scope: "row", tekst: `${d.alder} år` }),
          el("td", { tekst: `${kr(d.brutto)} kr.` }), el("td", { tekst: `${kr(d.skat)} kr.` }), el("td", { tekst: `${kr(d.netto / 12)} kr.` }))))));
    knap.addEventListener("click", () => { const aaben = knap.getAttribute("aria-expanded") === "true"; knap.setAttribute("aria-expanded", String(!aaben)); tabel.hidden = aaben; });

    if (k.engangs) {
      // Summen pr. ordning; de enkelte udbetalinger (fx portioner) under "Se år for år".
      const navn = (id, type) => {
        const o = aktivSvar()?.ordninger.find((x) => x.id === id);
        return o ? ordningstitel(o) : TYPER[type]?.titel;
      };
      const hvor = (iBuffer) => (iBuffer ? "til buffer" : "udbetales direkte");
      const engangsTabel = el("div", { class: "tabel-rul", id: detaljeId, hidden: true },
        el("table", {},
          el("caption", { class: "sr-only", tekst: "Engangsbeløb år for år" }),
          el("thead", {}, el("tr", {}, ...["Alder", "Ordning", "Efter afgift", "I dagens kroner", "Bruges"].map((t) => el("th", { scope: "col", tekst: t })))),
          el("tbody", {}, k.engangs.map((e) => el("tr", {}, el("th", { scope: "row", tekst: `${e.alder} år` }),
            el("td", { tekst: navn(e.ordning_id, e.type) }), el("td", { tekst: `${kr(e.netto)} kr.` }),
            el("td", { tekst: `${kr(e.netto_real)} kr.` }), el("td", { tekst: hvor(e.i_buffer) }))))));
      knap.addEventListener("click", () => { engangsTabel.hidden = knap.getAttribute("aria-expanded") !== "true"; });
      return el("article", { class: "kort", style: `--farve: var(${k.farve})` },
        el("div", { class: "kort__ikon", "aria-hidden": "true" }),
        el("h3", { class: "kort__titel" }, k.titel, info), infoTekst,
        el("ul", { class: "engangsliste" }, k.pr_ordning.map((o) => el("li", {}, `${navn(o.ordning_id, o.type)}: ${kr(o.netto)} kr. `,
          el("small", { tekst: `${o.antal > 1 ? `${o.antal} udbetalinger som ${o.fra_alder}–${o.til_alder}-årig` : `som ${o.fra_alder}-årig`}`
            + ` – ${kr(o.netto_real)} kr. i dagens kroner – ${hvor(o.i_buffer)}` })))),
        el("p", { class: "kort__periode", tekst: "Efter eventuel afgift." }),
        knap, engangsTabel);
    }
    return el("article", { class: "kort", style: `--farve: var(${k.farve})` },
      el("div", { class: "kort__ikon", "aria-hidden": "true" }),
      el("h3", { class: "kort__titel" }, k.titel, info),
      infoTekst,
      el("p", { class: "kort__beloeb" }, `${kr(tilstand.kroner === "aarets"
        ? k.netto_maaned / (v.aar.find((a) => a.alder === k.repraesentativ_alder)?.realfaktor ?? 1) : k.netto_maaned)} kr.`,
      el("small", { tekst: ` /md., ${kronerTekst()}` })),
      el("p", { class: "kort__periode", tekst: periode }),
      k.advarsler.length ? el("ul", { class: "advarsler", style: "margin:8px 0 0;padding:0;list-style:none" }, k.advarsler.map((a) => advarselEl(a))) : null,
      knap, tabel);
  }));
  $("#generelle-advarsler").replaceChildren(...(v.generelle_advarsler.length
    ? [el("h3", { tekst: "Værd at vide" }), el("ul", { class: "advarsler", style: "padding:0;list-style:none;margin:0" }, v.generelle_advarsler.map((a) => advarselEl(a)))]
    : []));
}

function tegnSaadan(v) {
  const kol = ["Alder", "Indkomst før skat", "Skat", "Efter skat pr. md.", "I dagens kr. pr. md.", "Indkomst, der nedsætter tillæg", "Tillægsprocent"];
  $("#aar-tabel").replaceChildren(el("table", {},
    el("thead", {}, el("tr", {}, kol.map((t) => el("th", { scope: "col", tekst: t })))),
    el("tbody", {}, v.aar.map((a) => el("tr", {}, el("th", { scope: "row", tekst: `${a.alder} år (${a.kalenderaar})` }),
      el("td", { tekst: `${kr(a.personlig_indkomst)} kr.` }), el("td", { tekst: `${kr(a.skat)} kr.` }),
      el("td", { tekst: `${kr(a.netto / 12)} kr.` }), el("td", { tekst: `${kr(a.netto_real / 12)} kr.` }),
      el("td", { tekst: `${kr(a.indtaegtsgrundlag)} kr.` }), el("td", { tekst: `${a.tillaegsprocent} %` }))))));
  // Feature 020: årets række åbner forklaringen af året.
  $$("#aar-tabel tbody th").forEach((th, i) => {
    const alder = v.aar[i].alder;
    const knap = el("button", { type: "button", class: "aar-tabel-knap", tekst: th.textContent, "aria-label": `Forklar året, hvor du er ${alder} år` });
    knap.addEventListener("click", () => { aabnPanel("graf", true); visAar(alder); });
    th.replaceChildren(knap);
  });

  const STATUS = { verificeret: ["✓", "status--ok", "Bekræftet i lov eller hos myndighed"], sekundaer: ["≈", "status--ca", "Fra en sekundær kilde"], uverificeret: ["!", "status--ca", "Ikke bekræftet"] };
  const vis = (s) => {
    if (s.vaerdi === null) return "tabel";
    if (s.enhed === "brok") return procent(s.vaerdi);
    if (s.enhed === "kr_aar") return `${kr(s.vaerdi)} kr.`;
    return decimal(s.vaerdi);
  };
  const navn = (id) => SATS_NAVNE[id] || (id.startsWith("kommune.") ? "Kommuneskat" : id.startsWith("kirkeskat.") ? "Kirkeskat" : id);
  $("#satser").replaceChildren(...v.satser.map((s) => {
    const [ikon, klasse, tekst] = STATUS[s.status];
    return el("li", {}, el("span", { class: `status ${klasse}`, title: tekst, tekst: ikon }),
      el("span", {}, el("strong", { tekst: `${navn(s.id)}: ` }), vis(s), el("span", { class: "sr-only", tekst: ` (${tekst})` })),
      el("small", { tekst: s.kilde }));
  }));
  $("#antagelser").replaceChildren(...Object.entries(ANTAGELSE_NAVNE).map(([k, [tekst, fmt]]) =>
    el("li", {}, el("span", { class: "status status--ca", tekst: "≈" }), el("span", {}, el("strong", { tekst: `${tekst}: ` }), fmt(v.antagelser[k])))));

  // Forenklingsregistret (feature 020): dem, der påvirker borgerens beregning, står først og siger det i tekst.
  const anvendte = v.forenklinger.filter((f) => f.anvendt).length;
  $("#forenklinger-titel").firstChild.textContent = anvendte
    ? `Se vores forenklinger (${anvendte === 1 ? "én" : anvendte} påvirker din beregning) ` : "Se vores forenklinger ";
  $("#forenklinger").replaceChildren(...v.forenklinger.map((f) => el("li", {},
    el("span", { class: `status ${f.anvendt ? "status--ca" : "status--info"}`, "aria-hidden": "true", tekst: f.anvendt ? "!" : "~" }),
    el("span", {}, el("strong", { tekst: f.anvendt ? `Påvirker din beregning: ${f.titel}. ` : `${f.titel}. ` }), `${f.beskrivelse} ${f.betydning}`),
    el("small", { tekst: `Hvorfor: ${f.begrundelse}` }))));
}

function tegnSkydere() {
  const s = tilstand.aktuelleSvar;
  const saet = (id, vaerdi, tekst) => { $(`#${id}`).value = vaerdi; $(`#${id}-v`).textContent = tekst; };
  saet("r-afkast", s.antagelser.afkast_efter_pal * 100, procent(s.antagelser.afkast_efter_pal));
  saet("r-inflation", s.antagelser.inflation * 100, procent(s.antagelser.inflation));
}

/* ── Feature 004: nøgletal, paneler og tidslinje ─────────────────────── */
const ENGANGSTYPER = new Set(["aldersopsparing", "kapitalpension"]);

function tegnNoegletal(v) {
  const s = aktivSvar();
  const opsparing = s.ordninger.reduce((sum, o) => sum + (o.saldo || 0), 0);
  const starter = s.ordninger.map((o) => o.udbetaling_start_alder).filter(Boolean);
  const engangs = v.kort.find((k) => k.noegle === "engangsbeloeb");
  const ops = s.antagelser.folkepension_opsaettelse_aar;
  const tal = [
    ["Folkepension fra", `${v.folkepensionsalder + ops} år`],
    ["Pensionsopsparing i dag", `${kr(opsparing)} kr.`],
    ["Første private udbetaling", starter.length ? `${Math.min(...starter)} år` : "–"],
    ["Engangsbeløb i alt", engangs ? `${kr(engangs.engangs.reduce((x, e) => x + e.netto_real, 0))} kr.` : "–"],
  ];
  $("#noegletal").replaceChildren(...tal.map(([dt, dd]) => el("div", {}, el("dt", { tekst: dt }), el("dd", { tekst: dd }))));
}

function aabnPanel(navn, aaben) {
  const knap = $(`#${navn}-panel-knap`);
  knap.setAttribute("aria-expanded", String(aaben));
  $(`#${navn}-panel-indhold`).hidden = !aaben;
  if (navn === "graf" && aaben) requestAnimationFrame(() => { tilstand.graf?.resize(); placerBjaelker(); });
}

function flytFormularTilPanel() {
  if (tilstand.panel) return;
  const form = $("#guide-form");
  form.classList.remove("guide__kort");
  form.classList.add("form--panel");
  $("#data-panel-form").append(form);
  $$(".trin", form).forEach((f) => (f.hidden = false));
  tilstand.panel = true;
  opdaterPartnerFelter();
}

function flytFormularTilGuide() {
  if (!tilstand.panel) return;
  const form = $("#guide-form");
  form.classList.add("guide__kort");
  form.classList.remove("form--panel");
  $("#guide > .ramme").append(form);
  tilstand.panel = false;
}

function synkroniserFormular() {
  // Tidslinjen ændrer start, periode og opsættelse — formularen viser altid det samme.
  const s = tilstand.aktuelleSvar;
  const pp = s.person?.partner?.profil;
  for (const o of [...tilstand.ordninger, ...tilstand.partnerOrdninger]) {
    const a = [...s.ordninger, ...(pp?.ordninger || [])].find((x) => x.id === o.id);
    if (a) {
      o.udbetaling_start_alder = a.udbetaling_start_alder;
      if (a.udbetaling_aar) o.udbetaling_aar = a.udbetaling_aar;
      if (a.udbetalingsform) o.udbetalingsform = a.udbetalingsform;
    }
  }
  if (pp) {
    $("#p-opsaettelse").value = pp.folkepension_opsaettelse_aar || 0;
    $("#p-opsaettelse-v").textContent = pp.folkepension_opsaettelse_aar ? `${pp.folkepension_opsaettelse_aar} år` : "Nej";
  }
  $("#opsaettelse").value = s.antagelser.folkepension_opsaettelse_aar;
  $("#opsaettelse-v").textContent = s.antagelser.folkepension_opsaettelse_aar ? `${s.antagelser.folkepension_opsaettelse_aar} år` : "Nej";
  $("#afkast").value = s.antagelser.afkast_efter_pal * 100;
  $("#afkast-v").textContent = procent(s.antagelser.afkast_efter_pal);
  $("#inflation").value = s.antagelser.inflation * 100;
  $("#inflation-v").textContent = procent(s.antagelser.inflation);
  $("#stop-alder").value = s.person.loen?.stop_alder ?? "";
  tegnOrdninger();
}

/* ── Forklaringer i tre niveauer (feature 020) ────────────────────────── */
// Kataloget (ord og pladsholdere) hentes én gang. Tallene kommer fra den aktuelle beregning, så en
// forklaring åbner uden et nyt kald til motoren. Niveauet huskes kun i denne browser.
const NIVEAUER = [["niveau1", "Kort fortalt"], ["niveau2", "Sådan regner vi"], ["niveau3", "For eksperter"]];

function gemtNiveau() {
  try { return localStorage.getItem("forklaringsniveau") || "niveau1"; } catch { return "niveau1"; }
}

function saetNiveau(n) {
  tilstand.niveau = n;
  try { localStorage.setItem("forklaringsniveau", n); } catch { /* kun en bekvemmelighed */ }
  tegnForklaringer();
  if (!$("#metode").hidden) tegnMetode();
}

async function hentForklaringer() {
  try { tilstand.forklaringer = await kald("forklaringer"); } catch { tilstand.forklaringer = null; }
  if (tilstand.v) tegnForklaringer();
}

const emne = (id) => tilstand.forklaringer?.emner.find((e) => e.id === id);
const udfyld = (tekst, vaerdier) => tekst.replace(/\{(\w+)\}/g, (_, k) => vaerdier[k] ?? "");

function niveauVaelger(rod) {
  const navn = `niveau-${rod.dataset.niveauvaelger}`;
  const n = tilstand.niveau ?? gemtNiveau();
  rod.replaceChildren(el("fieldset", {}, el("legend", { tekst: "Hvor meget vil du vide?" }),
    ...NIVEAUER.map(([id, tekst]) => {
      const input = el("input", { type: "radio", name: navn, value: id });
      input.checked = id === n;
      input.addEventListener("change", () => saetNiveau(id));
      return el("label", { class: "valg" }, input, ` ${tekst}`);
    })));
}

function tegnForklaringer() {
  if (!tilstand.forklaringer || !tilstand.v) return;
  tilstand.niveau ??= gemtNiveau();
  $$("[data-niveauvaelger]").forEach(niveauVaelger);
  tegnHovedtalForklaring();
  tegnLaesevejledninger();
  tegnKortforklaringer();
  tegnOrdliste();
  if (tilstand.forslagVist) $$("[data-optimering]").forEach((b) => tegnOptimeringForklaring(b, tilstand.forslagVist));
  if (tilstand.aarAlder !== undefined && !$("#aar-forklaring").hidden) tegnAar(tilstand.aarAlder);
}

/* ── Gem og genindlæs lokalt (feature 024) ─────────────────────────────── */
// Svarene krypteres i browseren med AES-GCM og en nøgle, der udledes af adgangskoden (PBKDF2-SHA-256).
// Filen indeholder kun format, version, salt, nonce og ciffertekst. Intet sendes ud (Princip VII).
const GEM = { format: "pensionsoverblik-gem", version: 1, iterationer: 600000, skema: 1 };

function tilB64(bytes) {
  let s = "";
  for (const b of new Uint8Array(bytes)) s += String.fromCharCode(b);
  return btoa(s);
}
const fraB64 = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));

async function gemNoegle(kode, salt, iterationer) {
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(kode), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({ name: "PBKDF2", hash: "SHA-256", salt, iterations: iterationer }, base,
    { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}

async function krypter(data, kode) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const noegle = await gemNoegle(kode, salt, GEM.iterationer);
  const ciffer = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, noegle, new TextEncoder().encode(JSON.stringify(data)));
  return { format: GEM.format, version: GEM.version, kdf: { navn: "PBKDF2-SHA-256", iterationer: GEM.iterationer, salt: tilB64(salt) },
    cipher: { navn: "AES-GCM", iv: tilB64(iv) }, data: tilB64(ciffer) };
}

async function dekrypter(fil, kode) {
  if (fil.format !== GEM.format || fil.version !== GEM.version) throw new Error("format");
  const noegle = await gemNoegle(kode, fraB64(fil.kdf.salt), fil.kdf.iterationer);
  const klar = await crypto.subtle.decrypt({ name: "AES-GCM", iv: fraB64(fil.cipher.iv) }, noegle, fraB64(fil.data));
  return JSON.parse(new TextDecoder().decode(klar));
}

// Guidens felter gemmes generelt (id → værdi), så nye felter kommer med uden ændring af formatet.
function guideFelter() {
  const felter = {};
  for (const i of $$("#guide-form input[id], #guide-form select[id]")) {
    if (i.type === "file" || i.type === "password") continue;
    felter[i.id] = i.type === "checkbox" ? i.checked : i.value;
  }
  for (const r of $$("#guide-form input[type=radio]:checked")) felter[`radio:${r.name}`] = r.value;
  return felter;
}

function saetGuideFelter(felter) {
  for (const [id, v] of Object.entries(felter)) {
    if (id.startsWith("radio:")) {
      const r = $(`#guide-form input[name="${id.slice(6)}"][value="${v}"]`);
      if (r) r.checked = true;
      continue;
    }
    const i = document.getElementById(id);
    if (!i) continue;
    if (i.type === "checkbox") i.checked = v; else i.value = v;
  }
}

async function gemTilSenere() {
  const status = $("#gem-status");
  ryd();
  const kode = $("#gem-kode").value;
  if (kode.length < 8) { visFejl("gem-kode", "Adgangskoden skal være mindst 8 tegn."); return; }
  if (kode !== $("#gem-kode2").value) { visFejl("gem-kode2", "De to adgangskoder er ikke ens."); return; }
  status.textContent = "Krypterer …";
  const data = {
    skema: GEM.skema, gemt: idag(), felter: guideFelter(),
    ordninger: tilstand.ordninger, partnerOrdninger: tilstand.partnerOrdninger,
    naesteId: tilstand.naesteId, naestePid: tilstand.naestePid,
    valg: { niveau: tilstand.niveau ?? null, kroner: tilstand.kroner ?? null },
  };
  const fil = await krypter(data, kode);
  const url = URL.createObjectURL(new Blob([JSON.stringify(fil)], { type: "application/json" }));
  const a = el("a", { href: url, download: `pensionsoverblik-gemt-${idag()}.json` });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("#gem-kode").value = $("#gem-kode2").value = "";
  status.textContent = "Filen er gemt i din browsers overførsler. Husk adgangskoden.";
}

async function aabnGemt() {
  const status = $("#gemt-status");
  ryd();
  const fil = $("#gemt-fil").files[0];
  if (!fil) { visFejl("gemt", "Vælg din gemte fil."); return; }
  status.textContent = "Åbner …";
  let data;
  try {
    data = await dekrypter(JSON.parse(await fil.text()), $("#gemt-kode").value);
  } catch {
    status.textContent = "";
    visFejl("gemt", "Filen kunne ikke åbnes. Tjek adgangskoden, og at det er en fil gemt her.");
    return;
  }
  if (data.skema !== GEM.skema) { status.textContent = ""; visFejl("gemt", "Filen er fra en version, vi ikke kan læse."); return; }
  saetGuideFelter(data.felter);
  tilstand.ordninger = data.ordninger || [];
  tilstand.partnerOrdninger = data.partnerOrdninger || [];
  tilstand.naesteId = data.naesteId || tilstand.naesteId;
  tilstand.naestePid = data.naestePid || tilstand.naestePid;
  if (data.valg?.niveau) saetNiveau(data.valg.niveau);
  if (data.valg?.kroner) { tilstand.kroner = data.valg.kroner; $$("input[name=kroner]").forEach((r) => (r.checked = r.value === tilstand.kroner)); }
  opdaterPartnerFelter();
  tegnOrdninger();
  $("#gemt-kode").value = "";
  status.textContent = "";
  await beregnFraGuide();
  if (!$("#resultat").hidden) {
    $("#hovedtal-aendring").textContent = `Din gemte beregning fra ${data.gemt}. Regnet med reglerne for i år, så tallene kan have ændret sig.`;
  }
}

/* ── Metodesiden, eksport og udskrift (feature 020d) ──────────────────── */
async function visMetode() {
  try { tilstand.metode ??= await kald("metode"); } catch { return; }
  $("#metode").hidden = false;
  tegnMetode();
  $("#metode-titel").focus();
  $("#metode").scrollIntoView?.({ block: "start" });
}

function tegnMetode() {
  const m = tilstand.metode;
  if (!m) return;
  tilstand.niveau ??= gemtNiveau();
  const n = tilstand.niveau;
  niveauVaelger($('[data-niveauvaelger="metode"]'));
  $("#metode-satsaar").textContent = m.satsaar;
  // Pladsholdere ({maaned} o.l.) udfyldes først ved borgerens egne tal; her står de som "…".
  $("#metode-emner").replaceChildren(...m.forklaringer.emner.map((e) => el("section", { class: "metode-emne" },
    el("h3", { tekst: e.titel }), ...afsnit(e[n].replace(/\{\w+\}/g, "…")))));
  $("#metode-forenklinger").replaceChildren(...m.forenklinger.map((f) => el("li", {},
    el("span", { class: "status status--info", "aria-hidden": "true", tekst: "~" }),
    el("span", {}, el("strong", { tekst: `${f.titel}. ` }), `${f.beskrivelse} ${f.betydning}`),
    el("small", { tekst: `Hvorfor: ${f.begrundelse} Kilde: ${f.kilde}.` }))));
  const STATUS = { verificeret: "Bekræftet i lov eller hos myndighed", sekundaer: "Fra en sekundær kilde", uverificeret: "Ikke bekræftet" };
  const vaerdi = (s) => (s.vaerdi === null ? "tabel" : s.enhed === "brok" ? procent(s.vaerdi) : s.enhed === "kr_aar" ? `${kr(s.vaerdi)} kr.` : decimal(s.vaerdi));
  $("#metode-satser").replaceChildren(tabel(`Satser og kilder for ${m.satsaar}`, ["Sats", "Værdi", "Status", "Kilde"],
    m.satser.map((s) => [SATS_NAVNE[s.id] || s.id, vaerdi(s), STATUS[s.status], s.kilde])));
}

async function hentEksport(slags) {
  const r = await kald("eksport", JSON.stringify(tilstand.aktuelleSvar), idag());
  if (!r.ok) { visFejl(r.fejl.felt, r.fejl.besked); return; }
  // CSV med BOM, så regneark læser æ, ø og å rigtigt. Intet sendes ud; filen laves i browseren.
  const [indhold, type, endelse] = slags === "json"
    ? [r.data.json, "application/json", "json"] : [`\ufeff${r.data.csv}`, "text/csv", "csv"];
  const url = URL.createObjectURL(new Blob([indhold], { type: `${type};charset=utf-8` }));
  const a = el("a", { href: url, download: `${r.data.filnavn}.${endelse}` });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// Udskrift: alle fold-ud'er åbnes, mens der udskrives, og lukkes igen bagefter.
let lukketFoerUdskrift = [];
window.addEventListener("beforeprint", () => {
  lukketFoerUdskrift = $$("#resultat details:not([open]), #metode details:not([open])");
  lukketFoerUdskrift.forEach((d) => (d.open = true));
});
window.addEventListener("afterprint", () => { lukketFoerUdskrift.forEach((d) => (d.open = false)); lukketFoerUdskrift = []; });

// "Sådan læser du …" (020b): emnets tekst på det valgte niveau. Grafen nævner kun det, der faktisk vises.
function tegnLaesevejledninger() {
  const n = tilstand.niveau;
  const v = tilstand.v;
  for (const d of $$("[data-laes]")) {
    const e = tilstand.forklaringer.emner.find((x) => (x.visninger || []).includes(d.dataset.laes));
    if (!e) continue;
    $("summary", d).textContent = e.titel;
    const tekster = [e[n]];
    if (d.dataset.laes === "graf") {
      const vist = [...v.graf.serier.map((s) => s.titel), ...(v.graf.jaevn ? [JAEVN_NAVN] : []),
        ...(v.graf.engangs.length ? ["mærker for engangsbeløb"] : []), ...(v.graf.markeringer.length ? ["felter for år med en advarsel"] : [])];
      tekster.push(`I din graf: ${vist.join(", ")}.`);
    }
    if (d.dataset.laes === "beloeb") {
      const a = v.aar.at(-1);
      tekster.push(`Eksempel fra din beregning: ${kr(a.netto / 12)} kr. om måneden i ${a.kalenderaar} svarer til ${kr(a.netto_real / 12)} kr. i dagens kroner.`);
    }
    $(".laes__tekst", d).replaceChildren(...afsnit(...tekster));
  }
}

function tegnKortforklaringer() {
  const n = tilstand.niveau;
  for (const boks of $$("[data-kort-forklaring]")) {
    const emner = tilstand.forklaringer.emner.filter((e) => (e.kort || []).includes(boks.dataset.kortForklaring));
    if (emner.length) boks.replaceChildren(...afsnit(...emner.map((e) => (emner.length > 1 ? `${e.titel}: ${e[n]}` : e[n]))));
  }
}

function tegnOrdliste() {
  const n = tilstand.niveau;
  $("#ordliste").replaceChildren(...tilstand.forklaringer.ordliste.flatMap((o) => [el("dt", { tekst: o.ord }), el("dd", { tekst: o[n] })]));
}

function afsnit(...tekster) { return tekster.filter(Boolean).map((t) => el("p", { tekst: t })); }

function tabel(caption, hoved, raekker) {
  return el("div", { class: "tabel-rul" }, el("table", {}, el("caption", { class: "sr-only", tekst: caption }),
    el("thead", {}, el("tr", {}, ...hoved.map((h) => el("th", { scope: "col", tekst: h })))),
    el("tbody", {}, raekker.map(([th, ...td]) => el("tr", {}, el("th", { scope: "row", tekst: th }), ...td.map((x) => el("td", { tekst: x })))))));
}

function tegnHovedtalForklaring() {
  const boks = $("#hovedtal-forklaring-tekst");
  const n = tilstand.niveau;
  if (tilstand.hvem === "samlet") {
    boks.replaceChildren(...afsnit(emne("husstand")[n]));
    return;
  }
  const v = tilstand.v;
  const h = v.hovedtal;
  const e = emne("fast_beloeb");
  const dele = h.forklaring.drivere.map((d) => `${d.titel} ca. ${kr(d.maaned)} kr.`).join(", ");
  const tekst = [udfyld(e.niveau1, { maaned: kr(h.maaned), fra_alder: h.fra_alder })];
  if (n === "niveau1") tekst.push(dele ? `Det største bidrag i gennemsnit om måneden: ${dele}.` : "");
  if (n !== "niveau1") tekst.push(e.niveau2);
  if (h.senere) tekst.push(`Fra ${h.senere.fra_alder} år stiger beløbet til ca. ${kr(h.senere.maaned)} kr.`);
  if (n === "niveau3") {
    tekst.push(e.niveau3, `Afkast ${procent(v.antagelser.afkast_efter_pal)} efter PAL-skat og inflation ${procent(v.antagelser.inflation)}. `
      + `Opsparingens renter, skat og formue blev regnet igennem ${h.forklaring.iterationer} ${h.forklaring.iterationer === 1 ? "gang" : "gange"}.`);
  }
  boks.replaceChildren(...afsnit(...tekst));
}

function visAar(alder) {
  tilstand.aarAlder = alder;
  $("#aar-forklaring").hidden = false;
  tegnForklaringer();
  tegnAar(alder);
  $("#aar-forklaring-titel").focus();
}

function tegnAar(alder) {
  const v = tilstand.v;
  const a = v.aar.find((x) => x.alder === alder);
  if (!a || !tilstand.forklaringer) return;
  const n = tilstand.niveau;
  const e = emne("aar");
  const md = (x) => `${kr(x * a.realfaktor / 12)} kr.`;      // om måneden i dagens kroner
  const aar = (x) => `${kr(x)} kr.`;                         // om året i årets kroner
  $("#aar-forklaring-titel").textContent = `Dit år ${a.kalenderaar} (du er ${a.alder})`;
  const navne = [...new Set(a.kilder.map((k) => k.titel.toLowerCase()))];
  const indhold = [];
  const intro = [udfyld(e.niveau1, { kalenderaar: a.kalenderaar, alder: a.alder, netto: kr(a.netto_real / 12),
    kilder: navne.length ? navne.join(", ") : "ingen indkomst" })];
  if (a.aendring) {
    intro.push(`Det er ${a.aendring.maaned > 0 ? "mere" : "mindre"} end året før. Den største ændring er ${a.aendring.titel.toLowerCase()}, `
      + `der ${a.aendring.maaned > 0 ? "stiger" : "falder"} med ca. ${kr(Math.abs(a.aendring.maaned))} kr. om måneden.`);
  }
  if (a.fra_opsparing > 1) intro.push(`Du bruger ca. ${md(a.fra_opsparing)} om måneden af din opsparing for at holde det faste beløb.`);
  if (a.til_opsparing > 1) intro.push(`Du sparer ca. ${md(a.til_opsparing)} om måneden op til senere år.`);
  indhold.push(...afsnit(...intro));

  const d = a.detaljer;
  if (n !== "niveau1" && d) {
    indhold.push(...afsnit(e.niveau2, "Beløbene herunder er for hele året, i årets kroner."));
    const sumBrutto = a.kilder.reduce((s, k) => s + k.brutto, 0);
    indhold.push(tabel("Årets indkomster før og efter skat", ["Indkomst", "Før skat", "Skat", "Efter skat"], [
      ...a.kilder.map((k) => [k.titel, aar(k.brutto), aar(k.skat), aar(k.netto)]),
      ["I alt", aar(sumBrutto), aar(a.skat), aar(a.netto)],
    ]));
    const linjer = [];
    if (d.pensionsindbetaling > 0) linjer.push(`Pensionsindbetaling trukket fra lønnen før skat: ${aar(d.pensionsindbetaling)}.`);
    if (d.am_bidrag > 0) linjer.push(`Heraf AM-bidrag: ${aar(d.am_bidrag)}.`);
    if (d.pensionstillaeg_foer_modregning > 0) {
      const udbetalt = a.kilder.find((k) => k.type === "pensionstillaeg")?.brutto ?? 0;
      linjer.push(`Pensionstillæg før modregning ${aar(d.pensionstillaeg_foer_modregning)}. Din anden indkomst (indtægtsgrundlaget) er ${aar(a.indtaegtsgrundlag)}, `
        + `så tillægget nedsættes med ${aar(d.pensionstillaeg_foer_modregning - udbetalt)} til ${aar(udbetalt)}.`);
    }
    if (d.formue_primo !== null) {
      const check = a.kilder.some((k) => k.type === "aeldrecheck");
      linjer.push(`Ældrecheck: din formue pr. 1. januar er ${aar(d.formue_primo)}, og grænsen er ${aar(d.formuegraense)}. `
        + (d.formue_primo > d.formuegraense ? "Formuen er over grænsen, så du får ingen ældrecheck."
          : check ? `Din tillægsprocent er ${a.tillaegsprocent} %, og du får ældrecheck.` : `Din tillægsprocent er ${a.tillaegsprocent} %, så du får ingen ældrecheck.`));
    }
    if (a.skat_kapitalindkomst > 0) linjer.push(`Afkastet af din opsparing er ${aar(a.kapitalindkomst)}. Skatten af det, ${aar(a.skat_kapitalindkomst)}, betales af opsparingen.`);
    indhold.push(...afsnit(...linjer));
  }
  if (n === "niveau3" && d) {
    const s = d.skat;
    indhold.push(...afsnit(e.niveau3));
    const typer = [["Bundskat", s.bundskat], ["Kommuneskat", s.kommuneskat], ["Kirkeskat", s.kirkeskat], ["Mellemskat", s.mellemskat],
      ["Topskat", s.topskat], ["Toptopskat", s.toptopskat], ["Nedslag for skatteloftet", -s.skatteloft_nedslag],
      ["Nedsættelse fra ægtefælle", -s.aegtefaelle_nedsaettelse], ["AM-bidrag", d.am_bidrag]].filter(([, x]) => Math.abs(x) >= 0.5);
    indhold.push(tabel("Årets skat pr. type", ["Skattetype", "Beløb"], [
      ...typer.map(([t, x]) => [t, aar(x)]),
      ["I alt (inkl. skat af kapitalindkomst)", aar(a.skat + a.skat_kapitalindkomst)],
    ]));
    indhold.push(...afsnit(
      d.ligningsmaessige_fradrag > 0 ? `Ligningsmæssige fradrag (kun kommune- og kirkeskat): ${aar(d.ligningsmaessige_fradrag)}.` : "",
      `Realfaktor ${String(a.realfaktor.toFixed(4)).replace(".", ",")}: årets kroner gange realfaktoren giver dagens kroner.`,
      `Registerposter brugt i året: ${a.sporing.filter((id) => !id.startsWith("antagelse.")).map((id) => SATS_NAVNE[id] || id).join(", ")}.`));
  }
  $("#aar-forklaring-tekst").replaceChildren(...indhold);
}

/* ── "Hvornår kan jeg stoppe?" (feature 017, US3) ─────────────────────── */
async function findStopalder() {
  const svar = $("#stop-svar");
  const oenske = beloeb($("#oenske").value);
  if (!tilstand.aktuelleSvar.person.loen?.aarlig) {
    svar.replaceChildren(el("p", { tekst: "Skriv din løn under \"Dine oplysninger\", så kan vi finde ud af, hvornår du kan stoppe." }));
    return;
  }
  if (!oenske) { svar.replaceChildren(el("p", { tekst: "Skriv, hvor meget du vil have om måneden." })); return; }
  const knap = $("#stop-knap");
  knap.disabled = true;
  svar.replaceChildren(el("p", { tekst: "Vi afprøver hver alder …" }));
  try {
    const r = await kald("stopalder", JSON.stringify(tilstand.aktuelleSvar), idag(), oenske);
    if (!r.ok) { svar.replaceChildren(el("p", { tekst: r.fejl.besked })); return; }
    const d = r.data;
    const omfang = el("p", { class: "felt__hjaelp", tekst: `Vi har afprøvet alle ${d.afproevet} aldre fra ${d.fra} til ${d.til} år med din nuværende plan. Efter skat og i dagens kroner.` });
    const alder = d.kunne ? d.alder : d.bedste.alder;
    const brug = el("button", { type: "button", class: "knap knap--sekundaer", tekst: `Brug ${alder} år` });
    brug.addEventListener("click", () => {
      tilstand.aktuelleSvar.person.loen = { ...tilstand.aktuelleSvar.person.loen, stop_alder: alder };
      synkroniserFormular();
      genberegn();
    });
    svar.replaceChildren(
      el("p", { class: "forslag__resultat", tekst: d.kunne
        ? `Du kan stoppe som ${d.alder}-årig og få ca. ${kr(d.maaned)} kr. om måneden.`
        : `Det når du ikke før folkepensionen. Mest får du ved at stoppe som ${d.bedste.alder}-årig: ca. ${kr(d.bedste.maaned)} kr. om måneden.` }),
      omfang, brug);
  } catch {
    svar.replaceChildren(el("p", { tekst: "Det kunne ikke regnes lige nu. Prøv igen." }));
  } finally {
    knap.disabled = false;
  }
}

async function opdaterFraPanel() {
  ryd();
  if (!validerTrin(1) || !validerTrin(2) || !validerTrin(3)) return;
  const status = $("#opdater-status");
  status.textContent = "Regner …";
  try {
    const svar = guideSvar();
    const { fejl, visning } = await hentBeregning(svar);
    if (fejl) { status.textContent = ""; visFejl(fejl.felt, fejl.besked); return; }
    tilstand.forrigeHovedtal = +$("#hovedtal").dataset.vaerdi;
    tilstand.mineSvar = structuredClone(svar);
    tilstand.aktuelleSvar = structuredClone(svar);
    tilstand.sidsteGyldige = structuredClone(svar);
    visResultat(visning, false);
    status.textContent = "Beregningen er opdateret.";
  } catch {
    status.textContent = "Beregningen kunne ikke gennemføres lige nu.";
  }
}

function aktivSvar() {
  // Svarene for den person, resultatsiden viser: dine eller — under fanen "Partner" — partnerens
  // ordninger og opsættelse (afkast og inflation er fælles). Ændringer skrives ind i husstandens svar.
  const s = tilstand.aktuelleSvar;
  const pp = s?.person?.partner?.profil;
  if (tilstand.hvem !== "partner" || !pp) return s;
  return { ordninger: pp.ordninger, antagelser: {
    get afkast_efter_pal() { return s.antagelser.afkast_efter_pal; },
    get inflation() { return s.antagelser.inflation; },
    get folkepension_opsaettelse_aar() { return pp.folkepension_opsaettelse_aar || 0; },
    set folkepension_opsaettelse_aar(n) { pp.folkepension_opsaettelse_aar = n; },
  } };
}

function ordningstitel(o) {
  const g = [...tilstand.ordninger, ...tilstand.partnerOrdninger].find((x) => x.id === o.id);
  const selskab = g?.kilde ? g.kilde.split(" · ")[0] : null;
  return selskab ? `${selskab} · ${TYPER[o.type].titel}` : TYPER[o.type].titel;
}

/* ── Feature 006: bjælker, der trækkes ───────────────────────────────── */
/* Bjælken (eller punktet) er selv kontrollen: træk med mus/finger, klik for ‹ ›, eller brug
   tastaturet. Alle tre veje går gennem saetVaerdi, og kernen regner, når ændringen er færdig. */

function tidslinjeRaekker(v) {
  // Én beskrivelse pr. række og kontrol: hvad den ændrer, grænser (fra kernen og registret) og tekst.
  const s = aktivSvar();
  const g = v.graenser;
  const aldre = v.graf.aldre;
  const raekker = s.ordninger.map((o) => {
    const titel = ordningstitel(o);
    // Kapitalpension (009): portioner og omlægning vises som bjælke; kun ét beløb er et punkt.
    const form = o.type === "kapitalpension" ? (o.udbetalingsform || "engangs") : null;
    const engang = ENGANGSTYPER.has(o.type) && (form === null || form === "engangs");
    const tidligste = Math.ceil(g.ordninger[o.id]?.tidligste ?? aldre[0]);
    const seneste = g.ordninger[o.id]?.seneste;
    const kontroller = {
      start: { navn: engang ? "Udbetales som" : "Start", label: `${titel}, ${engang ? "udbetales som" : "start"}`,
        ned: "Start 1 år tidligere", op: "Start 1 år senere", min: tidligste,
        get maks() {
          if (form === "engangs") return seneste;
          if (form === "portioner") return Math.max(tidligste, seneste - (o.udbetaling_aar || 2) + 1);
          return Math.max(tidligste, aldre.at(-1));
        },
        hent: () => o.udbetaling_start_alder, saet: (n) => { o.udbetaling_start_alder = n; }, tekst: (n) => `${n} år` },
    };
    if (o.type === "ratepension" || form === "ratepension") {
      kontroller.varighed = { navn: "Varighed", label: `${titel}, varighed`, ned: "Varighed 1 år kortere", op: "Varighed 1 år længere",
        min: g.ratepension_aar.min, maks: g.ratepension_aar.maks,
        hent: () => o.udbetaling_aar || g.ratepension_aar.min, saet: (n) => { o.udbetaling_aar = n; }, tekst: (n) => `${n} år` };
    }
    if (form === "portioner") {
      kontroller.varighed = { navn: "Portioner", label: `${titel}, antal portioner`, ned: "Portioner 1 færre", op: "Portioner 1 flere",
        min: 2, get maks() { return Math.max(2, seneste - o.udbetaling_start_alder + 1); },
        hent: () => o.udbetaling_aar || 2, saet: (n) => { o.udbetaling_aar = n; }, tekst: (n) => `${n} portioner` };
    }
    const iBuffer = ENGANGSTYPER.has(o.type) && !["ratepension", "livsvarig"].includes(form);
    return { id: o.id, type: o.type, titel, farve: TYPER[o.type].farve, engang, form,
      direkte: iBuffer && o.i_buffer === false, kontroller };
  });
  raekker.push({ id: "folkepension", type: "folkepension", titel: "Folkepension", farve: "--kilde-folkepension", engang: false,
    kontroller: { start: { navn: "Udskyd", label: "Folkepension, udskydelse", ned: "Udskyd 1 år mindre", op: "Udskyd 1 år mere",
      min: 0, maks: g.opsaettelse_maks,
      hent: () => s.antagelser.folkepension_opsaettelse_aar, saet: (n) => { s.antagelser.folkepension_opsaettelse_aar = n; },
      tekst: (n) => (n ? `${n} år (fra ${g.folkepensionsalder + n} år)` : `nej (fra ${g.folkepensionsalder} år)`) } } });
  return raekker;
}

function spaend(r, v) {
  // Første og sidste udbetalingsalder for rækkens bjælke, ud fra borgerens aktuelle valg.
  const sidste = v.graf.aldre.at(-1);
  const start = r.kontroller.start.hent();
  if (r.id === "folkepension") return [v.graenser.folkepensionsalder + start, sidste];
  if (r.kontroller.varighed) return [start, start + r.kontroller.varighed.hent() - 1];
  return r.engang ? [start, start] : [start, sidste];
}

function periodeTekst(r, v) {
  const [fra, til] = spaend(r, v);
  const hvor = r.direkte ? "udbetales direkte" : "til buffer";
  if (r.form === "portioner") return `${fra}–${til} år · ${r.kontroller.varighed.hent()} portioner · ${hvor}`;
  if (r.form === "ratepension") return `${fra}–${til} år · omlagt til ratepension`;
  if (r.form === "livsvarig") return `fra ${fra} år, livsvarig · omlagt til livrente`;
  if (r.kontroller.varighed) return `${fra}–${til} år`;
  if (r.engang) return `${fra} år · ${hvor}`;
  return `fra ${fra} år, livsvarig`;
}

function tegnTidslinje(v) {
  if (!v) return;
  const fokus = document.activeElement?.dataset?.kontrol;  // bevar fokus, når rækkerne tegnes igen
  tilstand.tlRaekker = tidslinjeRaekker(v);
  const raekker = tilstand.tlRaekker.map((r) => {
    const bjaelke = el("div", { class: `tl-bjaelke${r.engang ? " tl-bjaelke--engang" : ""}${r.direkte ? " tl-bjaelke--direkte" : ""}`, style: `--farve: var(${r.farve})`,
      role: "slider", tabindex: "0", "data-kontrol": `${r.id}:start` });
    const greb = r.kontroller.varighed
      ? el("div", { class: "tl-greb", style: `--farve: var(${r.farve})`, role: "slider", tabindex: "0", "data-kontrol": `${r.id}:varighed` })
      : null;
    forbindKontrol(bjaelke, r, r.kontroller.start);
    if (greb) forbindKontrol(greb, r, r.kontroller.varighed);
    const trin = Object.entries(r.kontroller).map(([noegle, k]) => {
      const knap = (retning) => {
        const b = el("button", { type: "button", class: "tl-trinknap", "aria-label": retning < 0 ? k.ned : k.op,
          "data-kontrol": `${r.id}:${noegle}:${retning}`, tekst: retning < 0 ? "‹" : "›" });
        b.addEventListener("click", () => saetVaerdi(r, k, k.hent() + retning, true));
        return b;
      };
      return el("div", { class: "tl-trin__gruppe", "data-noegle": noegle },
        el("span", { class: "tl-trin__navn", tekst: k.navn }), knap(-1), el("output", { class: "tl-trin__vaerdi" }), knap(1));
    });
    return el("div", { class: "tl-raekke", "data-id": r.id, "data-type": r.type },
      el("div", { class: "tl-hoved" }, el("strong", { tekst: r.titel }), el("span", { class: "tl-periode" })),
      el("div", { class: "tl-spor" }, bjaelke, greb),
      el("div", { class: "tl-trin", hidden: tilstand.valgtRaekke !== r.id }, trin));
  });
  $("#tidslinje").replaceChildren(...raekker);
  tilstand.tlRaekker.forEach((r) => opdaterRaekke(r));
  placerBjaelker();
  if (fokus) $(`[data-kontrol="${fokus}"]`)?.focus();
}

function opdaterRaekke(r) {
  // Tekst, ARIA og knapper følger borgerens valg med det samme — tallene kommer fra kernen bagefter.
  const raekke = $(`.tl-raekke[data-id="${r.id}"]`);
  if (!raekke) return;
  $(".tl-periode", raekke).textContent = periodeTekst(r, tilstand.v);
  for (const [noegle, k] of Object.entries(r.kontroller)) {
    const n = k.hent();
    const kontrol = $(`[data-kontrol="${r.id}:${noegle}"]`, raekke);
    kontrol.setAttribute("aria-label", k.label);
    kontrol.setAttribute("aria-valuemin", k.min);
    kontrol.setAttribute("aria-valuemax", k.maks);
    kontrol.setAttribute("aria-valuenow", n);
    kontrol.setAttribute("aria-valuetext", k.tekst(n));
    const gruppe = $(`.tl-trin__gruppe[data-noegle="${noegle}"]`, raekke);
    $(".tl-trin__vaerdi", gruppe).textContent = k.tekst(n);
    $(`[data-kontrol="${r.id}:${noegle}:-1"]`, gruppe).disabled = n <= k.min;
    $(`[data-kontrol="${r.id}:${noegle}:1"]`, gruppe).disabled = n >= k.maks;
  }
}

function saetVaerdi(r, k, ny, regn) {
  const n = Math.min(k.maks, Math.max(k.min, Math.round(ny)));
  if (n === k.hent()) return false;
  if (tilstand.forslag) fjernForslag();
  k.saet(n);
  synkroniserFormular();
  opdaterRaekke(r);
  placerBjaelker();
  if (regn) genberegn(r.id);
  return true;
}

function vaelgRaekke(id) {
  tilstand.valgtRaekke = tilstand.valgtRaekke === id ? null : id;
  $$(".tl-raekke").forEach((raekke) => { $(".tl-trin", raekke).hidden = raekke.dataset.id !== tilstand.valgtRaekke; });
}

const TASTER = { ArrowLeft: -1, ArrowDown: -1, ArrowRight: 1, ArrowUp: 1, PageDown: -5, PageUp: 5 };

function forbindKontrol(kontrol, r, k) {
  kontrol.addEventListener("keydown", (e) => {
    let ny;
    if (e.key in TASTER) ny = k.hent() + TASTER[e.key];
    else if (e.key === "Home") ny = k.min;
    else if (e.key === "End") ny = k.maks;
    else return;
    e.preventDefault();
    saetVaerdi(r, k, ny, true);
  });
  kontrol.addEventListener("pointerdown", (e) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    kontrol.setPointerCapture(e.pointerId);
    const x0 = e.clientX;
    const v0 = k.hent();
    let traekker = false;
    const flyt = (m) => {
      const dx = m.clientX - x0;
      if (!traekker && Math.abs(dx) < 4) return;  // under 4 px er et klik
      traekker = true;
      kontrol.classList.add("tl-aktiv");
      saetVaerdi(r, k, v0 + Math.round(dx / tilstand.prAar), false);
    };
    const slip = () => {
      kontrol.removeEventListener("pointermove", flyt);
      kontrol.removeEventListener("pointerup", slip);
      kontrol.removeEventListener("pointercancel", slip);
      kontrol.classList.remove("tl-aktiv");
      if (!traekker) vaelgRaekke(r.id);
      else if (k.hent() !== v0) genberegn(r.id);
    };
    kontrol.addEventListener("pointermove", flyt);
    kontrol.addEventListener("pointerup", slip);
    kontrol.addEventListener("pointercancel", slip);
  });
}

/* ── Feature 007: find bedste plan ─────────────────────────────────────── */
/* Kernen afprøver kombinationer i workeren og foreslår det højeste faste beløb hele perioden.
   Forslaget vises med spøgelsesbjælker og ændres først, når borgeren trykker "Anvend". */
const svarNoegle = () => JSON.stringify(tilstand.aktuelleSvar);
const stortTal = (n) => (n >= 1e6 ? `${String(+(n / 1e6).toFixed(1)).replace(".", ",")} mio.` : kr(n));

function fjernForslag() {
  tilstand.forslag = null;
  const boks = $("#forslag");
  boks.hidden = true;
  boks.replaceChildren();
  $$(".tl-spoegelse").forEach((e) => e.remove());
}

async function findBedstePlan() {
  fjernForslag();
  const knap = $("#optimer-knap");
  const noegle = svarNoegle();
  const boks = $("#forslag");
  const fremdrift = el("progress", { max: 1, value: 0, "aria-label": "Afprøver kombinationer" });
  // Søgningen kan tage over 10 sekunder med mange ordninger: borgeren skal kunne afbryde den.
  // Kernen kører i workeren og kan ikke stoppes midtvejs, så workeren genstartes; planen er uændret.
  const afbryd = el("button", { type: "button", class: "knap knap--tekst", id: "optimer-afbryd", tekst: "Afbryd" });
  let afbrudt = false;
  afbryd.addEventListener("click", () => {
    afbrudt = true;
    startMotor();
    hentKommuner();
    fjernForslag();
    knap.disabled = false;
    knap.focus();
  });
  boks.replaceChildren(el("p", { tekst: "Afprøver kombinationer …" }), fremdrift, afbryd);
  boks.hidden = false;
  knap.disabled = true;
  try {
    const hvem = tilstand.hvem === "partner" ? "partner" : "dig";
    const r = await kaldMedFremdrift("optimer", [noegle, idag(), hvem], (andel) => { fremdrift.value = andel; });
    if (afbrudt || svarNoegle() !== noegle) return;  // afbrudt, eller planen er ændret, mens vi søgte
    if (!r.ok) { boks.replaceChildren(el("p", { class: "forslag__resultat", tekst: r.fejl.besked })); return; }
    visForslag(r.data, noegle);
  } catch {
    if (afbrudt) return;
    boks.replaceChildren(el("p", { class: "forslag__resultat", tekst: "Vi kunne ikke søge efter en bedre plan lige nu. Prøv igen." }));
  } finally {
    if (!afbrudt) knap.disabled = false;
  }
}

const FORM_TEKST = {
  engangs: () => "ét beløb",
  portioner: (aar) => `i portioner over ${aar} år`,
  ratepension: (aar) => `ratepension over ${aar} år`,
  livsvarig: () => "livrente",
};

function aendringTekst(a, engang) {
  if (a.felt === "form") return `${FORM_TEKST[a.fra.form](a.fra.aar)} → ${FORM_TEKST[a.til.form](a.til.aar)}`;
  if (a.felt === "varighed") return `varighed ${a.fra} → ${a.til} år`;
  if (a.felt === "opsaettelse") return `udskyd ${a.fra} → ${a.til} år`;
  return `${engang ? "udbetales som" : "start"} ${a.fra} → ${a.til} år`;
}

function visForslag(d, noegle) {
  const afproevet = d.udtoemmende
    ? `Vi har afprøvet alle ${kr(d.mulige)} mulige kombinationer.`
    : `Vi har afprøvet ${kr(d.evalueret)} af ${stortTal(d.mulige)} mulige kombinationer – de mest lovende, men ikke alle.`;
  const boks = $("#forslag");
  tilstand.forslagVist = d;
  if (!d.forbedret) {
    boks.replaceChildren(
      el("p", { class: "forslag__resultat", tekst: "Din plan er allerede den bedste, vi kan finde." }),
      el("p", { class: "felt__hjaelp", tekst: afproevet }),
      optimeringForklaring(d));
    return;
  }
  const pr = new Map();
  for (const a of d.aendringer) pr.set(a.id, [...(pr.get(a.id) || []), a]);
  const linjer = [...pr].map(([id, aendringer]) => {
    const o = aktivSvar().ordninger.find((x) => x.id === id);
    const titel = o ? ordningstitel(o) : "Folkepension";
    return el("li", {}, el("strong", { tekst: `${titel}: ` }), aendringer.map((a) => aendringTekst(a, o && ENGANGSTYPER.has(o.type))).join(", "));
  });
  const anvend = el("button", { type: "button", class: "knap knap--primaer", tekst: "Anvend" });
  const behold = el("button", { type: "button", class: "knap knap--tekst", tekst: "Behold min plan" });
  anvend.addEventListener("click", anvendForslag);
  behold.addEventListener("click", fjernForslag);
  boks.replaceChildren(
    el("h3", { class: "forslag__resultat", tekst: `Forslag: ${kr(d.efter - d.foer)} kr. mere om måneden` }),
    el("p", { tekst: `Fast beløb hele perioden: ${kr(d.efter)} kr. i stedet for ${kr(d.foer)} kr. Efter skat og i dagens kroner. De stiplede bjælker viser forslaget.` }),
    el("ul", { class: "forslag__liste" }, linjer),
    el("p", { class: "felt__hjaelp", tekst: afproevet }),
    el("p", { class: "felt__hjaelp forslag__forbehold", tekst: emne("forbehold")?.niveau1 ?? "" }),
    optimeringForklaring(d),
    el("div", { class: "forslag__knapper" }, anvend, behold));
  tilstand.forslag = { d, noegle };
  placerBjaelker();
}

// Feature 020c: sådan har vi fundet forslaget, på det valgte niveau, med søgningens omfang (Princip V).
function optimeringForklaring(d) {
  const boks = el("details", { class: "laes", "data-optimering": "" },
    el("summary", { tekst: "Sådan har vi fundet forslaget" }), el("div", { class: "laes__tekst" }));
  tegnOptimeringForklaring(boks, d);
  return boks;
}

function tegnOptimeringForklaring(boks, d) {
  const e = emne("optimering");
  if (!e) return;
  const n = tilstand.niveau ?? gemtNiveau();
  const tekster = [e[n]];
  if (d.forbedret) tekster.push(`Det bedste, vi fandt, giver ${kr(d.efter)} kr. om måneden i stedet for ${kr(d.foer)} kr.`);
  if (n !== "niveau1") tekster.push("Målet er det højeste faste beløb hele perioden. Et forslag må ikke give nye år uden indkomst.");
  if (n === "niveau3") {
    tekster.push(`Søgerum: startalder, varighed, udbetalingsform og opsættelse af folkepensionen inden for lovens grænser. `
      + `Afprøvet: ${kr(d.evalueret)} af ${kr(d.mulige)} mulige kombinationer (${d.udtoemmende ? "alle" : "ikke alle"}). `
      + "Søgningen er deterministisk: samme input giver samme forslag.");
  }
  tekster.push(emne("forbehold")[n]);
  $(".laes__tekst", boks).replaceChildren(...afsnit(...tekster));
}

function anvendForslag() {
  const { d } = tilstand.forslag;
  const s = aktivSvar();
  for (const [id, felter] of Object.entries(d.plan.ordninger)) Object.assign(s.ordninger.find((o) => o.id === id), felter);
  s.antagelser.folkepension_opsaettelse_aar = d.plan.folkepension_opsaettelse_aar;
  fjernForslag();
  synkroniserFormular();
  tegnTidslinje(tilstand.v);
  genberegn();
  $("#hovedtal").scrollIntoView?.({ block: "center" });
}

function forslagSpaend(r, v, plan) {
  // Forslagets første og sidste alder for rækken — null, hvis forslaget ikke ændrer den.
  const sidste = v.graf.aldre.at(-1);
  if (r.id === "folkepension") {
    const ops = plan.folkepension_opsaettelse_aar;
    return ops === r.kontroller.start.hent() ? null : [v.graenser.folkepensionsalder + ops, sidste];
  }
  const p = plan.ordninger[r.id];
  if (!p) return null;
  const start = p.udbetaling_start_alder;
  const form = p.udbetalingsform ?? r.form;
  const aar = p.udbetaling_aar ?? r.kontroller.varighed?.hent();
  if (start === r.kontroller.start.hent() && aar === r.kontroller.varighed?.hent() && form === r.form) return null;
  if (form === "portioner" || form === "ratepension" || (!form && r.kontroller.varighed)) return [start, start + aar - 1];
  if (form === "engangs" || (!form && r.engang)) return [start, start];
  return [start, sidste];
}

const PUNKT_PX = 24;  // engangsbeløb og greb: mindst 24×24 px (WCAG 2.5.8)

function placerBjaelker() {
  // Bjælkerne følger grafens aldersakse: samme første/sidste år og samme pixel pr. år.
  const v = tilstand.v;
  if (!v || !tilstand.tlRaekker) return;
  const aldre = v.graf.aldre;
  const graf = tilstand.graf;
  const spor = $(".tl-spor");
  if (!spor) return;
  const bredde = spor.getBoundingClientRect().width;
  let x0, prAar;
  if (graf?.scales?.x && aldre.length > 1) {
    const ramme = graf.canvas.getBoundingClientRect();
    const forskydning = ramme.left - spor.getBoundingClientRect().left;
    prAar = (graf.scales.x.getPixelForValue(aldre.length - 1) - graf.scales.x.getPixelForValue(0)) / (aldre.length - 1);
    x0 = forskydning + graf.scales.x.getPixelForValue(0) - prAar / 2;
  } else {
    prAar = bredde / aldre.length;
    x0 = 0;
  }
  tilstand.prAar = prAar;
  const placer = (e, start, slut, engang) => {
    const fra = Math.max(start, aldre[0]) - aldre[0];
    const til = Math.min(slut, aldre.at(-1)) - aldre[0] + 1;
    if (engang) {
      e.style.left = `${x0 + (fra + 0.5) * prAar - PUNKT_PX / 2}px`;
      e.style.width = "";
    } else {
      e.style.left = `${x0 + fra * prAar}px`;
      e.style.width = `${Math.max(PUNKT_PX, (til - fra) * prAar)}px`;
    }
    return til;
  };
  tilstand.tlRaekker.forEach((r) => {
    const raekke = $(`.tl-raekke[data-id="${r.id}"]`);
    if (!raekke) return;
    const b = $(".tl-bjaelke", raekke);
    const [start, slut] = spaend(r, v);
    b.dataset.start = start;
    b.dataset.slut = slut;
    const til = placer(b, start, slut, r.engang);
    const greb = $(".tl-greb", raekke);
    if (greb) greb.style.left = `${x0 + til * prAar - PUNKT_PX / 2}px`;
    // Spøgelse: forslagets placering (feature 007).
    const forslag = tilstand.forslag?.d.forbedret ? forslagSpaend(r, v, tilstand.forslag.d.plan) : null;
    let spoegelse = $(".tl-spoegelse", raekke);
    if (!forslag) { spoegelse?.remove(); return; }
    if (!spoegelse) {
      spoegelse = el("div", { class: `tl-spoegelse${r.engang ? " tl-spoegelse--engang" : ""}`, style: `--farve: var(${r.farve})`, "aria-hidden": "true" });
      $(".tl-spor", raekke).prepend(spoegelse);
    }
    placer(spoegelse, forslag[0], forslag[1], r.engang);
  });
}

function visResultat(v, foersteGang = true) {
  $("#guide").hidden = true;
  $("#resultat").hidden = false;
  $("#menu").hidden = false;
  $("#ny-beregning").hidden = false;
  tilstand.vDig = v;
  tilstand.husstand = v.husstand ?? null;
  if (!tilstand.husstand) tilstand.hvem = "dig";
  $("#person-faner").hidden = !tilstand.husstand;
  visHvem(foersteGang);
  regnUsikkerhed();
}

/* ── Usikkerhed om afkast og inflation (feature 018) ──────────────────── */
// Scenarierne regnes i baggrunden, ét ad gangen, efter resultatet. En ny beregning afbryder
// løkken, så den højst venter på ét scenarie i motorens kø.
let usikkerhedNr = 0;

async function regnUsikkerhed() {
  const nr = ++usikkerhedNr;
  const svar = JSON.stringify(tilstand.aktuelleSvar);
  tilstand.usikkerhed = null;
  tegnUsikkerhed();
  try {
    const liste = await kald("scenarier", svar);
    const raekker = [];
    for (const s of liste) {
      if (nr !== usikkerhedNr) return;
      const r = await kald("scenarie", svar, idag(), s.afkast, s.inflation, s.plan_slut_alder);
      raekker.push({ ...s, beloeb: r.ok ? r.data : null });
    }
    if (nr !== usikkerhedNr) return;
    tilstand.usikkerhed = raekker;
    tegnUsikkerhed();
  } catch { /* spændet er en ekstra oplysning; resultatet står stadig */ }
}

function tegnUsikkerhed() {
  const linje = $("#hovedtal-spaend");
  const u = tilstand.usikkerhed;
  if (!u) {
    linje.textContent = "Regner, hvor meget beløbet kan svinge …";
    $("#usikkerhed").hidden = true;
    return;
  }
  const hvem = tilstand.hvem;
  const eget = +$("#hovedtal").dataset.vaerdi;
  const a = tilstand.aktuelleSvar.antagelser;
  const normalSlut = tilstand.vDig.antagelser.livsvarig_horisont_alder;
  const raekker = [{ titel: "Dit valg", afkast: a.afkast_efter_pal, inflation: a.inflation, plan_slut_alder: null, vaerdi: eget },
    ...u.map((r) => ({ ...r, vaerdi: r.beloeb ? r.beloeb[hvem] : null }))];
  // Spændet gælder afkast og inflation (018). Levetid (019) er et andet spørgsmål og står kun i tabellen.
  const tal = raekker.filter((r) => r.plan_slut_alder === null).map((r) => r.vaerdi).filter((x) => x !== null && x !== undefined);
  const min = Math.min(...tal);
  const max = Math.max(...tal);
  linje.replaceChildren(`Hvis afkast og inflation bliver anderledes: mellem ${kr(min)} og ${kr(max)} kr. `,
    el("a", { href: "#usikkerhed", tekst: "Se hvordan" }));
  $("#usikkerhed").hidden = false;
  $("#usikkerhed-tabel").replaceChildren(el("table", {},
    el("caption", { class: "sr-only", tekst: "Det faste beløb om måneden efter skat i dagens kroner ved andet afkast og anden inflation" }),
    el("thead", {}, el("tr", {}, ...["Scenarie", "Afkast", "Inflation", "Planen rækker til", "Fast beløb om måneden"].map((x) => el("th", { scope: "col", tekst: x })))),
    el("tbody", {}, raekker.map((r) => el("tr", {}, el("th", { scope: "row", tekst: r.titel }),
      el("td", { tekst: procent(r.afkast) }), el("td", { tekst: procent(r.inflation) }),
      el("td", { tekst: `${r.plan_slut_alder ?? normalSlut} år` }),
      el("td", { tekst: r.vaerdi === null || r.vaerdi === undefined ? "–" : `${kr(r.vaerdi)} kr.` }))))));
  // Lever du længere end planen (019): kun for én person, ikke under "Samlet".
  const efter = u.find((r) => r.beloeb?.efter_plan)?.beloeb.efter_plan[hvem];
  const linje2 = $("#usikkerhed-efter");
  linje2.hidden = hvem === "samlet" || efter === null || efter === undefined;
  if (!linje2.hidden) {
    linje2.textContent = `Planen bruger ${hvem === "partner" ? "din partners" : "din"} opsparing op til ${normalSlut} år. `
      + `Lever ${hvem === "partner" ? "din partner" : "du"} længere, er der derefter ca. ${kr(efter)} kr. om måneden fra folkepension, ATP og livrente, i dagens kroner.`;
  }
}

function visHvem(foersteGang = false) {
  for (const f of $$('#person-faner [role="tab"]')) {
    const valgt = f.dataset.hvem === tilstand.hvem;
    f.setAttribute("aria-selected", String(valgt));
    f.tabIndex = valgt ? 0 : -1;
  }
  const samlet = tilstand.hvem === "samlet";
  $("#samlet-panel").hidden = !samlet;
  $("#graf-panel").hidden = samlet;
  $("#sammensaetning").hidden = samlet;
  $("#link-sammensaetning").hidden = samlet;
  $("#link-graf").setAttribute("href", samlet ? "#samlet-panel" : "#graf-panel");
  $("#overblik-titel").textContent = { dig: "Dit overblik", partner: "Din partners overblik", samlet: "Jeres overblik" }[tilstand.hvem];
  if (samlet) { tegnSamlet(); return; }
  tegnPerson(tilstand.hvem === "partner" ? tilstand.husstand.partner : tilstand.vDig, foersteGang);
}

function tegnPerson(v, foersteGang) {
  const partner = tilstand.hvem === "partner";
  $("#resultat-titel").textContent = partner ? "Din partner kan forvente ca." : "Du kan forvente ca.";
  const h = v.hovedtal;
  $("#hovedtal").textContent = `${kr(h.maaned)} kr.`;
  $("#hovedtal").dataset.vaerdi = h.maaned;
  $("#hovedtal-forklaring").textContent = h.type === "jaevn"
    ? (partner
      ? `Det faste beløb, din partner kan bruge hver måned fra ${h.fra_alder} år ved selv at udjævne (den stiplede linje i grafen). I dagens kroner.`
        + (h.senere ? ` Fra ${h.senere.fra_alder} år stiger det til ca. ${kr(h.senere.maaned)} kr.` : "")
        + ` Din partners folkepensionsalder er ${v.folkepensionsalder} år.`
      : `Det faste beløb, du kan bruge hver måned fra du er ${h.fra_alder} år, hvis du selv udjævner (den stiplede linje i grafen). I dagens kroner, så beløbet er lige meget værd hele livet.`
        + (h.senere ? ` Fra du er ${h.senere.fra_alder}, stiger det til ca. ${kr(h.senere.maaned)} kr., når flere af dine udbetalinger er begyndt.` : "")
        + ` Din folkepensionsalder er ${v.folkepensionsalder} år.`)
    : `Efter skat og i dagens kroner, i dit første hele år med folkepension (${h.fra_alder} år).`;
  const foer = tilstand.forrigeHovedtal;
  $("#hovedtal-aendring").textContent = foer !== null && foer !== h.maaned
    ? `${h.maaned > foer ? "↑" : "↓"} ${kr(Math.abs(h.maaned - foer))} kr. i forhold til før` : "";
  $("#hovedtal-advarsler").replaceChildren(...v.hovedtal_advarsler.map((a) => advarselEl(a, "chip")));
  const antal = v.hovedtal_advarsler.length;
  $("#hovedtal-forudsaetninger").hidden = !antal;
  $("#forudsaetninger-titel").textContent = `≈ ${antal === 1 ? "Én forudsætning" : `${antal} forudsætninger`} bag tallet →`;

  tilstand.v = v;
  if (tilstand.forslag && tilstand.forslag.noegle !== svarNoegle()) fjernForslag();
  flytFormularTilPanel();
  tegnNoegletal(v);
  tegnGraf(v);
  tegnTidslinje(v);
  tegnKort(v);
  tegnSaadan(v);
  tegnSkydere();
  tegnUsikkerhed();
  tegnForklaringer();
  if (foersteGang) { window.scrollTo({ top: 0 }); $("#resultat-titel").setAttribute("tabindex", "-1"); $("#resultat-titel").focus(); }
}


/* ── Samlet oversigt for et par (feature 012) ─────────────────────────── */
const PERSONFARVER = { dig: "--petrol-700", partner: "--sand-500" };

function tegnSamlet() {
  const s = tilstand.husstand.samlet;
  const vDig = tilstand.vDig;
  const vP = tilstand.husstand.partner;
  $("#resultat-titel").textContent = "I kan forvente ca.";
  $("#hovedtal").textContent = `${kr(s.maaned)} kr.`;
  $("#hovedtal").dataset.vaerdi = s.maaned;
  $("#hovedtal-forklaring").textContent = `Dig ${kr(s.dig.maaned)} kr. og din partner ${kr(s.partner.maaned)} kr. om måneden – `
    + "jeres faste beløb, hvis I hver især udjævner. I dagens kroner. Jeres pensionstillæg og ældrecheck er regnet sammen, som loven siger.";
  $("#hovedtal-aendring").textContent = "";
  const advarsler = [...vDig.hovedtal_advarsler, ...vP.hovedtal_advarsler].filter((a, i, l) => l.findIndex((b) => b.kode === a.kode) === i);
  $("#hovedtal-advarsler").replaceChildren(...advarsler.map((a) => advarselEl(a, "chip")));
  $("#hovedtal-forudsaetninger").hidden = !advarsler.length;
  $("#forudsaetninger-titel").textContent = `≈ ${advarsler.length === 1 ? "Én forudsætning" : `${advarsler.length} forudsætninger`} bag tallet →`;
  const svar = tilstand.aktuelleSvar;
  const pp = svar.person.partner.profil;
  const opsparing = (liste) => liste.reduce((sum, o) => sum + (o.saldo || 0), 0);
  $("#noegletal").replaceChildren(...[
    ["Din folkepension fra", `${vDig.folkepensionsalder + svar.antagelser.folkepension_opsaettelse_aar} år`],
    ["Din partners folkepension fra", `${vP.folkepensionsalder + (pp.folkepension_opsaettelse_aar || 0)} år`],
    ["Jeres pensionsopsparing i dag", `${kr(opsparing(svar.ordninger) + opsparing(pp.ordninger))} kr.`],
    ["Fast beløb: dig / partner", `${kr(s.dig.maaned)} / ${kr(s.partner.maaned)} kr.`],
  ].map(([dt, dd]) => el("div", {}, el("dt", { tekst: dt }), el("dd", { tekst: dd }))));
  tegnSamletGraf(s);
  tegnSamletTidslinje(s);
  tegnUsikkerhed();
  tegnForklaringer();
  $("#samlet-formue").hidden = !s.formue;
  if (s.formue) $("#samlet-formue").textContent = `Jeres opsparing uden for pension: ${kr(s.formue.rest)} kr. tilbage ved udgangen af jeres planer, i dagens kroner.`;
}

function tegnSamletGraf(s) {
  $("#samlet-forklaring").replaceChildren(
    el("li", {}, el("i", { style: `background: var(${PERSONFARVER.dig})`, "aria-hidden": "true" }), "Dig"),
    el("li", {}, el("i", { style: `background: var(${PERSONFARVER.partner})`, "aria-hidden": "true" }), "Din partner"),
    el("li", {}, el("i", { class: "linje", "aria-hidden": "true" }), "Jeres faste beløb tilsammen"));
  const aldre = (i) => `du ${s.alder_dig[i]}, din partner ${s.alder_partner[i]} år`;
  $("#samlet-tabel").replaceChildren(el("table", {},
    el("caption", { class: "sr-only", tekst: "Jeres udbetaling pr. måned efter skat i dagens kroner, pr. kalenderår" }),
    el("thead", {}, el("tr", {}, ...["År", "Din alder", "Din partners alder", "Dig", "Din partner", "I alt", "Faste beløb tilsammen"]
      .map((x) => el("th", { scope: "col", tekst: x })))),
    el("tbody", {}, s.kalenderaar.map((k, i) => el("tr", {}, el("th", { scope: "row", tekst: `${k}` }),
      el("td", { tekst: `${s.alder_dig[i]} år` }), el("td", { tekst: `${s.alder_partner[i]} år` }),
      ...[s.netto_dig[i], s.netto_partner[i], s.netto_dig[i] + s.netto_partner[i], s.jaevn[i]].map((x) => el("td", { tekst: `${kr(x)} kr.` })))))));
  if (typeof Chart === "undefined") return;
  const data = {
    labels: s.kalenderaar.map((k) => `${k}`),
    datasets: [
      { type: "line", label: "Jeres faste beløb tilsammen", data: s.jaevn.map((x) => Math.round(x)), borderColor: css("--jaevn-linje"),
        borderDash: [6, 4], borderWidth: 3, pointRadius: 0, tension: 0, order: 0 },
      { label: "Dig", data: s.netto_dig.map((x) => Math.round(x)), backgroundColor: css(PERSONFARVER.dig), stack: "netto", order: 1, borderRadius: 2 },
      { label: "Din partner", data: s.netto_partner.map((x) => Math.round(x)), backgroundColor: css(PERSONFARVER.partner), stack: "netto", order: 1, borderRadius: 2 },
    ],
  };
  const valg = {
    responsive: true, maintainAspectRatio: false, animation: { duration: 250 },
    plugins: { legend: { display: false },
      tooltip: { callbacks: { title: (t) => `${t[0].label} (${aldre(t[0].dataIndex)})`, label: (c) => ` ${c.dataset.label}: ${kr(c.raw)} kr.` } } },
    scales: {
      x: { stacked: true, grid: { display: false }, title: { display: true, text: "Kalenderår" }, ticks: { maxRotation: 0, autoSkipPadding: 8 } },
      y: { stacked: true, ticks: { callback: (x) => `${kr(x)} kr.` }, grid: { color: css("--graa-200") } },
    },
  };
  if (tilstand.samletGraf) { tilstand.samletGraf.data = data; tilstand.samletGraf.update(); }
  else tilstand.samletGraf = new Chart($("#samlet-graf"), { type: "bar", data, options: valg });
}

function tegnSamletTidslinje(s) {
  // Kun til visning: begges ordninger og folkepension på en fælles kalenderakse. Der rettes under hver person.
  const svar = tilstand.aktuelleSvar;
  const foersteAar = s.kalenderaar[0];
  const sidsteAar = s.kalenderaar.at(-1);
  const pct = (aar) => (100 * (Math.min(Math.max(aar, foersteAar), sidsteAar + 1) - foersteAar)) / (sidsteAar + 1 - foersteAar);
  const personer = [
    { hvem: "dig", navn: "Dig", foedt: +svar.person.foedselsdato.slice(0, 4), ordninger: svar.ordninger,
      fp: tilstand.vDig.folkepensionsalder + svar.antagelser.folkepension_opsaettelse_aar },
    { hvem: "partner", navn: "Din partner", foedt: +svar.person.partner.foedselsdato.slice(0, 4), ordninger: svar.person.partner.profil.ordninger,
      fp: tilstand.husstand.partner.folkepensionsalder + (svar.person.partner.profil.folkepension_opsaettelse_aar || 0) },
  ];
  const raekker = [];
  for (const p of personer) {
    const linjer = p.ordninger.map((o) => {
      const engang = ENGANGSTYPER.has(o.type) && (o.type !== "kapitalpension" || (o.udbetalingsform || "engangs") === "engangs");
      const varighed = o.type === "ratepension" || ["portioner", "ratepension"].includes(o.udbetalingsform) ? (o.udbetaling_aar || 10) : null;
      const fra = p.foedt + o.udbetaling_start_alder;
      const til = engang ? fra : varighed ? fra + varighed - 1 : sidsteAar;
      return { titel: `${p.navn} · ${ordningstitel(o)}`, fra, til, engang };
    });
    linjer.push({ titel: `${p.navn} · Folkepension`, fra: p.foedt + p.fp, til: sidsteAar, engang: false });
    for (const l of linjer) {
      const tekst = l.engang ? `${l.fra}` : l.til >= sidsteAar ? `fra ${l.fra}` : `${l.fra}–${l.til}`;
      const stil = l.engang ? `left: calc(${pct(l.fra)}% + 2px); width: 24px` : `left: ${pct(l.fra)}%; width: ${Math.max(1, pct(l.til + 1) - pct(l.fra))}%`;
      raekker.push(el("div", { class: "tl-raekke tl-raekke--visning", role: "listitem" },
        el("div", { class: "tl-hoved" }, el("strong", { tekst: l.titel }), el("span", { tekst: tekst })),
        el("div", { class: "tl-spor", "aria-hidden": "true" },
          el("div", { class: `tl-bjaelke${l.engang ? " tl-bjaelke--engang" : ""}`, style: `--farve: var(${PERSONFARVER[p.hvem]}); ${stil}` }))));
    }
  }
  $("#samlet-tidslinje").replaceChildren(...raekker);
}

function vaelgFane(hvem, fokus = false) {
  if (tilstand.hvem === hvem) return;
  tilstand.hvem = hvem;
  fjernForslag();
  visHvem();
  if (fokus) $(`#person-faner [data-hvem="${hvem}"]`).focus();
}

/* ── Opsætning ─────────────────────────────────────────────────────────── */
function forbind() {
  startMotor();
  $("#optimer-knap").addEventListener("click", findBedstePlan);
  $("#motor-igen").addEventListener("click", () => { startMotor(); hentKommuner(); });
  hentKommuner();
  visTrin(1, false);
  // Rapporten aflæses, så snart den er valgt (ingen knap).
  $("#pdf-fil").addEventListener("change", () => aflaesPdf("dig"));
  $("#p-pdf-fil").addEventListener("change", () => aflaesPdf("partner"));
  $$("input[name=civilstand], input[name=partnerdata]").forEach((r) => r.addEventListener("change", opdaterPartnerFelter));
  opdaterPartnerFelter();
  $("#p-tilfoej-ordning").addEventListener("click", () => tilfoejOrdning($("#p-ny-type").value, "partner"));
  const faner = $$('#person-faner [role="tab"]');
  faner.forEach((f, i) => {
    f.addEventListener("click", () => vaelgFane(f.dataset.hvem));
    f.addEventListener("keydown", (e) => {
      const ny = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: faner.length - 1 }[e.key];
      if (ny === undefined) return;
      e.preventDefault();
      vaelgFane(faner[(ny + faner.length) % faner.length].dataset.hvem, true);
    });
  });
  for (const [id, fmt] of [["afkast", (v) => `${decimal(v)} %`], ["inflation", (v) => `${decimal(v)} %`], ["opsaettelse", (v) => (+v ? `${v} år` : "Nej")],
    ["p-opsaettelse", (v) => (+v ? `${v} år` : "Nej")]]) {
    $(`#${id}`).addEventListener("input", (e) => { $(`#${id}-v`).textContent = fmt(e.target.value); });
  }
  $("#tilfoej-ordning").addEventListener("click", () => tilfoejOrdning($("#ny-type").value));

  $("#guide-form").addEventListener("submit", (e) => {
    e.preventDefault();
    if (!validerTrin(tilstand.trin)) return;
    if (tilstand.trin < 5) visTrin(naesteTrin(tilstand.trin)); else beregnFraGuide();
  });
  $("#tilbage").addEventListener("click", () => { ryd(); visTrin(forrigeTrin(tilstand.trin)); });
  $("#ny-beregning").addEventListener("click", () => {
    $("#resultat").hidden = true; $("#guide").hidden = false; $("#menu").hidden = true; $("#ny-beregning").hidden = true;
    flytFormularTilGuide();
    tilstand.hvem = "dig";
    visTrin(1);
  });
  for (const navn of ["data", "graf"]) {
    $(`#${navn}-panel-knap`).addEventListener("click", (e) => aabnPanel(navn, e.currentTarget.getAttribute("aria-expanded") !== "true"));
  }
  $("#opdater").addEventListener("click", opdaterFraPanel);
  $("#stop-knap").addEventListener("click", findStopalder);
  $("#aar-forklaring-luk").addEventListener("click", () => { $("#aar-forklaring").hidden = true; $("#graf").focus?.(); });
  hentForklaringer();
  $("#metode-link").addEventListener("click", (e) => { e.preventDefault(); visMetode(); });
  $("#metode-luk").addEventListener("click", () => { $("#metode").hidden = true; $("#metode-link").focus(); });
  $("#metode-udskriv").addEventListener("click", () => window.print());
  $("#udskriv").addEventListener("click", () => window.print());
  $("#eksport-json").addEventListener("click", () => hentEksport("json"));
  $("#eksport-csv").addEventListener("click", () => hentEksport("csv"));
  $("#gem-knap").addEventListener("click", () => {
    const aaben = $("#gem-knap").getAttribute("aria-expanded") === "true";
    $("#gem-knap").setAttribute("aria-expanded", String(!aaben));
    $("#gem-form").hidden = aaben;
  });
  $("#gem-fil").addEventListener("click", gemTilSenere);
  $("#gemt-aabn").addEventListener("click", aabnGemt);
  // Rulbare tabeller skal kunne nås og rulles med tastaturet (WCAG 2.1.1; axe scrollable-region-focusable).
  const rulbare = () => $$(".tabel-rul:not([tabindex])").forEach((d) => {
    d.tabIndex = 0;
    d.setAttribute("role", "region");
    d.setAttribute("aria-label", d.querySelector("caption")?.textContent || "Tabel");
  });
  rulbare();
  new MutationObserver(rulbare).observe(document.body, { childList: true, subtree: true });
  tilstand.kroner = gemtKroner();
  for (const r of $$("input[name=kroner]")) {
    r.checked = r.value === tilstand.kroner;
    r.addEventListener("change", () => {
      tilstand.kroner = r.value;
      try { localStorage.setItem("beloebsvisning", r.value); } catch { /* kun en bekvemmelighed */ }
      if (tilstand.v) { tegnGraf(tilstand.v); tegnKort(tilstand.v); tegnForklaringer(); }
    });
  }

  const skyder = (id, opdater, fmt) => $(`#${id}`).addEventListener("input", (e) => {
    $(`#${id}-v`).textContent = fmt(+e.target.value);
    opdater(+e.target.value);
    genberegn();
  });
  skyder("r-afkast", (v) => { tilstand.aktuelleSvar.antagelser.afkast_efter_pal = v / 100; synkroniserFormular(); }, (v) => `${decimal(v)} %`);
  skyder("r-inflation", (v) => { tilstand.aktuelleSvar.antagelser.inflation = v / 100; synkroniserFormular(); }, (v) => `${decimal(v)} %`);
  $("#hovedtal-spaend").addEventListener("click", (e) => { if (e.target.closest("a")) $("#usikkerhed").open = true; });
  $("#nulstil").addEventListener("click", () => {
    tilstand.aktuelleSvar = structuredClone(tilstand.mineSvar);
    synkroniserFormular();
    tegnSkydere();
    tegnTidslinje(tilstand.v);
    genberegn();
  });
}

document.addEventListener("DOMContentLoaded", forbind);
