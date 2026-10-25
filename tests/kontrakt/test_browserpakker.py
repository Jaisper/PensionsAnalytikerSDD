"""Feature 005 (FR-001, D5): src/ kører i Pyodide. Kun standardbiblioteket, projektets egne pakker
og PDF-læseren må importeres — alt andet skal med i den byggede side og koster download."""
import sys

from tests.kontrakt.test_ingen_ai import KILDER, ROD, _importerede_moduler

TILLADTE = {"pensionskerne", "pensionsoverblik", "pdfplumber", "pdfminer"}


def test_kun_stdlib_og_pdflaeser_importeres():
    fund = [f"{f.relative_to(ROD)}: {m}" for f in KILDER for m in _importerede_moduler(f)
            if m.split(".")[0] not in TILLADTE and m.split(".")[0] not in sys.stdlib_module_names]
    assert not fund, "Ikke tilladt i browseren:\n" + "\n".join(fund)
