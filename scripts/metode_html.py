"""Metodebeskrivelsen (docs/metode.md) som en side i løsningen (feature 039). Kun standardbiblioteket.

Kilden er én: docs/metode.md, som revisionen læser på GitHub. Siden i løsningen er den samme tekst uden
det rent tekniske:

- Alt mellem `<!-- teknisk -->` og `<!-- /teknisk -->` udelades (også midt i en linje). Kommentarerne ses
  ikke på GitHub.
- Links til filer i repositoriet bliver til almindelig tekst. Links til nettet beholdes.
- Kodeformatering (backticks) bliver til almindelig tekst. Testen sikrer, at der ikke står kodenavne tilbage.

Konverteren kan kun det, dokumentet bruger: overskrifter, afsnit, punkt- og nummerlister, tabeller,
kodeblokke, citater, vandrette linjer, fed, kursiv, kode og links.
"""
from __future__ import annotations

import html
import re

TEKNISK = re.compile(r"<!-- teknisk -->.*?<!-- /teknisk -->", re.DOTALL)
# En hel linje (eller flere), der er teknisk, fjernes med linjeskiftet, så fx en tabel ikke brydes.
TEKNISK_LINJER = re.compile(r"^[ \t]*<!-- teknisk -->(?:(?!<!-- /teknisk -->).)*<!-- /teknisk -->[ \t]*\n",
                            re.DOTALL | re.MULTILINE)
KOMMENTAR = re.compile(r"<!--.*?-->", re.DOTALL)
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
KODE = re.compile(r"`([^`]+)`")
FED = re.compile(r"\*\*(.+?)\*\*")
KURSIV = re.compile(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])")
OVERSKRIFT = re.compile(r"^(#{1,4})\s+(.*)$")
PUNKT = re.compile(r"^(\s*)-\s+(.*)$")
NUMMER = re.compile(r"^(\s*)\d+\.\s+(.*)$")


def slug(tekst: str) -> str:
    """Ankre som GitHubs: små bogstaver, tegnsætning fjernes, mellemrum bliver bindestreger."""
    t = re.sub(r"<[^>]+>", "", tekst).strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


# Featurenumre (fx "feature 010", "017c", "033/033b/037") er projektets interne mærker. I en parentes alene
# fjernes hele parentesen, ellers kun numrene.
_NR = r"0\d{2}[a-z]?"
FEATURE_PARENTES = re.compile(rf"\s*\((?:features?\s+)?{_NR}(?:\s*(?:/|,|og)\s*{_NR})*\)")
FEATURE_I_PARENTES = re.compile(rf"(?:,\s*|\s+)(?:features?\s+)?{_NR}(?:\s*(?:/|,|og)\s*{_NR})*(?=[,)])")


def ren(md: str) -> str:
    """Markdown uden det tekniske (afsnittet øverst)."""
    md = TEKNISK_LINJER.sub("", md)
    md = TEKNISK.sub("", md)
    md = KOMMENTAR.sub("", md)
    md = FEATURE_PARENTES.sub("", md)
    md = FEATURE_I_PARENTES.sub("", md)
    return md


def _inline(t: str) -> str:
    koder: list[str] = []

    def gem_kode(m: re.Match) -> str:
        koder.append(m.group(1))
        return f"\x00{len(koder) - 1}\x00"

    t = KODE.sub(gem_kode, t)
    t = html.escape(t, quote=False)

    def link(m: re.Match) -> str:
        tekst, maal = m.group(1), m.group(2)
        if maal.startswith(("http://", "https://")):
            return f'<a href="{html.escape(maal)}" rel="noopener">{tekst}</a>'
        if maal.startswith("#"):
            return f'<a href="{html.escape(maal)}">{tekst}</a>'
        return tekst  # en fil i repositoriet: kun teksten

    t = LINK.sub(link, t)
    t = FED.sub(r"<strong>\1</strong>", t)
    t = KURSIV.sub(r"<em>\1</em>", t)
    return re.sub("\x00(\\d+)\x00", lambda m: html.escape(koder[int(m.group(1))], quote=False), t)


