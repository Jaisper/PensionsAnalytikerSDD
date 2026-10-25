/* Pensionsoverblik — frontend uden build-trin.
   Alle tal kommer fra /api/beregn (Princip I). Her formateres og vises de kun. */
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
  sidsteGyldige: null, // seneste svar, der kunne beregnes (skydere vender tilbage hertil ved fejl)
  forrigeHovedtal: null, graf: null,
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

/* ── Guide ─────────────────────────────────────────────────────────────── */
async function hentKommuner() {
  try {
    const liste = await (await fetch("/api/kommuner")).json();
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
  if (trin) visTrin(+trin.dataset.trin, false);
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
      ordningsFelt(o, "oprettet", "Hvornår blev ordningen oprettet?", "Bestemmer, hvornår du tidligst må få pengene.", oprettet),
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
    })),
    antagelser: {
      afkast_efter_pal: +$("#afkast").value / 100,
      inflation: +$("#inflation").value / 100,
      folkepension_opsaettelse_aar: +$("#opsaettelse").value,
    },
  };
}

/* ── Indlæsning af PensionsInfo-rapport (feature 003) ──────────────────── */
async function pdfStatus() {
  try { $("#upload").hidden = !(await (await fetch("/api/pdf/status")).json()).aktiv; } catch { /* manuel indtastning virker */ }
}

async function aflaesPdf() {
  ryd();
  const status = $("#pdf-status");
  const fil = $("#pdf-fil").files[0];
  if (!fil) { visFejl("pdf", "Vælg din rapport først."); return; }
  const knap = $("#pdf-knap");
  knap.disabled = true;
  status.textContent = "Aflæser rapporten …";
  try {
    const svar = await fetch("/api/pdf", { method: "POST", headers: { "Content-Type": "application/pdf" }, body: fil });
    const data = await svar.json().catch(() => ({}));
    if (!svar.ok) {
      status.textContent = "";
      visFejl(data.felt || "pdf", data.besked || "Rapporten kunne ikke aflæses. Du kan i stedet indtaste dine oplysninger selv.");
      return;
    }
    udfyldFraRapport(data);
  } catch {
    status.textContent = "";
    visFejl("pdf", "Rapporten kunne ikke sendes. Prøv igen, eller indtast dine oplysninger selv.");
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
  const svarHttp = await fetch("/api/beregn", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(svar),
  });
  const data = await svarHttp.json().catch(() => ({}));
  if (svarHttp.status === 422) return { fejl: data };
  if (!svarHttp.ok) throw new Error("server");
  return { visning: data };
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
function genberegn() {
  clearTimeout(ventetimer);
  ventetimer = setTimeout(async () => {
    $("#r-start-fejl").hidden = true;
    try {
      const { fejl, visning } = await hentBeregning(tilstand.aktuelleSvar);
      if (fejl) {
        tilstand.aktuelleSvar = structuredClone(tilstand.sidsteGyldige);
        tegnSkydere();
        const p = $("#r-start-fejl");
        p.textContent = `${fejl.besked}. Vi har sat skyderen tilbage.`; p.hidden = false;
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
  saet("r-opsaettelse", s.antagelser.folkepension_opsaettelse_aar, s.antagelser.folkepension_opsaettelse_aar ? `${s.antagelser.folkepension_opsaettelse_aar} år` : "Nej");
  const loebende = s.ordninger.filter((o) => o.type === "ratepension" || o.type === "livsvarig");
  $("#r-start-felt").hidden = !loebende.length;
  if (loebende.length) saet("r-start", loebende[0].udbetaling_start_alder, `${loebende[0].udbetaling_start_alder} år`);
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

  tegnGraf(v);
  tegnKort(v);
  tegnSaadan(v);
  tegnSkydere();
  if (foersteGang) { window.scrollTo({ top: 0 }); $("#resultat-titel").setAttribute("tabindex", "-1"); $("#resultat-titel").focus(); }
}

/* ── Opsætning ─────────────────────────────────────────────────────────── */
function forbind() {
  hentKommuner();
  pdfStatus();
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
    visTrin(1);
  });

  const skyder = (id, opdater, fmt) => $(`#${id}`).addEventListener("input", (e) => {
    $(`#${id}-v`).textContent = fmt(+e.target.value);
    opdater(+e.target.value);
    genberegn();
  });
  skyder("r-afkast", (v) => (tilstand.aktuelleSvar.antagelser.afkast_efter_pal = v / 100), (v) => `${decimal(v)} %`);
  skyder("r-inflation", (v) => (tilstand.aktuelleSvar.antagelser.inflation = v / 100), (v) => `${decimal(v)} %`);
  skyder("r-opsaettelse", (v) => (tilstand.aktuelleSvar.antagelser.folkepension_opsaettelse_aar = v), (v) => (v ? `${v} år` : "Nej"));
  skyder("r-start", (v) => tilstand.aktuelleSvar.ordninger
    .filter((o) => o.type === "ratepension" || o.type === "livsvarig")
    .forEach((o) => (o.udbetaling_start_alder = v)), (v) => `${v} år`);
  $("#nulstil").addEventListener("click", () => {
    tilstand.aktuelleSvar = structuredClone(tilstand.mineSvar);
    tegnSkydere();
    genberegn();
  });
}

document.addEventListener("DOMContentLoaded", forbind);
