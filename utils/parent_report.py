import os
import json
from datetime import datetime
from pathlib import Path
from fpdf import FPDF
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser
import platform

def generate_parent_report_pdf():
    home = Path.home()
    guard_dir = home / ".Guard"
    report_json = guard_dir / "parent_report.json"
    screenshot_dir = guard_dir / "screenshots"
    # Default to Downloads
    downloads_dir = Path.home() / "Downloads"
    default_pdf_path = downloads_dir / "Guard_Report.pdf"

    if not report_json.exists():
        messagebox.showerror("Error", "No parent report log found.")
        return

    with open(report_json, "r") as f:
        events = json.load(f)

    # Prompt user for save location
    root = tk.Tk()
    root.withdraw()
    pdf_path = filedialog.asksaveasfilename(
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
        initialdir=downloads_dir,
        initialfile="Guard_Report.pdf",
        title="Save Parent Report PDF"
    )
    root.destroy()
    if not pdf_path:
        return  # User cancelled

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

    # Open the PDF in the default viewer
    try:
        if platform.system() == "Windows":
            os.startfile(pdf_path)
        elif platform.system() == "Darwin":
            os.system(f"open '{pdf_path}'")
        else:
            os.system(f"xdg-open '{pdf_path}'")
    except Exception:
        try:
            webbrowser.open_new_tab(f"file://{pdf_path}")
        except Exception:
            messagebox.showinfo("Report Saved", f"Report saved to {pdf_path}") 