def _tabel(linjer: list[str]) -> str:
    def celler(linje: str) -> list[str]:
        return [c.strip() for c in linje.strip().strip("|").split("|")]

    hoved, *raekker = [celler(x) for x in linjer if not re.match(r"^\s*\|?\s*:?-{3,}", x)]
    th = "".join(f"<th scope=\"col\">{_inline(c)}</th>" for c in hoved)
    tr = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in raekker)
    # tabindex: en tabel, der kan rulle vandret, skal kunne nås med tastaturet (WCAG 2.1.1).
    return f'<div class="tabel-rul" tabindex="0"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def til_html(md: str) -> tuple[str, list[tuple[int, str, str]]]:
    """(HTML, overskrifter) for markdown uden det tekniske. Overskrifterne er (niveau, tekst, anker)."""
    linjer = ren(md).splitlines()
    ud: list[str] = []
    overskrifter: list[tuple[int, str, str]] = []
    i = 0
    while i < len(linjer):
        linje = linjer[i]
        if not linje.strip():
            i += 1
            continue
        if linje.startswith("```"):
            j = i + 1
            while j < len(linjer) and not linjer[j].startswith("```"):
                j += 1
            ud.append('<pre tabindex="0">' + html.escape("\n".join(linjer[i + 1:j]), quote=False) + "</pre>")
            i = j + 1
            continue
        if m := OVERSKRIFT.match(linje):
            niveau, tekst = len(m.group(1)), _inline(m.group(2))
            anker = slug(tekst)
            overskrifter.append((niveau, tekst, anker))
            ud.append(f'<h{niveau} id="{anker}">{tekst}</h{niveau}>')
            i += 1
            continue
        if re.match(r"^-{3,}\s*$", linje):
            ud.append("<hr>")
            i += 1
            continue
        if linje.lstrip().startswith("|"):
            j = i
            while j < len(linjer) and linjer[j].lstrip().startswith("|"):
                j += 1
            ud.append(_tabel(linjer[i:j]))
            i = j
            continue
        if linje.startswith(">"):
            j = i
            while j < len(linjer) and linjer[j].startswith(">"):
                j += 1
            ud.append("<blockquote><p>" + _inline(" ".join(x.lstrip("> ").strip() for x in linjer[i:j])) + "</p></blockquote>")
            i = j
            continue
        if PUNKT.match(linje) or NUMMER.match(linje):
            html_liste, i = _liste(linjer, i)
            ud.append(html_liste)
            continue
        j = i
        afsnit = []
        while j < len(linjer) and linjer[j].strip() and not (
                OVERSKRIFT.match(linjer[j]) or PUNKT.match(linjer[j]) or NUMMER.match(linjer[j])
                or linjer[j].lstrip().startswith("|") or linjer[j].startswith(("```", ">"))):
            afsnit.append(linjer[j].strip())
            j += 1
        ud.append("<p>" + _inline(" ".join(afsnit)) + "</p>")
        i = j
    return "\n".join(ud), overskrifter


