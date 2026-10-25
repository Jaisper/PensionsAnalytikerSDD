"""Syntetiske PDF'er til test (ingen rigtige rapporter i repoet — og ingen persondata)."""


def lav_pdf(sider: list[list[str]]) -> bytes:
    """Minimal, gyldig PDF med én tekstlinje pr. element (Helvetica, WinAnsi)."""
    objekter: list[bytes] = []

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    n_sider = len(sider)
    font_nr = 3 + 2 * n_sider
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n_sider))
    objekter.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objekter.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_sider} >>".encode())
    for i, linjer in enumerate(sider):
        indhold = "BT /F1 11 Tf 50 800 Td 14 TL " + " ".join(f"({esc(l)}) Tj T*" for l in linjer) + " ET"
        data = indhold.encode("cp1252")
        objekter.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents {4 + 2 * i} 0 R "
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
    for off in offsets:
        ud += f"{off:010d} 00000 n \n".encode()
    ud += f"trailer\n<< /Size {len(objekter) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(ud)


RAPPORT = [
    ["Pensionsoplysninger for Test Testesen", "CPR-nr. 010563-1234", "Udskrevet fra PensionsInfo"],
    ["Nuværende pensionsopsparinger", "Danica Pension  aftale 123456  Ratepension  saldo 1.200.000 kr."],
    ["Side om noget helt andet", "Reklame for fondsopsparing"],
    ["Dine aftaler", "PFA Pension  aftale 98765  Livsvarig pension  indbetaling i alt 30.000 kr.",
     "Tidligst mulig pensionsalder: 63 år"],
]
