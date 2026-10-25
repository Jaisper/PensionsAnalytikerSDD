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
  buffer_kapitalskat: ["Skat af afkast på opsparing uden for pension", procent],
  folkepension_opsaettelse_aar: ["Folkepension udskudt", (v) => (v ? `${v} år` : "nej")],
};

const tilstand = {
  trin: 1, ordninger: [], naesteId: 1,
  mineSvar: null,      // svarene fra guiden (til "Nulstil")
  aktuelleSvar: null,  // svarene inkl. ændringer fra skyderne
  sidsteGyldige: null,
  panel: false,        // guidens formular står i datapanelet på resultatsiden
  v: null,             // seneste visningsmodel // seneste svar, der kunne beregnes (skydere vender tilbage hertil ved fejl)
  forrigeHovedtal: null, graf: null,
  tlRaekker: null, valgtRaekke: null, prAar: null,  // tidslinjen (006)
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
async function kald(op, ...args) {
  await motorKlar;
  return new Promise((resolve, reject) => {
    const id = naesteKald++;
    ventende.set(id, { resolve, reject });
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
  $("#naeste").textContent = n === 3 ? "Se min pension" : "Næste →";
  if (fokus) $(`.trin[data-trin="${n}"] h2`).focus();
}

function ryd(rod = document) {
  $$(".felt--fejl", rod).forEach((f) => f.classList.remove("felt--fejl"));
  $$(".felt__fejl.dynamisk", rod).forEach((p) => p.remove());
  $$("[aria-invalid]", rod).forEach((i) => i.removeAttribute("aria-invalid"));
  $("#fejlboks").hidden = true;
}

function visFejl(felt, besked) {
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
    if ($("input[name=civilstand]:checked").value === "gift_samlevende" && !$("#partner-foedselsdato").value) {
      visFejl("partner.foedselsdato", "Skriv din partners fødselsdato."); return false;
    }
  }
  if (n === 2) {
    for (const o of tilstand.ordninger) {
      if (beloeb(o.saldo) === null) { visFejl(`ordninger[${o.id}].saldo`, "Skriv opsparingen (0, hvis den er tom)."); return false; }
      if (!o.udbetaling_start_alder) { visFejl(`ordninger[${o.id}].udbetaling_start_alder`, "Skriv hvornår udbetalingen starter."); return false; }
    }
  }
  return true;
}

function tilfoejOrdning(type) {
  const id = `o${tilstand.naesteId++}`;
  tilstand.ordninger.push({ id, type, saldo: "", aarlig_indbetaling: "", udbetaling_start_alder: type === "livsvarig" ? 67 : 65,
    udbetaling_aar: 10, oprettet: "ved_ikke" });
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
    hjaelp ? el("p", { class: "felt__hjaelp", id: `${id}-hjaelp`, tekst: hjaelp }) : null,
    input);
}

function tegnOrdninger() {
  const rod = $("#ordninger");
  rod.replaceChildren(...tilstand.ordninger.map((o, i) => {
    const t = TYPER[o.type];
    const tal = (navn, ph = "0") => el("input", { inputmode: "numeric", class: "beloeb", value: o[navn] ?? "", placeholder: ph });
    const oprettet = el("select", {}, ...Object.entries(OPRETTET).map(([k, v]) => el("option", { value: k, selected: o.oprettet === k, tekst: v.tekst })));
    const felter = [
      ordningsFelt(o, "saldo", "Opsparing i dag (kr.)", null, tal("saldo")),
      ordningsFelt(o, "aarlig_indbetaling", "Indbetaling pr. år (kr.)", "Efter arbejdsmarkedsbidrag. 0 hvis du ikke indbetaler mere.", tal("aarlig_indbetaling")),
      ordningsFelt(o, "udbetaling_start_alder", o.type === "aldersopsparing" || o.type === "kapitalpension" ? "Udbetales når du er (alder)" : "Udbetalingen starter når du er (alder)",
        null, el("input", { inputmode: "numeric", value: o.udbetaling_start_alder })),
      o.type === "ratepension" ? ordningsFelt(o, "udbetaling_aar", "Udbetales over (antal år)", "Mindst 10 år.", el("input", { inputmode: "numeric", value: o.udbetaling_aar })) : null,
      o.tidligste_udbetalingsalder
        ? el("p", { class: "felt__hjaelp", tekst: `Tidligst udbetaling: ${decimal(o.tidligste_udbetalingsalder)} år (oplyst af selskabet).` })
        : ordningsFelt(o, "oprettet", "Hvornår blev ordningen oprettet?", "Bestemmer, hvornår du tidligst må få pengene.", oprettet),
    ];
    const fjern = el("button", { type: "button", class: "knap knap--tekst", "aria-label": `Fjern ${t.titel.toLowerCase()} ${i + 1}`, tekst: "Fjern" });
    fjern.addEventListener("click", () => { tilstand.ordninger = tilstand.ordninger.filter((x) => x !== o); tegnOrdninger(); $("#ny-type").focus(); });
    const infoId = `${o.id}-info`;
    const info = el("button", { type: "button", class: "info-knap", "aria-expanded": "false", "aria-controls": infoId, "aria-label": `Hvad er ${t.titel.toLowerCase()}?`, tekst: "i" });
    const infoTekst = el("p", { id: infoId, class: "felt__hjaelp", hidden: true, tekst: t.forklaring });
    info.addEventListener("click", () => { const aaben = info.getAttribute("aria-expanded") === "true"; info.setAttribute("aria-expanded", String(!aaben)); infoTekst.hidden = aaben; });
    return el("div", { class: "ordning", style: `--farve: var(${t.farve})` },
      el("div", { class: "ordning__top" }, el("h3", {}, `${t.titel} `, info), fjern),
      infoTekst,
      o.kilde ? el("p", { class: "aflaest", tekst: `Aflæst fra rapporten: ${o.kilde}` }) : null,
      o.usikkerheder?.length ? el("ul", { class: "usikkerheder", "aria-label": "Tjek disse oplysninger" }, o.usikkerheder.map((u) => el("li", { tekst: u }))) : null,
      el("div", { class: "ordning__felter" }, felter));
  }));
}

function guideSvar() {
  const gift = $("input[name=civilstand]:checked").value === "gift_samlevende";
  return {
    person: {
      foedselsdato: $("#foedselsdato").value,
      civilstand: gift ? "gift_samlevende" : "enlig",
      kommune: $("#kommune").value.trim(),
      folkekirkemedlem: $("#folkekirke").checked,
      likvid_formue: beloeb($("#formue").value) ?? 0,
      atp_aarlig: beloeb($("#atp").value),
      partner: gift ? { foedselsdato: $("#partner-foedselsdato").value, oevrig_indkomst_aar: beloeb($("#partner-indkomst").value) ?? 0 } : null,
    },
    ordninger: tilstand.ordninger.map((o) => ({
      id: o.id, type: o.type, saldo: beloeb(o.saldo), aarlig_indbetaling: beloeb(o.aarlig_indbetaling) ?? 0,
      udbetaling_start_alder: beloeb(o.udbetaling_start_alder),
      udbetaling_aar: o.type === "ratepension" ? beloeb(o.udbetaling_aar) : null,
      oprettet: OPRETTET[o.oprettet].dato,
      tidligste_udbetalingsalder: o.tidligste_udbetalingsalder ?? null,
    })),
    antagelser: {
      afkast_efter_pal: +$("#afkast").value / 100,
      inflation: +$("#inflation").value / 100,
      folkepension_opsaettelse_aar: +$("#opsaettelse").value,
    },
  };
}

/* ── Indlæsning af PensionsInfo-rapport (feature 003) ──────────────────── */
async function aflaesPdf() {
  ryd();
  const status = $("#pdf-status");
  const fil = $("#pdf-fil").files[0];
  if (!fil) { visFejl("pdf", "Vælg din rapport først."); return; }
  if (fil.size > MAKS_PDF_BYTES) { visFejl("pdf", `Filen er for stor. Den må højst fylde ${MAKS_PDF_BYTES / 1024 / 1024} MB.`); return; }
  const knap = $("#pdf-knap");
  knap.disabled = true;
  status.textContent = "Aflæser rapporten …";
  try {
    const svar = await kald("pdf", await fil.arrayBuffer());
    if (!svar.ok) {
      status.textContent = "";
      visFejl(svar.fejl.felt || "pdf", svar.fejl.besked);
      return;
    }
    udfyldFraRapport(svar.data);
  } catch {
    status.textContent = "";
    visFejl("pdf", "Rapporten kunne ikke aflæses. Prøv igen, eller indtast dine oplysninger selv.");
  } finally {
    knap.disabled = false;
  }
}

function udfyldFraRapport(d) {
  if (d.person.foedselsdato) $("#foedselsdato").value = d.person.foedselsdato;
  if (d.atp_aarlig) $("#atp").value = kr(d.atp_aarlig);
  tilstand.ordninger = d.ordninger.map((o) => ({
    id: `o${tilstand.naesteId++}`, type: o.type,
    saldo: o.saldo === null ? "" : kr(o.saldo), aarlig_indbetaling: o.aarlig_indbetaling === null ? "" : kr(o.aarlig_indbetaling),
    udbetaling_start_alder: o.udbetaling_start_alder ?? "", udbetaling_aar: o.udbetaling_aar ?? 10,
    oprettet: o.oprettet, kilde: o.kilde, usikkerheder: o.usikkerheder,
    tidligste_udbetalingsalder: o.tidligste_udbetalingsalder,
  }));
  tegnOrdninger();
  const n = d.ordninger.length;
  const usikre = d.ordninger.filter((o) => o.usikkerheder.length).length;
  $("#pdf-status").replaceChildren(...[
    el("p", { tekst: `Vi har aflæst ${n === 1 ? "én ordning" : `${n} ordninger`}${d.atp_aarlig ? " og din ATP" : ""}. `
      + (usikre ? `Tjek tallene – især ved ≈ i trin 2.` : "Tjek tallene i trin 2.") }),
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
    knap.disabled = false; knap.textContent = tilstand.trin === 3 ? "Se min pension" : "Næste →";
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

function tegnGraf(v) {
  const serier = v.graf.serier;
  $("#farveforklaring").replaceChildren(...serier.map((s) => el("li", {}, el("i", { style: `background: var(${s.farve})`, "aria-hidden": "true" }), s.titel)),
    ...(v.graf.jaevn ? [el("li", {}, el("i", { class: "linje", "aria-hidden": "true" }), "Jævnt fordelt (beløbet øverst)")] : []));
  $("#graf-markeringer").replaceChildren(...v.graf.markeringer.map((m) =>
    el("li", {}, el("span", { class: "ikon", "aria-hidden": "true", tekst: "!" }), `${m.titel}: som ${m.fra}–${m.til}-årig`)));

  // Tabelalternativ (FR-023)
  const jaevn = v.graf.jaevn;
  const hoved = el("tr", {}, el("th", { scope: "col", tekst: "Alder" }), ...serier.map((s) => el("th", { scope: "col", tekst: s.titel })),
    el("th", { scope: "col", tekst: "I alt" }), jaevn ? el("th", { scope: "col", tekst: "Jævnt fordelt" }) : null);
  const raekker = v.graf.aldre.map((alder, i) => el("tr", {}, el("th", { scope: "row", tekst: `${alder} år` }),
    ...serier.map((s) => el("td", { tekst: s.vaerdier[i] ? `${kr(s.vaerdier[i])} kr.` : "–" })),
    el("td", { tekst: `${kr(serier.reduce((sum, s) => sum + s.vaerdier[i], 0))} kr.` }),
    jaevn ? el("td", { tekst: `${kr(jaevn[i])} kr.` }) : null));
  $("#graf-tabel").replaceChildren(el("table", {}, el("caption", { class: "sr-only", tekst: "Udbetaling pr. måned efter skat i dagens kroner, pr. alder og kilde" }), el("thead", {}, hoved), el("tbody", {}, raekker)));

  if (typeof Chart === "undefined") {
    $(".graf-ramme").hidden = true;
    $(".tabel-alternativ").open = true;
    return;
  }
  const data = {
    labels: v.graf.aldre.map((a) => `${a}`),
    datasets: [
      ...(jaevn ? [{ type: "line", label: "Jævnt fordelt", data: jaevn.map((x) => Math.round(x)), borderColor: css("--jaevn-linje"),
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
    scales: {
      x: { stacked: true, grid: { display: false }, title: { display: true, text: "Alder" }, ticks: { maxRotation: 0, autoSkipPadding: 8 } },
      y: { stacked: true, ticks: { callback: (x) => `${kr(x)} kr.` }, grid: { color: css("--graa-200") } },
    },
  };
  if (tilstand.graf) { tilstand.graf.data = data; tilstand.graf.update(); }
  else tilstand.graf = new Chart($("#graf"), { type: "bar", data, options: valg });
}

function tegnKort(v) {
  const sidsteAlder = v.graf.aldre.at(-1);
  $("#kort").replaceChildren(...v.kort.map((k) => {
    const detaljeId = `detaljer-${k.noegle}`;
    const infoId = `info-${k.noegle}`;
    const periode = k.til_alder === sidsteAlder ? `Fra du er ${k.fra_alder} år og resten af livet` : `Fra du er ${k.fra_alder} til ${k.til_alder} år`;
    const info = el("button", { type: "button", class: "info-knap", "aria-expanded": "false", "aria-controls": infoId, "aria-label": `Hvad er ${k.titel.toLowerCase()}?`, tekst: "i" });
    const infoTekst = el("p", { class: "kort__forklaring", id: infoId, hidden: true, tekst: k.forklaring });
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
      return el("article", { class: "kort", style: `--farve: var(${k.farve})` },
        el("div", { class: "kort__ikon", "aria-hidden": "true" }),
        el("h3", { class: "kort__titel" }, k.titel, info), infoTekst,
        el("ul", { class: "engangsliste" }, k.engangs.map((e) => el("li", {}, `${kr(e.netto)} kr. `,
          el("small", { tekst: `som ${e.alder}-årig – ${kr(e.netto_real)} kr. i dagens kroner` })))),
        el("p", { class: "kort__periode", tekst: "Efter eventuel afgift. Udbetales én gang." }));
    }
    return el("article", { class: "kort", style: `--farve: var(${k.farve})` },
      el("div", { class: "kort__ikon", "aria-hidden": "true" }),
      el("h3", { class: "kort__titel" }, k.titel, info),
      infoTekst,
      el("p", { class: "kort__beloeb" }, `${kr(k.netto_maaned)} kr.`, el("small", { tekst: " /md." })),
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
  const s = tilstand.aktuelleSvar;
  const opsparing = s.ordninger.reduce((sum, o) => sum + (o.saldo || 0), 0);
  const starter = s.ordninger.map((o) => o.udbetaling_start_alder).filter(Boolean);
  const engangs = v.kort.find((k) => k.noegle === "engangsbeloeb");
  const ops = s.antagelser.folkepension_opsaettelse_aar;
  const tal = [
    ["Folkepension fra", `${v.folkepensionsalder + ops} år`],
    ["Opsparing i dag", `${kr(opsparing)} kr.`],
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
  for (const o of tilstand.ordninger) {
    const a = s.ordninger.find((x) => x.id === o.id);
    if (a) { o.udbetaling_start_alder = a.udbetaling_start_alder; if (a.udbetaling_aar) o.udbetaling_aar = a.udbetaling_aar; }
  }
  $("#opsaettelse").value = s.antagelser.folkepension_opsaettelse_aar;
  $("#opsaettelse-v").textContent = s.antagelser.folkepension_opsaettelse_aar ? `${s.antagelser.folkepension_opsaettelse_aar} år` : "Nej";
  $("#afkast").value = s.antagelser.afkast_efter_pal * 100;
  $("#afkast-v").textContent = procent(s.antagelser.afkast_efter_pal);
  $("#inflation").value = s.antagelser.inflation * 100;
  $("#inflation-v").textContent = procent(s.antagelser.inflation);
  tegnOrdninger();
}

async function opdaterFraPanel() {
  ryd();
  if (!validerTrin(1) || !validerTrin(2)) return;
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

function ordningstitel(o) {
  const g = tilstand.ordninger.find((x) => x.id === o.id);
  const selskab = g?.kilde ? g.kilde.split(" · ")[0] : null;
  return selskab ? `${selskab} · ${TYPER[o.type].titel}` : TYPER[o.type].titel;
}

/* ── Feature 006: bjælker, der trækkes ───────────────────────────────── */
/* Bjælken (eller punktet) er selv kontrollen: træk med mus/finger, klik for ‹ ›, eller brug
   tastaturet. Alle tre veje går gennem saetVaerdi, og kernen regner, når ændringen er færdig. */

function tidslinjeRaekker(v) {
  // Én beskrivelse pr. række og kontrol: hvad den ændrer, grænser (fra kernen og registret) og tekst.
  const s = tilstand.aktuelleSvar;
  const g = v.graenser;
  const aldre = v.graf.aldre;
  const raekker = s.ordninger.map((o) => {
    const titel = ordningstitel(o);
    const engang = ENGANGSTYPER.has(o.type);
    const tidligste = Math.ceil(g.ordninger[o.id]?.tidligste ?? aldre[0]);
    const kontroller = {
      start: { navn: engang ? "Udbetales som" : "Start", label: `${titel}, ${engang ? "udbetales som" : "start"}`,
        ned: "Start 1 år tidligere", op: "Start 1 år senere", min: tidligste, maks: Math.max(tidligste, aldre.at(-1)),
        hent: () => o.udbetaling_start_alder, saet: (n) => { o.udbetaling_start_alder = n; }, tekst: (n) => `${n} år` },
    };
    if (o.type === "ratepension") {
      kontroller.varighed = { navn: "Varighed", label: `${titel}, varighed`, ned: "Varighed 1 år kortere", op: "Varighed 1 år længere",
        min: g.ratepension_aar.min, maks: g.ratepension_aar.maks,
        hent: () => o.udbetaling_aar || g.ratepension_aar.min, saet: (n) => { o.udbetaling_aar = n; }, tekst: (n) => `${n} år` };
    }
    return { id: o.id, type: o.type, titel, farve: TYPER[o.type].farve, engang, kontroller };
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
  if (r.kontroller.varighed) return `${fra}–${til} år`;
  return r.engang ? `udbetales som ${fra}-årig` : `fra ${fra} år, livsvarig`;
}

function tegnTidslinje(v) {
  if (!v) return;
  const fokus = document.activeElement?.dataset?.kontrol;  // bevar fokus, når rækkerne tegnes igen
  tilstand.tlRaekker = tidslinjeRaekker(v);
  const raekker = tilstand.tlRaekker.map((r) => {
    const bjaelke = el("div", { class: `tl-bjaelke${r.engang ? " tl-bjaelke--engang" : ""}`, style: `--farve: var(${r.farve})`,
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
  tilstand.tlRaekker.forEach((r) => {
    const raekke = $(`.tl-raekke[data-id="${r.id}"]`);
    if (!raekke) return;
    const b = $(".tl-bjaelke", raekke);
    const [start, slut] = spaend(r, v);
    b.dataset.start = start;
    b.dataset.slut = slut;
    const fra = Math.max(start, aldre[0]) - aldre[0];
    const til = Math.min(slut, aldre.at(-1)) - aldre[0] + 1;
    if (r.engang) {
      b.style.left = `${x0 + (fra + 0.5) * prAar - PUNKT_PX / 2}px`;
      b.style.width = "";
    } else {
      b.style.left = `${x0 + fra * prAar}px`;
      b.style.width = `${Math.max(PUNKT_PX, (til - fra) * prAar)}px`;
    }
    const greb = $(".tl-greb", raekke);
    if (greb) greb.style.left = `${x0 + til * prAar - PUNKT_PX / 2}px`;
  });
}

function visResultat(v, foersteGang = true) {
  $("#guide").hidden = true;
  $("#resultat").hidden = false;
  $("#menu").hidden = false;
  $("#ny-beregning").hidden = false;

  const h = v.hovedtal;
  $("#hovedtal").textContent = `${kr(h.maaned)} kr.`;
  $("#hovedtal").dataset.vaerdi = h.maaned;
  $("#hovedtal-forklaring").textContent = h.type === "jaevn"
    ? `Når dine udbetalinger fordeles jævnt, fra du er ${h.fra_alder} år. I dagens kroner, så beløbet er lige meget værd hele livet.`
      + (h.foer ? ` De første år, fra du er ${h.foer.fra_alder}, er det ca. ${kr(h.foer.maaned)} kr., indtil dit engangsbeløb er udbetalt.` : "")
      + ` Din folkepensionsalder er ${v.folkepensionsalder} år.`
    : `Efter skat og i dagens kroner, i dit første hele år med folkepension (${h.fra_alder} år).`;
  const foer = tilstand.forrigeHovedtal;
  $("#hovedtal-aendring").textContent = foer !== null && foer !== h.maaned
    ? `${h.maaned > foer ? "↑" : "↓"} ${kr(Math.abs(h.maaned - foer))} kr. i forhold til før` : "";
  $("#hovedtal-advarsler").replaceChildren(...v.hovedtal_advarsler.map((a) => advarselEl(a, "chip")));
  const antal = v.hovedtal_advarsler.length;
  $("#hovedtal-forudsaetninger").hidden = !antal;
  $("#forudsaetninger-titel").textContent = `≈ ${antal === 1 ? "Én forudsætning" : `${antal} forudsætninger`} bag tallet →`;

  tilstand.v = v;
  flytFormularTilPanel();
  tegnNoegletal(v);
  tegnGraf(v);
  tegnTidslinje(v);
  tegnKort(v);
  tegnSaadan(v);
  tegnSkydere();
  if (foersteGang) { window.scrollTo({ top: 0 }); $("#resultat-titel").setAttribute("tabindex", "-1"); $("#resultat-titel").focus(); }
}

/* ── Opsætning ─────────────────────────────────────────────────────────── */
function forbind() {
  startMotor();
  $("#motor-igen").addEventListener("click", () => { startMotor(); hentKommuner(); });
  hentKommuner();
  visTrin(1, false);
  $("#pdf-knap").addEventListener("click", aflaesPdf);

  $$("input[name=civilstand]").forEach((r) => r.addEventListener("change", () => {
    $("#partner-felter").hidden = $("input[name=civilstand]:checked").value !== "gift_samlevende";
  }));
  for (const [id, fmt] of [["afkast", (v) => `${decimal(v)} %`], ["inflation", (v) => `${decimal(v)} %`], ["opsaettelse", (v) => (+v ? `${v} år` : "Nej")]]) {
    $(`#${id}`).addEventListener("input", (e) => { $(`#${id}-v`).textContent = fmt(e.target.value); });
  }
  $("#tilfoej-ordning").addEventListener("click", () => tilfoejOrdning($("#ny-type").value));

  $("#guide-form").addEventListener("submit", (e) => {
    e.preventDefault();
    if (!validerTrin(tilstand.trin)) return;
    if (tilstand.trin < 3) visTrin(tilstand.trin + 1); else beregnFraGuide();
  });
  $("#tilbage").addEventListener("click", () => { ryd(); visTrin(tilstand.trin - 1); });
  $("#ny-beregning").addEventListener("click", () => {
    $("#resultat").hidden = true; $("#guide").hidden = false; $("#menu").hidden = true; $("#ny-beregning").hidden = true;
    flytFormularTilGuide();
    visTrin(1);
  });
  for (const navn of ["data", "graf"]) {
    $(`#${navn}-panel-knap`).addEventListener("click", (e) => aabnPanel(navn, e.currentTarget.getAttribute("aria-expanded") !== "true"));
  }
  $("#opdater").addEventListener("click", opdaterFraPanel);

  const skyder = (id, opdater, fmt) => $(`#${id}`).addEventListener("input", (e) => {
    $(`#${id}-v`).textContent = fmt(+e.target.value);
    opdater(+e.target.value);
    genberegn();
  });
  skyder("r-afkast", (v) => { tilstand.aktuelleSvar.antagelser.afkast_efter_pal = v / 100; synkroniserFormular(); }, (v) => `${decimal(v)} %`);
  skyder("r-inflation", (v) => { tilstand.aktuelleSvar.antagelser.inflation = v / 100; synkroniserFormular(); }, (v) => `${decimal(v)} %`);
  $("#nulstil").addEventListener("click", () => {
    tilstand.aktuelleSvar = structuredClone(tilstand.mineSvar);
    synkroniserFormular();
    tegnSkydere();
    tegnTidslinje(tilstand.v);
    genberegn();
  });
}

document.addEventListener("DOMContentLoaded", forbind);
