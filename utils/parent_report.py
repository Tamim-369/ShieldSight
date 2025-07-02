import os
import json
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

def generate_parent_report_pdf():
    home = Path.home()
    guard_dir = home / ".Guard"
    report_json = guard_dir / "parent_report.json"
    screenshot_dir = guard_dir / "screenshots"
    reports_dir = guard_dir / "reports"
    pdf_path = reports_dir / "parent_report.pdf"

    if not report_json.exists():
        print("No parent report log found.")
        return

    with open(report_json, "r") as f:
        events = json.load(f)

    os.makedirs(reports_dir, exist_ok=True)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Parent Mode Report", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    for idx, event in enumerate(events):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Event {idx+1}", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Date/Time: {event['timestamp']}", ln=True)
        pdf.cell(0, 8, f"Content Type: {event.get('content_type', 'NSFW')}", ln=True)
        pdf.cell(0, 8, f"NSFW Score: {event['score']}", ln=True)
        screenshot_path = str(screenshot_dir / event['screenshot'])
        pdf.cell(0, 8, f"Screenshot: {screenshot_path}", ln=True)
        pdf.ln(5)

    pdf.output(str(pdf_path))
    print(f"Parent report PDF generated: {pdf_path}") 