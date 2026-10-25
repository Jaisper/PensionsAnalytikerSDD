/* Beregningsmotor (feature 005, D2): Python-kernen i Pyodide, uden for sidens hovedtråd.
   Alt hentes fra sidens egne filer (py/manifest.json). Intet sendes ud — rapporter og
   guidedata bliver i denne worker (Princip VII og XI). */
import { loadPyodide } from "./pyodide/pyodide.mjs";

const status = (s) => postMessage({ status: s });
const stille = { messageCallback: () => {} };

const PYTHON = `
import json
from pensionsoverblik import app

def kald(op, *args):
    if op == "kommuner":
        svar = app.kommuner()
    elif op == "beregn":
        svar = app.beregn(args[0], args[1])
    elif op == "pdf":
        svar = app.pdf(args[0].to_bytes())
    elif op == "optimer":
        svar = app.optimer(args[0], args[1], args[-1], *args[2:-1])  # fremdrift sidst; evt. hvem
    else:
        raise ValueError(op)
    return json.dumps(svar, allow_nan=False)

kald
`;

const url = (w) => new URL(`./py/${w}`, import.meta.url).href;

// Opstart: kun Pyodide og kernen. PDF-læseren (pdfminer, pdfplumber og cryptography) hentes
// bagefter i baggrunden, så borgeren kan regne hurtigere (research R005).
const motor = (async () => {
  status({ andel: 0.05 });
  const manifest = await (await fetch(new URL("./py/manifest.json", import.meta.url))).json();
  const py = await loadPyodide({ indexURL: new URL("./pyodide/", import.meta.url).href });
  status({ andel: 0.6 });
  await py.loadPackage(manifest.kerne.map(url), stille);
  status({ andel: 0.85 });
  const kald = py.runPython(PYTHON);
  status({ andel: 1, klar: true });
  return { py, manifest, kald };
})();
motor.catch((e) => status({ fejl: String(e) }));

let pdfKlar = null;
function hentPdf({ py, manifest }) {
  pdfKlar ??= (async () => {
    await py.loadPackage(manifest.pdf.pakker, stille);
    await py.loadPackage(manifest.pdf.wheels.map(url), stille);
    py.runPython("import pdfplumber");  // loadPackage melder ikke fejl, hvis en fil ikke kunne hentes
  })().catch((e) => { pdfKlar = null; throw e; });  // næste PDF prøver igen
  return pdfKlar;
}
motor.then((m) => hentPdf(m)).catch(() => {});

onmessage = async ({ data: { id, op, args } }) => {
  try {
    const m = await motor;
    if (op === "pdf") await hentPdf(m);
    const kald = m.kald;
    const pyArgs = args.map((a) => (a instanceof ArrayBuffer ? new Uint8Array(a) : a));
    if (op === "optimer") {
      // Fremdrift fra kernen (antal afprøvede / budget), højst ved hver hele procent.
      let sidst = -1;
      pyArgs.push((n, iAlt) => {
        const andel = Math.floor((100 * n) / iAlt);
        if (andel !== sidst) { sidst = andel; postMessage({ id, fremdrift: andel / 100 }); }
      });
    }
    postMessage({ id, svar: JSON.parse(kald(op, ...pyArgs)) });
  } catch (e) {
    postMessage({ id, fejl: String(e) });
  }
};
