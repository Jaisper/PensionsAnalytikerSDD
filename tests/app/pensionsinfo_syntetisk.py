"""Syntetisk PensionsInfo-rapport med samme layout som en rigtig rapport (2026), men opdigtede data.

Rigtige rapporter indeholder persondata og må ikke ligge i repoet. Placeringerne her svarer til
dem, parseren læser efter: kolonner på "Dine aftaler", tabellen "Hvis du går på pension som
X-årig får du" og de tætte linjer i venstre kolonne på "Pension - flere oplysninger".
"""
B, H = 842, 596  # liggende A4 i punkter, som rapporten


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def lav_pdf_placeret(sider: list[list[tuple[float, float, str, float]]]) -> bytes:
    """Hver side er en liste af (x, top, tekst, størrelse) — top målt fra sidens overkant."""
    objekter: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>"]
    n = len(sider)
    font_nr = 3 + 2 * n
    objekter.append(f"<< /Type /Pages /Kids [{' '.join(f'{3 + 2 * i} 0 R' for i in range(n))}] /Count {n} >>".encode())
    for i, elementer in enumerate(sider):
        dele = []
        for x, top, tekst, str_ in elementer:
            y = H - top - str_ * 0.8
            dele.append(f"BT /F1 {str_} Tf {x} {y:.2f} Td ({_esc(tekst)}) Tj ET")
        data = "\n".join(dele).encode("cp1252")
        objekter.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {B} {H}] /Contents {4 + 2 * i} 0 R "
                        f"/Resources << /Font << /F1 {font_nr} 0 R >> >> >>".encode())
        objekter.append(f"<< /Length {len(data)} >>\nstream\n".encode() + data + b"\nendstream")
    objekter.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    ud = bytearray(b"%PDF-1.4\n")
    offsets = []
    for nr, obj in enumerate(objekter, start=1):
        offsets.append(len(ud))
        ud += f"{nr} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(ud)
    ud += f"xref\n0 {len(objekter) + 1}\n0000000000 65535 f \n".encode()
    ud += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    ud += f"trailer\n<< /Size {len(objekter) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(ud)


def _linjer(start_top: float, linjer: list[str], x=60, str_=7.0, afstand=12.0):
    return [(x, start_top + i * afstand, l, str_) for i, l in enumerate(linjer)]


FORSIDE = [(650, 450, "Pensionsoplysninger for:", 9), (650, 462, "Test Testesen", 9),
           (650, 485, "150368-xxxx", 9), (650, 505, "Udskrevet:", 9), (650, 517, "01. oktober 2026", 9)]

# Indholdsfortegnelse i højre kolonne; venstre kolonnes brødtekst flettes ind i linjerne (som i
# en rigtig rapport). Sidetallene passer til rækkefølgen i RAPPORT_PDF.
INDHOLD = [(130, 120, "Information", 14), (450, 120, "Indhold", 14),
           (130, 150, "PensionsInfo er en forening af omkring 80", 8), (450, 150, "3 Dine aftaler", 8),
           (130, 162, "pensionskasser og banker.", 8), (450, 162, "4 Hvis du går på pension som 62-årig får du", 8),
           (450, 174, "5 Pension - flere oplysninger", 8), (450, 186, "6 Bilag", 8)]

BILAG = [(60, 30, "Bilag", 14), (60, 60, "Dine aftaler og Pension - flere oplysninger nævnes også her.", 8)]

AFTALER = [
    (60, 30, "Dine aftaler", 14),
    (65, 64, "Leverandør", 6), (211, 64, "Aftalenr.", 6), (356, 64, "Bemærkninger", 6),
    (660, 66, "Årlig", 6), (680, 66, "indbetaling", 6), (747, 66, "Opsparing", 6),
    # ATP
    (211, 93, "ATP Livslang Pension", 6), (356, 93, "Investeringsform: Ingen oplysninger", 6), (688, 94, "3.500kr.", 6),
    (211, 101, "Lovpligtig", 6), (356, 99, "Den årlige indbetaling er opgjort før arbejdsmarkedsbidrag (AMB)", 6),
    (742, 97, "Opgøres ikke", 6),
    # Kun forsikring
    (211, 126, "11111 - 2222", 6), (356, 125, "Investeringsform: Der er ikke leveret oplysninger", 6),
    (211, 134, "Via arbejde", 6), (699, 130, "0kr.", 6), (739, 130, "Kun forsikring", 6),
    # Kapitalpension — saldo på anden linje
    (211, 158, "1234567890", 6), (356, 157, "Investeringsform: Flere investeringsformer", 6), (748, 159, "800.000kr.", 6),
    (211, 166, "Via arbejde", 6), (699, 163, "0kr.", 6), (747, 167, "pr. 01.10.2026", 6),
    # Rate + livsvarig på samme aftale
    (211, 190, "5555555555", 6), (356, 190, "Investeringsform: Markedsrente", 6),
    (680, 192, "100.000kr.", 6), (742, 192, "2.000.000kr.", 6),
    (211, 199, "Via arbejde", 6), (680, 199, "pr. 01.10.2026", 6),
    # Aftale med opsparing, men uden udbetalingsprognose
    (211, 223, "9999999999", 6), (356, 226, "Investeringsform: Markedsrente", 6), (751, 224, "50.000kr.", 6),
    (211, 231, "Via arbejde", 6),
]

