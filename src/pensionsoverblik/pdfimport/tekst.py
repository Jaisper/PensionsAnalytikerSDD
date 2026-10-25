"""PDF → tekst, sidefilter og CPR-fjernelse. Alt sker lokalt og i hukommelsen (FR-001, FR-002)."""
from __future__ import annotations

import io
import logging
import re
from datetime import date

import pdfplumber

# pdfminer logger harmløse font-advarsler for mange PensionsInfo-rapporter.
logging.getLogger("pdfminer").setLevel(logging.ERROR)

RELEVANTE_NOEGLEORD = (
    "Pensionsoplysninger for", "Nuværende pensionsopsparinger", "Dine aftaler",
    "flere oplysninger", "yderligere oplysninger", "Tidligst mulig pensionsalder",
    "Tidligst udbetaling", "Tidligste pensionsalder", "tidligste pensionsalder",
    "Du kan tidligst", "Opsparingsalder", "Hvis du går på pension som", "Udbetaling",
)

CPR = re.compile(r"\b(\d{2})(\d{2})(\d{2})-?(\d{4})\b")
CPR_ERSTATNING = "[CPR fjernet]"


class PdfFejl(ValueError):
    def __init__(self, kode: str, besked: str):
        super().__init__(besked)
        self.kode = kode
        self.besked = besked


def udtraek_sider(data: bytes) -> list[str]:
    if not data.startswith(b"%PDF-"):
        raise PdfFejl("ikke_pdf", "Filen er ikke en PDF. Hent rapporten som PDF fra pensionsinfo.dk.")
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            sider = [side.extract_text() or "" for side in pdf.pages]
    except Exception:
        raise PdfFejl("ulaeselig", "PDF'en kunne ikke læses. Prøv at hente en ny rapport fra pensionsinfo.dk.") from None
    if not any(s.strip() for s in sider):
        raise PdfFejl("ingen_tekst", "Vi kunne ikke finde tekst i PDF'en. Den er måske scannet. "
                                     "Hent rapporten som PDF direkte fra pensionsinfo.dk.")
    return sider


def relevante_sider(sider: list[str]) -> str:
    """Kun sider om ordninger og udbetaling sendes videre (mindre data, færre tokens)."""
    valgte = [f"=== SIDE {i + 1} ===\n{s}" for i, s in enumerate(sider) if any(n in s for n in RELEVANTE_NOEGLEORD)]
    if not valgte:
        valgte = [f"=== SIDE {i + 1} ===\n{s}" for i, s in enumerate(sider) if s.strip()]
    return "\n\n".join(valgte)


def cpr_foedselsdato(cpr: str) -> date | None:
    """Fødselsdato af et CPR-nummer. Århundredet afgøres af 7. ciffer (CPR-kontorets regel)."""
    cifre = re.sub(r"\D", "", cpr)
    if len(cifre) != 10:
        return None
    dd, mm, aa, syvende = int(cifre[0:2]), int(cifre[2:4]), int(cifre[4:6]), int(cifre[6])
    if syvende <= 3:
        aarhundrede = 1900
    elif syvende in (4, 9):
        aarhundrede = 2000 if aa <= 36 else 1900
    else:
        aarhundrede = 2000 if aa <= 57 else 1800
    try:
        return date(aarhundrede + aa, mm, dd)
    except ValueError:
        return None


MASKERET_CPR = re.compile(r"\b(\d{2})(\d{2})(\d{2})-[xX*]{4}\b")
UDSKREVET = re.compile(r"Udskrevet:\s*\d{1,2}\.\s*\w+\s+(\d{4})")
MAKS_ALDER = 110


CPR_MED_BINDESTREG = re.compile(r"\b\d{6}-\d{4}\b")


def foedselsdato_fra_rapport(forside: str) -> date | None:
    """Fødselsdato fra rapportens forside: fuldt CPR-nummer (DDMMÅÅ-NNNN) eller PensionsInfos
    maskerede form (DDMMÅÅ-xxxx). Kun forsiden og kun formen med bindestreg bruges — rapporten
    indeholder 10-cifrede aftale- og depotnumre, der ellers kan forveksles med et CPR-nummer.

    Uden 7. ciffer vælges det århundrede, der giver en alder mellem 0 og 110 år i rapportens
    udskriftsår.
    """
    if (m := CPR_MED_BINDESTREG.search(forside)) and (fuld := cpr_foedselsdato(m.group(0))):
        return fuld
    m = MASKERET_CPR.search(forside)
    u = UDSKREVET.search(forside)
    if not m or not u:
        return None
    dd, mm, aa, rapportaar = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(u.group(1))
    for aarhundrede in (2000, 1900):
        if 0 <= rapportaar - (aarhundrede + aa) <= MAKS_ALDER:
            try:
                return date(aarhundrede + aa, mm, dd)
            except ValueError:
                return None
    return None


def fjern_cpr(tekst: str) -> tuple[str, date | None]:
    """Erstatter alle gyldige CPR-numre og returnerer den første fødselsdato."""
    foedt: list[date] = []

    def erstat(m: re.Match) -> str:
        d = cpr_foedselsdato(m.group(0))
        if d is None:
            return m.group(0)
        foedt.append(d)
        return CPR_ERSTATNING

    return CPR.sub(erstat, tekst), (foedt[0] if foedt else None)