def _liste(linjer: list[str], i: int) -> tuple[str, int]:
    """En liste fra linje i. Fortsættelseslinjer er indrykket; et indrykket punkt er en underliste."""
    nummereret = bool(NUMMER.match(linjer[i]) and not PUNKT.match(linjer[i]))
    indryk = len(linjer[i]) - len(linjer[i].lstrip())
    punkter: list[str] = []
    while i < len(linjer):
        linje = linjer[i]
        m = PUNKT.match(linje) if not nummereret else (None if PUNKT.match(linje) else NUMMER.match(linje))
        if not m or len(m.group(1)) != indryk:
            break
        tekst = [m.group(2)]
        under = ""
        i += 1
        while i < len(linjer) and linjer[i].strip():
            n = PUNKT.match(linjer[i]) or NUMMER.match(linjer[i])
            dybde = len(linjer[i]) - len(linjer[i].lstrip())
            if n and dybde > indryk:
                under_html, i = _liste(linjer, i)
                under += under_html
                continue
            if n or dybde <= indryk:
                break
            tekst.append(linjer[i].strip())
            i += 1
        punkter.append(f"<li>{_inline(' '.join(tekst))}{under}</li>")
        if i < len(linjer) and not linjer[i].strip():
            # Tom linje: listen fortsætter kun, hvis næste linje er et punkt på samme niveau.
            k = i + 1
            n = (NUMMER if nummereret else PUNKT).match(linjer[k]) if k < len(linjer) else None
            if n and len(n.group(1)) == indryk and not (nummereret and PUNKT.match(linjer[k])):
                i = k
                continue
            break
    tag = "ol" if nummereret else "ul"
    return f"<{tag}>" + "".join(punkter) + f"</{tag}>", i


SIDE = """<!doctype html>
<html lang="da">
<head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titel} – Pensionsoverblik</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='10' fill='%23123845'/%3E%3Ccircle cx='16' cy='16' r='7' fill='%23f0c46a'/%3E%3C/svg%3E">
  <link rel="stylesheet" href="app.css">
  <script src="saadan-fungerer.js" defer></script>
</head>
<body>
  <a class="spring-over" href="#indhold">Gå til indhold</a>
  <header class="topbjaelke">
    <div class="ramme topbjaelke__indhold">
      <a class="logo" href="./"><span class="logo__maerke" aria-hidden="true"></span>Pensionsoverblik</a>
      <button type="button" class="knap knap--sekundaer tilbage-til-beregningen" id="tilbage-til-beregningen">Tilbage til beregningen</button>
    </div>
  </header>
  <main id="indhold" class="metodedok">
    <div class="ramme">
{indledning}
      <p class="metodedok__intro">Den fulde beskrivelse til revision, med henvisninger til koden, findes i
        <a href="https://github.com/Jaisper/PensionsAnalytikerSDD/blob/main/{kilde}" rel="noopener">projektets dokumentation</a>.{andre}</p>
      <nav class="metodedok__indhold" aria-label="Indhold"><h2>Indhold</h2>{indhold}</nav>
{tekst}
    </div>
  </main>
  <footer class="bund"><div class="ramme"><p><strong>Pensionsoverblik</strong> er information, ikke rådgivning.
</p></div></footer>
</body>
</html>
"""


# Siderne i løsningen: (kilde i repositoriet, side i løsningen, titel). 041: udviklingsmetoden ved siden af metoden.
SIDER = (
    ("docs/metode.md", "saadan-fungerer.html", "Sådan fungerer løsningen"),
    ("docs/udviklingsmetode.md", "saadan-udvikles.html", "Sådan udvikles løsningen"),
)


def side(md: str, kilde: str = SIDER[0][0]) -> str:
    """Siden for `kilde` (en af SIDER). Den henviser til den fulde tekst og til de andre sider."""
    _, _, titel = next(s for s in SIDER if s[0] == kilde)
    tekst, overskrifter = til_html(md)
    # Titel og indledning først, så indholdsfortegnelsen, så afsnittene.
    i = tekst.find("<h2 ")
    indledning, afsnit = (tekst[:i], tekst[i:]) if i >= 0 else (tekst, "")
    indhold = "<ul>" + "".join(f'<li><a href="#{a}">{t}</a></li>' for n, t, a in overskrifter if n == 2) + "</ul>"
    andre = "".join(f' Se også <a class="metodedok__anden" href="{fil}">{html.escape(t)}</a>.' for k, fil, t in SIDER if k != kilde)
    return (SIDE.replace("{titel}", html.escape(titel)).replace("{kilde}", kilde).replace("{andre}", andre)
            .replace("{indledning}", indledning).replace("{indhold}", indhold).replace("{tekst}", afsnit))
