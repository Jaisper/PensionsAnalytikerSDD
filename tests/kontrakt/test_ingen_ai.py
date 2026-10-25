"""Princip XI (NFR): ingen persondata til AI/LLM. Håndhæves ved, at ingen kode, der håndterer
brugerdata, kan tale med en AI/LLM-tjeneste — hverken via klientbibliotek, afhængighed eller URL."""
import ast
import tomllib
from pathlib import Path

ROD = Path(__file__).resolve().parents[2]
KILDER = sorted((ROD / "src").rglob("*.py"))
STATISK = sorted((ROD / "src").rglob("*.js")) + sorted((ROD / "src").rglob("*.html"))

FORBUDTE_MODULER = {
    "anthropic", "openai", "cohere", "mistralai", "ollama", "litellm", "langchain", "llama_index",
    "transformers", "vertexai", "groq", "together", "replicate",
}
FORBUDTE_PRAEFIKSER = ("google.generativeai", "google.genai", "langchain_", "azure.ai.inference")
FORBUDTE_VAERTER = (
    "api.anthropic.com", "anthropic.com", "claude.ai", "api.openai.com", "openai.azure.com",
    "generativelanguage.googleapis.com", "api.mistral.ai", "api.cohere.ai", "api.groq.com",
)


def _importerede_moduler(fil: Path) -> set[str]:
    moduler = set()
    for node in ast.walk(ast.parse(fil.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            moduler |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            moduler.add(node.module)
        elif isinstance(node, ast.Call) and getattr(node.func, "id", None) == "__import__":
            moduler |= {a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)}
    return moduler


def _forbudt(modul: str) -> bool:
    return modul.split(".")[0] in FORBUDTE_MODULER or modul.startswith(FORBUDTE_PRAEFIKSER)


def test_ingen_ai_klientbiblioteker_importeres():
    fund = [f"{f.relative_to(ROD)}: {m}" for f in KILDER for m in _importerede_moduler(f) if _forbudt(m)]
    assert not fund, "Princip XI: AI/LLM-klienter må ikke bruges:\n" + "\n".join(fund)


def test_ingen_ai_afhaengigheder():
    pyproject = tomllib.loads((ROD / "pyproject.toml").read_text(encoding="utf-8"))
    alle = list(pyproject["project"].get("dependencies", []))
    for gruppe in pyproject.get("dependency-groups", {}).values():
        alle += gruppe
    navne = {d.split(">")[0].split("=")[0].split("<")[0].split("[")[0].strip().lower() for d in alle}
    fund = sorted(n for n in navne if _forbudt(n.replace("-", "_")))
    assert not fund, f"Princip XI: AI/LLM-afhængigheder fundet: {fund}"


def test_ingen_ai_vaerter_i_koden():
    fund = [f"{f.relative_to(ROD)}: {v}" for f in KILDER + STATISK
            for v in FORBUDTE_VAERTER if v in f.read_text(encoding="utf-8")]
    assert not fund, "Princip XI: AI/LLM-endpoints fundet:\n" + "\n".join(fund)


def test_pdf_aflaesning_er_slaaet_fra_selv_med_ai_noegle(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    from pensionsoverblik.pdfimport.aflaeser import vaelg_aflaeser
    assert vaelg_aflaeser() is None
