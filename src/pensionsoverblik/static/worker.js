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
    else:
        raise ValueError(op)
    return json.dumps(svar, allow_nan=False)

kald
`;

const motor = (async () => {
  status({ andel: 0.05 });
  const manifest = await (await fetch(new URL("./py/manifest.json", import.meta.url))).json();
  const py = await loadPyodide({ indexURL: new URL("./pyodide/", import.meta.url).href });
  status({ andel: 0.45 });
  await py.loadPackage(manifest.pakker, stille);
  status({ andel: 0.65 });
  await py.loadPackage(manifest.wheels.map((w) => new URL(`./py/${w}`, import.meta.url).href), stille);
  status({ andel: 0.85 });
  const kald = py.runPython(PYTHON);
  status({ andel: 1, klar: true });
  return kald;
})();
motor.catch((e) => status({ fejl: String(e) }));

onmessage = async ({ data: { id, op, args } }) => {
  try {
    const kald = await motor;
    const pyArgs = args.map((a) => (a instanceof ArrayBuffer ? new Uint8Array(a) : a));
    postMessage({ id, svar: JSON.parse(kald(op, ...pyArgs)) });
  } catch (e) {
    postMessage({ id, fejl: String(e) });
  }
};
