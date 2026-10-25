"""Feature 005 (FR-001, D5): src/ kører i Pyodide. Kun standardbiblioteket, projektets egne pakker
og PDF-læseren må importeres — alt andet skal med i den byggede side og koster download."""
import sys

from tests.kontrakt.test_ingen_ai import KILDER, ROD, _importerede_moduler

TILLADTE = {"pensionskerne", "pensionsoverblik", "pdfplumber", "pdfminer"}


def test_kun_stdlib_og_pdflaeser_importeres():
    fund = [f"{f.relative_to(ROD)}: {m}" for f in KILDER for m in _importerede_moduler(f)
            if m.split(".")[0] not in TILLADTE and m.split(".")[0] not in sys.stdlib_module_names]
    assert not fund, "Ikke tilladt i browseren:\n" + "\n".join(fund)


def test_beregning_kraever_ikke_pdflaeseren():
    """Opstart i browseren: kernen indlæses uden pdfplumber/pdfminer/cryptography, som først
    hentes, når en rapport indlæses (research R005)."""
    import subprocess

    kode = ("import sys; from pensionsoverblik import app; "
            "app.beregn('{}', '2026-10-25'); app.kommuner(); "
            "print(sorted(m for m in sys.modules if m.split('.')[0] in ('pdfplumber', 'pdfminer', 'cryptography')))")
    ud = subprocess.run([sys.executable, "-c", kode], capture_output=True, text=True, check=True, cwd=ROD)
    assert ud.stdout.strip() == "[]"
