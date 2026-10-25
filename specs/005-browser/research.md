# Research: Kør i browseren

## R001 Afprøvning: kerne og parser i Pyodide (2026-10-25)

**Opsætning:**
- Projektets wheel (`uv build --wheel`) blev kørt uændret i Pyodide 0.27.7 (Python 3.12) i
  headless Chrome.
- Afhængigheder:
  - `pydantic` fra Pyodides egen pakkeliste
  - `pdfminer.six==20260107` via micropip
  - `pdfplumber==0.11.10` med `deps=False`
- Pipeline: samme kæde som `/api/pdf` og `/api/beregn`, dvs. `udtraek_forside`,
  `foedselsdato_fra_rapport`, `aflaes_sync`, `til_guide`, `til_kerne`, `beregn`, `byg_visning`
  og `graenser`. Fast dato 2026-10-25.
- Testdata: den syntetiske rapport og guide-eksemplet (`tests/app/test_oversaet.py::GUIDE`).

**Resultat:**

| Del | Sammenlignet med CPython |
|---|---|
| PDF-aflæsning (alle felter) | identisk |
| Hovedtal, grænser, advarsler, satser, 98 kommuner | identisk |
| Rå årstal, graf og kort | største relative afvigelse 4,2·10⁻¹⁶ (1–2 ULP) |

| Tid (første besøg) | ms |
|---|---|
| Pyodide-opstart | 1.882 |
| Pakker | 2.544 |
| Import af kernen | 846 |
| Første kørsel / anden kørsel | 218 / 189 (CPython 114) |

Overført cirka 16 MB.

**Fund:**
- pdfplumber kræver pypdfium2 og Pillow, men bruger dem kun i `display.py` til at tegne sider
  som billeder. Det gør vi aldrig, så installation med `deps=False` er nok.
- Kaldt fra JavaScript skal micropips nøgleordsargumenter gives med `install.callKwargs(...)`.
  Et JS-objekt som andet argument bliver ellers ignoreret.
- En `Uint8Array` fra JS skal konverteres med `.to_bytes()`, før `pdfplumber` kan læse den.
- Afvigelserne i sidste decimal skyldes `**`/`pow` i WebAssemblys libm i forhold til Windows'
  CRT. De optræder ved afrunding til kroner i ekstremt sjældne tilfælde og er ikke en
  regelafvigelse.

**Afvist alternativ:** At skrive kernen om til JavaScript ville give to implementeringer af
reglerne og bryde med Princip I og II.

## R002 pydantic fjernet

`aflaeser.py` brugte `BaseModel` som ren datastruktur. Det var en rest fra AI-tiden, hvor JSON
skulle valideres. Ingen kode brugte validering eller serialisering, så modellerne blev erstattet
af `@dataclass`. Det sparer pydantic, pydantic_core, typing_extensions og annotated_types i
browseren. `tests/kontrakt/test_browserpakker.py` sikrer, at `src/` kun importerer stdlib,
egne pakker og PDF-læseren.

## R003 Pyodide melder ikke altid fejl

Hvis `pyodide.asm.wasm` ikke kan hentes, logger Pyodide en advarsel ("wasm instantiation
failed"), men `loadPyodide` hverken afviser eller afslutter. Derfor har `app.js` en frist på
120 s, som giver langsomme forbindelser tid til de cirka 15 MB. Når fristen udløber, stoppes
workeren, og borgeren får "Prøv igen" (testet med en frist på 3 s).

## R004 Scanning af historikken før offentligt repo (2026-10-25)

`scripts/scan_historik.py --rapport <rigtig rapport>` blev kørt på alle 23 commits og 278
filversioner.

- **Fra den rigtige rapport** (navn, CPR, 3 aftalenumre og 7 ticifrede numre): 0
  fund.
- **PDF-filer og nøgler** (Anthropic, OpenAI, GitHub, AWS, private nøgler): 0 fund.
- **Generelt CPR-mønster:** 17 fund, alle fiktive eller falske positiver:
  - testværdier, der ender på `-1234`, i `tests/app/pdfhjaelp.py` og
    `tests/app/test_pdf_tekst.py`
  - et eksempel i den gamle AI-prompt i `legacy/prompts.py`
  - cifre i wheel-URL'er i `uv.lock`

Konklusion: historikken kan gøres offentlig uden oprydning. Commit-forfatter (navn og e-mail)
bliver synlig, som det altid er tilfældet på GitHub.

## R005 Hurtigere opstart: PDF-læseren hentes bagefter

**Måling på den udgivne side** (2026-10-25): andet besøg var klar på 3,1 s, mens SC-002 kræver
under 3 s. Tiden gik til at starte Pyodide og indlæse cryptography (med openssl), pdfminer og
pdfplumber. Den del bruges kun, når en rapport indlæses.

**Ændring:**
- `app.py` importerer først PDF-modulerne og opretter først parseren ved første `pdf()`.
- `manifest.json` er delt i `kerne` og `pdf`.
- Workeren melder klar efter kernen og henter PDF-delen i baggrunden bagefter. En PDF, der
  kommer for tidligt, venter på den.
- Pyodides `loadPackage` melder ikke fejl, når en fil ikke kan hentes. Derfor tjekker workeren
  med `import pdfplumber`. Fejler det, prøver næste PDF igen.

**Tests:**
- `tests/kontrakt/test_browserpakker.py::test_beregning_kraever_ikke_pdflaeseren`
- `tests/browser/test_indlaesning.py::test_motoren_er_klar_uden_pdflaeseren`
- Netværkstesten tjekker nu kravet direkte: kun GET af egne filer, ingen data i nogen request og
  ingen requests, efter rapporten er læst.

**Resultat lokalt:** første besøg 2,8 → 2,2 s og andet besøg 2,4 → 2,1 s. Resten er Pyodides
egen opstart.
