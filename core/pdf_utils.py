def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_simple_pdf(title: str, lines: list[str]) -> bytes:
    # Minimal PDF generator for plain text reports (A4-ish layout).
    content_lines = ["BT", "/F1 14 Tf", "40 800 Td", f"({_escape_pdf_text(title)}) Tj", "0 -22 Td", "/F1 10 Tf"]
    line_count = 0
    for line in lines:
        safe = _escape_pdf_text(line[:120])
        content_lines.append(f"({safe}) Tj")
        content_lines.append("0 -14 Td")
        line_count += 1
        if line_count >= 48:
            break
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj")
    objects.append(f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj")

    pdf = bytearray(b"%PDF-1.4\n")
    xref_positions = [0]
    for obj in objects:
        xref_positions.append(len(pdf))
        pdf.extend(obj)
        pdf.extend(b"\n")
    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(xref_positions)}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for pos in xref_positions[1:]:
        pdf.extend(f"{pos:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        f"trailer << /Size {len(xref_positions)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("latin-1")
    )
    return bytes(pdf)

