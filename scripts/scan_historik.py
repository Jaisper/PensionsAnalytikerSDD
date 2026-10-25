"""Scanner hele git-historikken for persondata og hemmeligheder (feature 005, D8).

Køres før repoet gøres offentligt. Fundne værdier skrives ALDRIG ud — kun commit, fil, linje og
hvilken slags fund det er.

Brug:
    uv run python scripts/scan_historik.py [--rapport STI_TIL_RIGTIG_RAPPORT.pdf]

Med --rapport læses navn, CPR-nummer, aftale- og depotnumre fra en rigtig PensionsInfo-rapport
(kun i hukommelsen), og historikken gennemsøges for netop de værdier.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pensionsoverblik.pdfimport.tekst import cpr_foedselsdato  # noqa: E402

CPR_BINDESTREG = re.compile(r"(?<![\d-])\d{6}-\d{4}(?![\d-])")
TI_CIFRE = re.compile(r"(?<![\d.,-])\d{10}(?![\d.,-])")
NOEGLER = {
    "Anthropic-nøgle": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "OpenAI-nøgle": re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{32,}"),
    "GitHub-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "AWS-nøgle": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Privat nøgle": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
# Kendte, fiktive værdier i tests (fx depotnummeret i den syntetiske rapport).
KENDT_FIKTIV = {"1002114321"}


def git(*args: str, input: bytes | None = None) -> bytes:
    return subprocess.run(["git", *args], capture_output=True, check=True, input=input).stdout


def blobs() -> dict[str, set[tuple[str, str]]]:
    """Alle blobs i hele historikken → {(commit, sti)}."""
    hvor: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for commit in git("rev-list", "--all").decode().split():
        for linje in git("ls-tree", "-r", commit).decode("utf-8", "replace").splitlines():
            meta, sti = linje.split("\t", 1)
            _, typ, sha = meta.split()
            if typ == "blob":
                hvor[sha].add((commit[:8], sti))
    return hvor


def laes_blob(sha: str) -> bytes:
    return git("cat-file", "blob", sha)


def fra_rapport(sti: Path) -> dict[str, set[str]]:
    """Værdier fra en rigtig rapport, der ikke må findes i historikken. Kun i hukommelsen."""
    import io

    import pdfplumber

    from pensionsoverblik.pdfimport.aflaeser import vaelg_aflaeser

    data = sti.read_bytes()
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        tekst = "\n".join(s.extract_text() or "" for s in pdf.pages)
        forside = pdf.pages[0].extract_text() or ""
    vaerdier: dict[str, set[str]] = defaultdict(set)
    for m in re.finditer(r"Pensionsoplysninger for[ \t]*(.*)\n?(.*)", forside):
        navn = (m.group(1) or m.group(2)).strip()
        if len(navn.split()) >= 2:
            vaerdier["navn"].add(navn)
            vaerdier["efternavn"].add(navn.split()[-1])
    for m in re.finditer(r"\d{6}-[\dxX*]{4}", forside):
        vaerdier["cpr"].add(m.group(0)[:6])
    for o in vaelg_aflaeser().aflaes(data).ordninger:
        if o.aftalenr and len(re.sub(r"\D", "", o.aftalenr)) >= 5:
            vaerdier["aftalenr"].add(o.aftalenr)
    vaerdier["10-cifret nummer fra rapporten"] |= set(TI_CIFRE.findall(tekst))
    return vaerdier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapport", type=Path)
    args = ap.parse_args()
    specifikke = fra_rapport(args.rapport) if args.rapport else {}
    print("Værdier fra rapporten:", {k: len(v) for k, v in specifikke.items()} or "ingen")

    hvor = blobs()
    print(f"Scanner {len(hvor)} filversioner i {len(git('rev-list', '--all').split())} commits …")
    fund: dict[tuple[str, str, int], set[str]] = defaultdict(set)
    for sha, steder in hvor.items():
        indhold = laes_blob(sha)
        sti = sorted(steder)[0][1]
        if sti.lower().endswith(".pdf"):
            fund[(sti, sha[:8], 0)].add("PDF-fil")
            continue
        if b"\0" in indhold[:8000]:
            continue
        tekst = indhold.decode("utf-8", "replace")
        for nr, linje in enumerate(tekst.splitlines(), 1):
            for m in CPR_BINDESTREG.finditer(linje):
                if cpr_foedselsdato(m.group(0)):
                    fund[(sti, sha[:8], nr)].add("CPR-nummer (gyldig dato)")
            for m in TI_CIFRE.finditer(linje):
                if m.group(0) not in KENDT_FIKTIV and cpr_foedselsdato(m.group(0)):
                    fund[(sti, sha[:8], nr)].add("10 cifre med gyldig CPR-dato")
            for art, mønster in NOEGLER.items():
                if mønster.search(linje):
                    fund[(sti, sha[:8], nr)].add(art)
            for art, vaerdier in specifikke.items():
                if any(v in linje for v in vaerdier):
                    fund[(sti, sha[:8], nr)].add(f"RAPPORT: {art}")

    if not fund:
        print("Ingen fund.")
        return 0
    print(f"{len(fund)} fund (værdier vises ikke):")
    for (sti, sha, nr), arter in sorted(fund.items()):
        commits = ", ".join(sorted(c for c, s in hvor_for(hvor, sha)))
        print(f"  {sti}:{nr}  [{', '.join(sorted(arter))}]  blob {sha}  commits {commits}")
    return 1


def hvor_for(hvor: dict[str, set[tuple[str, str]]], kort_sha: str) -> set[tuple[str, str]]:
    return next(v for k, v in hvor.items() if k.startswith(kort_sha))


if __name__ == "__main__":
    sys.exit(main())
