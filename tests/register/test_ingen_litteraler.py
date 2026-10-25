"""T008 (T-LINT) — ingen satser som tal i beregningskoden (Forfatningens Princip II)."""
import ast
from pathlib import Path

import pensionskerne

TILLADTE = {0, 1, 12, 100}
ROD = Path(pensionskerne.__file__).parent
FILER = sorted((ROD / "regler").glob("*.py")) + [ROD / "fremskrivning.py"]


def test_ingen_numeriske_litteraler():
    fund = []
    for fil in FILER:
        for node in ast.walk(ast.parse(fil.read_text(encoding="utf-8"))):
            if (isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
                    and not isinstance(node.value, bool) and node.value not in TILLADTE):
                fund.append(f"{fil.name}:{node.lineno}: {node.value}")
    assert not fund, "Satser hører hjemme i regelregistret:\n" + "\n".join(fund)