SCENARIE = _linjer(30, [
    "Hvis du går på pension som 62-årig får du",
    "Nedenfor ses forløbet af dine pensionsudbetalinger.",
    "Pensioner 62 år 63-69 år Fra 70 år",
    "Folkepension 0 kr. 0 kr. 90.000 kr.",
    "S Folkepension - grundbeløb 0 kr. 0 kr. 90.000 kr. Konstant",
    "Udbetales tidligst fra 69 år",
    "På én gang 500.000 kr. 0 kr. 0 kr.",
    "A Danica 500.000 kr. 0 kr. 0 kr.",
    "1234567890",
    "Kapitalpension",
    "Om året i en årrække 150.000 kr. 150.000 kr. 0 kr.",
    "S Testselskab 150.000 kr. 150.000 kr. 0 kr. Faldende",
    "5555555555",
    "Ratepension Udbetales i 10 år",
    "Om året, så længe du lever 60.000 kr. 60.000 kr. 80.000 kr.",
    "S ATP 0 kr. 0 kr. 20.000 kr. Stigende",
    "ATP Livslang Pension",
    "Livsvarig pension Udbetales tidligst fra 69 år",
    "S Testselskab 60.000 kr. 60.000 kr. 60.000 kr. Faldende",
    "5555555555",
    "Livsvarig pension",
    "I alt årligt: 710.000 kr. 210.000 kr. 170.000 kr.",
])


def _blok(top: float, venstre: list[str], udbetaling: list[str]):
    return ([(65, top + i * 6.6, t, 5.5) for i, t in enumerate(venstre)]
            + [(152, top + i * 7.0, t, 5.5) for i, t in enumerate(udbetaling)])


FLERE = ([(60, 28, "Pension - flere oplysninger", 14), (65, 81, "Leverandør, aftalenr.", 5.5),
          (152, 84, "Udbetaling", 5.5), (312, 84, "Indbetaling", 5.5), (470, 84, "Opsparing", 5.5), (629, 84, "Øvrigt", 5.5),
          (65, 109, "Folkepension S", 5.5), (152, 107, "Vær opmærksom på din folkepensionsalder.", 5.5)]
         + _blok(150, ["Danica", "1234567890 A", "Kapitalpension"],
                 ["Pensionen kan tidligst udbetales ved 60 år.", "Det er aftalt, at pensionen kommer til udbetaling",
                  "ved 65 år (pr. 01.01.2033)."])
         + _blok(200, ["Testselskab", "5555555555", "S", "Ratepension"],
                 ["Pensionen kan tidligst udbetales fra 64 år.", "Det er aftalt, at pensionen kommer til udbetaling",
                  "fra 67 år (pr. 01.04.2035)."])
         + _blok(250, ["Testselskab", "5555555555 S", "Livsvarig", "pension"],
                 ["Pensionen kan tidligst udbetales fra 64 år.", "Det er aftalt, at pensionen kommer til udbetaling",
                  "fra 67 år (pr. 01.04.2035)."])
         + [(92, 560, "S Skattepligtig F Skatte- og afgiftsfri A Afgiftspligtig", 5.5)])

RAPPORT_PDF = lav_pdf_placeret([FORSIDE, INDHOLD, AFTALER, SCENARIE, FLERE, BILAG])
RAPPORT_UDEN_INDHOLD_PDF = lav_pdf_placeret([FORSIDE, AFTALER, SCENARIE, FLERE])


# ── Forsikringer (feature 031) ───────────────────────────────────────────────
# Layout som PensionsInfos demorapport (2026): pr. afsnit en "Overblik"-side med tabellen og en
# "Detaljer"-side med bemærkninger. Skattekoden står til venstre for selskabet; beløbene er
# højrestillede under kolonneoverskrifterne.

