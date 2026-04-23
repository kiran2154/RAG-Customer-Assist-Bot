from pathlib import Path
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


DOC_MAP = {
    "HLD.md": "HLD.pdf",
    "LLD.md": "LLD.pdf",
    "TECHNICAL_DOCUMENTATION.md": "Technical_Documentation.pdf",
}


def write_line(pdf: canvas.Canvas, text: str, y: int, font_name: str, font_size: int) -> int:
    pdf.setFont(font_name, font_size)
    pdf.drawString(42, y, text)
    return y - (font_size + 4)


def markdown_to_pdf(markdown_path: Path, output_path: Path) -> None:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()

    pdf = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    y = height - 42

    title = markdown_path.stem.replace("_", " ")
    y = write_line(pdf, title, y, "Helvetica-Bold", 16)
    y -= 6

    in_code_block = False

    for raw_line in lines:
        line = raw_line.rstrip()

        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if y < 50:
            pdf.showPage()
            y = height - 42

        if in_code_block:
            wrapped = textwrap.wrap(line if line else " ", 95) or [" "]
            for part in wrapped:
                if y < 50:
                    pdf.showPage()
                    y = height - 42
                y = write_line(pdf, part, y, "Courier", 8)
            continue

        if line.startswith("# "):
            y = write_line(pdf, line[2:].strip(), y, "Helvetica-Bold", 14)
            continue

        if line.startswith("## "):
            y = write_line(pdf, line[3:].strip(), y, "Helvetica-Bold", 12)
            continue

        if line.startswith("### "):
            y = write_line(pdf, line[4:].strip(), y, "Helvetica-Bold", 11)
            continue

        wrapped = textwrap.wrap(line if line else " ", 110) or [" "]
        for part in wrapped:
            if y < 50:
                pdf.showPage()
                y = height - 42
            y = write_line(pdf, part, y, "Helvetica", 10)

    pdf.save()


def main() -> None:
    docs_dir = Path("docs")

    for md_name, pdf_name in DOC_MAP.items():
        md_path = docs_dir / md_name
        if not md_path.exists():
            raise FileNotFoundError(f"Missing source markdown: {md_path}")

        output_path = docs_dir / pdf_name
        markdown_to_pdf(md_path, output_path)
        print(f"Generated {output_path}")


if __name__ == "__main__":
    main()
