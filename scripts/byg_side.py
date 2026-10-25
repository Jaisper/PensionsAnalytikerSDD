"""Bygger den statiske side til _site/ (feature 005, D4). Kun standardbiblioteket.

Alt hentes i de versioner og med de SHA-256, der står i scripts/pyodide_laas.toml, og bygget
fejler ved enhver afvigelse. Downloads gemmes i .byggecache/, så et nyt byg ikke henter igen.

Brug:  uv run python scripts/byg_side.py
       uv run python -m http.server -d _site 8002
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tomllib
import urllib.request
from pathlib import Path

ROD = Path(__file__).resolve().parents[1]
LAAS = tomllib.loads((ROD / "scripts" / "pyodide_laas.toml").read_text(encoding="utf-8"))
CACHE = ROD / ".byggecache"
SITE = ROD / "_site"
STATISK = ROD / "src" / "pensionsoverblik" / "static"
KERNEFILER = ("pyodide.mjs", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json")


def hent(url: str, sha256: str) -> Path:
    """Henter url til cachen (én gang) og tjekker SHA-256."""
    sti = CACHE / sha256[:16] / url.rsplit("/", 1)[-1]
    if not sti.exists():
        sti.parent.mkdir(parents=True, exist_ok=True)
        print(f"  henter {url}")
        with urllib.request.urlopen(url, timeout=120) as svar:
            data = svar.read()
        sti.write_bytes(data)
    faktisk = hashlib.sha256(sti.read_bytes()).hexdigest()
    if faktisk != sha256:
        sti.unlink()
        sys.exit(f"SHA-256 passer ikke for {url}: forventet {sha256}, fik {faktisk}")
    return sti


def pyodide_kerne(ud: Path) -> dict:
    p = LAAS["pyodide"]
    with tarfile.open(hent(p["kerne_url"], p["kerne_sha256"]), "r:bz2") as tar:
        for navn in KERNEFILER:
            kilde = tar.extractfile(f"pyodide/{navn}")
            (ud / navn).write_bytes(kilde.read())
    return json.loads((ud / "pyodide-lock.json").read_text(encoding="utf-8"))


def pyodide_pakker(ud: Path, lock: dict) -> list[str]:
    """Pakkerne og deres afhængigheder fra Pyodides lock, lagt ved siden af kernen (indexURL)."""
    valgt: list[str] = []

    def tilfoej(navn: str) -> None:
        if navn in valgt:
            return
        valgt.append(navn)
        for afh in lock["packages"][navn]["depends"]:
            tilfoej(afh)

    for navn in LAAS["pyodide"]["pakker"]:
        tilfoej(navn)
    for navn in valgt:
        pk = lock["packages"][navn]
        shutil.copy(hent(LAAS["pyodide"]["pakke_url"] + pk["file_name"], pk["sha256"]), ud / pk["file_name"])
    return LAAS["pyodide"]["pakker"]


def pdf_wheels(ud: Path) -> list[str]:
    navne = []
    for w in LAAS["wheel"]:
        sti = hent(w["url"], w["sha256"])
        shutil.copy(sti, ud / sti.name)
        navne.append(sti.name)
    return navne


def kerne_wheel(ud: Path) -> list[str]:
    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(ud), "--quiet"], cwd=ROD, check=True)
    (ud / ".gitignore").unlink(missing_ok=True)  # uv lægger en .gitignore i out-dir
    return sorted(p.name for p in ud.glob("pensionskerne-*.whl"))


def byg() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "pyodide").mkdir(parents=True)
    (SITE / "py").mkdir()
    print("Pyodide …")
    lock = pyodide_kerne(SITE / "pyodide")
    pakker = pyodide_pakker(SITE / "pyodide", lock)
    print("Wheels …")
    # Kernen indlæses ved opstart. PDF-delen hentes bagefter i baggrunden (research R005).
    manifest = {"pyodide": LAAS["pyodide"]["version"], "kerne": kerne_wheel(SITE / "py"),
                "pdf": {"pakker": pakker, "wheels": pdf_wheels(SITE / "py")}}
    (SITE / "py" / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for f in LAAS.get("fil", []):
        shutil.copy(hent(f["url"], f["sha256"]), SITE / f["navn"])
    shutil.copytree(STATISK, SITE, dirs_exist_ok=True)
    (SITE / ".nojekyll").touch()  # GitHub Pages: server filerne som de er
    stoerrelse = sum(p.stat().st_size for p in SITE.rglob("*") if p.is_file())
    print(f"Færdig: {SITE} ({stoerrelse / 1e6:.1f} MB)")


if __name__ == "__main__":
    byg()