_BREDDE = {".": 0.278, " ": 0.278, ",": 0.278, "k": 0.5, "r": 0.333, "-": 0.333}


def _hoejre(x1: float, top: float, tekst: str, str_: float = 7.0):
    """Højrestillet tekst, der slutter ved x1 (Helvetica-bredder, kun tal og 'kr.')."""
    return (x1 - sum(_BREDDE.get(c, 0.556) for c in tekst) * str_, top, tekst, str_)


def _hoved(titel: str, under: str):
    return [(58, 28, titel, 14), (58, 49, under, 9)]


FORKLARING = [(60, 480, "A", 6), (67, 480, "Afgiftspligtig", 6), (136, 480, "F", 6),
              (143, 480, "Skatte- og afgiftsfri", 6), (231, 480, "S", 6), (239, 480, "Skattepligtig", 6)]

SUNDHED = (_hoved("Sundhedsforsikring (2 | 2)", "Detaljer")
           + [(167, 85, "Leverandør, aftalenr.", 7), (306, 85, "Bemærkninger", 7), (734, 83, "Dækningsbeløb", 7),
              (306, 109, "Dækningen ophører ved 67 år (01.03.2033).", 7), (82, 117, "På én gang", 7),
              (167, 120, "Testselskab", 7), _hoejre(780, 123, "100.000 kr."), (167, 127, "7777777777", 7),
              (306, 135, "Dækningen er ikke tegnet med ret til præmiefritagelse.", 7),
              (63, 300, "I alt", 7), _hoejre(780, 300, "100.000 kr.")] + FORKLARING)

DOED = (_hoved("Udbetaling ved død (2 | 3)", "Overblik")
        + [(63, 93, "Modtager", 7), (600, 93, "Om året i en årrække", 7), (726, 93, "På én gang", 7),
           # Ægtefælle: ATP (engangsbeløb) og Danica (ægtefællepension om året)
           (84, 126, "Ægtefælle", 7),
           (99, 143, "ATP", 7), (87, 145, "A", 7), (99, 152, "Dækningsbeløbet", 7), _hoejre(780, 154, "40.000 kr."),
           (99, 158, "nedtrappes.", 7), (99, 166, "ATP Livslang Pension", 7),
           (99, 180, "Danica", 7), (87, 182, "A", 7), _hoejre(690, 190, "60.000 kr."), (99, 189, "Dækker indtil 70 år", 7),
           (99, 197, "1234567890", 7),
           # Begunstiget: Testselskab, procent af lønnen
           (84, 242, "Begunstiget oplyst", 7),
           (99, 259, "Testselskab", 7), (87, 262, "F", 7), (99, 268, "Dækningen", 7),
           (99, 274, "fastsættes som en", 7), (99, 280, "procentdel af din løn.", 7), _hoejre(780, 283, "1.500.000 kr."),
           (99, 300, "Dækker indtil 67 år", 7), (99, 308, "5555555555", 7),
           (63, 377, "I alt:", 7), _hoejre(690, 386, "60.000 kr."), _hoejre(779, 386, "1.540.000 kr.")] + FORKLARING)

DOED_DETALJER = (_hoved("Udbetaling ved død (3 | 3)", "Detaljer")
                 + [(63, 86, "Modtager, leverandør og aftalenr.", 7), (302, 86, "Bemærkninger", 7),
                    (63, 113, "Ægtefælle", 7),
                    (63, 122, "ATP", 7), (302, 122, "Dækningsbeløbet nedtrappes.", 7),
                    (63, 130, "ATP Livslang Pension", 7), (302, 130, "Yderligere oplysninger hos ATP.", 7),
                    (63, 150, "Danica", 7), (302, 150, "Dækningen ophører ved 70 år (01.03.2036).", 7),
                    (63, 158, "1234567890", 7), (302, 158, "Dækningen er ikke tegnet med ret til præmiefritagelse.", 7),
                    (63, 180, "Begunstiget oplyst", 7),
                    (63, 189, "Testselskab", 7), (302, 189, "Dækningen fastsættes som en procentdel af din løn.", 7),
                    (63, 197, "5555555555", 7), (302, 197, "Dækningen ophører ved 67 år (01.03.2033).", 7),
                    (302, 205, "Dækningen er tegnet med ret til præmiefritagelse.", 7)])

