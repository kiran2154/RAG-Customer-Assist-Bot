from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


OUTPUT_PATH = Path("data/customer_support_kb.pdf")


SECTIONS = [
    (
        "Account Access",
        [
            "If a user forgets a password, direct them to reset via the login page.",
            "Password reset links expire after 30 minutes.",
            "For locked accounts, support can unlock only after identity verification.",
        ],
    ),
    (
        "Billing and Refunds",
        [
            "Refunds are allowed within 14 days for monthly plans.",
            "Annual plans are prorated only if service outage exceeded 48 hours.",
            "Chargeback disputes are always escalated to a human billing specialist.",
        ],
    ),
    (
        "Service Reliability",
        [
            "Known outages are posted on the status page.",
            "If issue persists after status is green, gather logs and escalate.",
            "Critical production incidents require immediate human intervention.",
        ],
    ),
    (
        "Communication Policy",
        [
            "Never promise compensation before policy confirmation.",
            "If legal language appears in customer message, escalate to human.",
            "Maintain concise and respectful tone in all customer responses.",
        ],
    ),
]


def draw_wrapped_line(pdf: canvas.Canvas, text: str, x: int, y: int, limit: int = 95) -> int:
    words = text.split()
    current = ""
    consumed_lines = 0

    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > limit:
            pdf.drawString(x, y, current)
            y -= 14
            consumed_lines += 1
            current = word
        else:
            current = candidate

    if current:
        pdf.drawString(x, y, current)
        y -= 14
        consumed_lines += 1

    return y


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(OUTPUT_PATH), pagesize=LETTER)
    width, height = LETTER
    y = height - 50

    pdf.setTitle("Customer Support Knowledge Base")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(40, y, "Customer Support Knowledge Base")
    y -= 30

    pdf.setFont("Helvetica", 11)
    for section_title, bullets in SECTIONS:
        if y < 120:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 11)

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(40, y, section_title)
        y -= 18

        pdf.setFont("Helvetica", 11)
        for bullet in bullets:
            if y < 90:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 11)
            y = draw_wrapped_line(pdf, f"- {bullet}", 55, y)

        y -= 10

    pdf.save()
    print(f"Generated sample PDF at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
