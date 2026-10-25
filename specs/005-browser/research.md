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