TAE = (_hoved("Udbetaling ved tab af arbejdsevne (2 | 3)", "Overblik")
       + [(89, 83, "Pensioner", 7), (638, 83, "Mistet arbejdsevne", 7), (737, 83, "Indtil 67 år", 7),
          (89, 105, "Om året i en årrække", 7), _hoejre(703, 105, "300.000 kr."), _hoejre(775, 105, "300.000 kr."),
          (103, 114, "Testselskab", 7), (91, 116, "S", 7), _hoejre(703, 114, "300.000 kr."), _hoejre(775, 114, "300.000 kr."),
          (103, 123, "5555555555", 7), (103, 133, "Ophørende udbetaling", 7),
          (95, 154, "I alt:", 7), _hoejre(703, 154, "300.000 kr."), _hoejre(775, 154, "300.000 kr.")] + FORKLARING)

TAE_DETALJER = (_hoved("Udbetaling ved tab af arbejdsevne (3 | 3)", "Detaljer")
                + [(63, 86, "Modtager, leverandør og aftalenr.", 7), (302, 86, "Bemærkninger", 7),
                   (63, 113, "Forsikringstager", 7),
                   (63, 122, "Testselskab", 7), (302, 122, "Udbetaling af dækningen ophører senest ved 67 år (pr. 01.03.2033).", 7),
                   (63, 130, "5555555555", 7), (302, 130, "Dækningen ophører ved 67 år (01.03.2033).", 7),
                   (302, 138, "Dækningen er tegnet med ret til præmiefritagelse.", 7)])

KS = (_hoved("Visse kritiske sygdomme (2 | 3)", "Overblik")
      + [(89, 80, "På én gang", 7), _hoejre(775, 80, "150.000 kr."),
         (103, 90, "Testselskab", 7), (91, 91, "F", 7), _hoejre(775, 90, "150.000 kr."),
         (103, 98, "5555555555", 7), (103, 108, "Engangsudbetaling", 7),
         (95, 130, "I alt:", 7), _hoejre(775, 130, "150.000 kr.")] + FORKLARING)

KS_DETALJER = (_hoved("Visse kritiske sygdomme (3 | 3)", "Detaljer")
               + [(63, 86, "Modtager, leverandør og aftalenr.", 7), (302, 86, "Bemærkninger", 7),
                  (63, 113, "Forsikringstager", 7),
                  (63, 122, "Testselskab", 7), (302, 122, "Der er ikke leveret oplysninger om indbetalingen på denne dækning.", 7),
                  (63, 130, "5555555555", 7), (302, 130, "Dækningen ophører ved 67 år (01.03.2033).", 7),
                  (302, 138, "Dækningen er tegnet med ret til præmiefritagelse.", 7)])

KS_BOERN = ([(58, 28, "Visse kritiske sygdomme - børn (3 | 3)", 14), (58, 49, "Hvis du har børn under en vis alder", 9)]
            + [(89, 80, "På én gang", 7), _hoejre(775, 80, "50.000 kr."),
               (103, 90, "Testselskab", 7), (91, 91, "F", 7), _hoejre(775, 90, "50.000 kr."),
               (103, 98, "5555555555", 7), (95, 130, "I alt:", 7), _hoejre(775, 130, "50.000 kr.")] + FORKLARING)

INDHOLD_FORSIKRING = [(130, 120, "Information", 14), (450, 120, "Indhold", 14),
                      (130, 150, "PensionsInfo er en forening af omkring 80", 8), (450, 150, "3 Dine aftaler", 8),
                      (450, 162, "4 Sundhedsforsikring", 8), (450, 174, "5 Udbetalinger ved død", 8),
                      (450, 186, "7 Udbetaling ved tabt arbejdsevne", 8), (450, 198, "9 Visse kritiske sygdomme", 8),
                      (450, 210, "12 Hvis du går på pension som 62-årig får du", 8),
                      (450, 222, "13 Pension - flere oplysninger", 8), (450, 234, "14 Bilag", 8)]

RAPPORT_MED_FORSIKRINGER_PDF = lav_pdf_placeret([
    FORSIDE, INDHOLD_FORSIKRING, AFTALER, SUNDHED, DOED, DOED_DETALJER, TAE, TAE_DETALJER, KS, KS_DETALJER, KS_BOERN,
    SCENARIE, FLERE, BILAG])
# Et forsikringsafsnit med ukendt layout: ingen skattekoder og ingen detaljer.
RAPPORT_MED_UKENDT_FORSIKRING_PDF = lav_pdf_placeret([
    FORSIDE, INDHOLD_FORSIKRING, AFTALER, SUNDHED, _hoved("Udbetaling ved død (2 | 3)", "Overblik") + [(99, 143, "Noget andet", 7)],
    DOED_DETALJER, TAE, TAE_DETALJER, KS, KS_DETALJER, KS_BOERN, SCENARIE, FLERE, BILAG])
