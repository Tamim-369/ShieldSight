import os
import json
from datetime import datetime
from pathlib import Path
from fpdf import FPDF
import webbrowser
import platform

# Try to use CustomTkinter's file dialog, fallback to tkinter if not available
try:
    import customtkinter as ctk
    filedialog = ctk.filedialog
except ImportError:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    ctk = None
    # Note: fallback to tkinter dialog if CustomTkinter dialog is not available

def generate_parent_report_pdf():
    home = Path.home()
    guard_dir = home / ".Guard"
    report_json = guard_dir / "parent_report.json"
    screenshot_dir = guard_dir / "screenshots"
    downloads_dir = Path.home() / "Downloads"
    default_pdf_name = "Guard_Report.pdf"

    if not report_json.exists():
        if ctk:
            ctk.CTkMessageBox(title="Error", message="No parent report log found.")
        else:
            messagebox.showerror("Error", "No parent report log found.")
        return

    with open(report_json, "r") as f:
        events = json.load(f)

    # Prompt user for save location using CustomTkinter or fallback
    pdf_path = None
    if ctk:
        root = ctk.CTk()
        root.withdraw()
        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=downloads_dir,
            initialfile=default_pdf_name,
            title="Save Parent Report PDF"
        )
        root.destroy()
    else:
        root = tk.Tk()
        root.withdraw()
        pdf_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=downloads_dir,
            initialfile=default_pdf_name,
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
    for event in events:
        # Format time as HH:MM:SS for the event title
        try:
            dt = datetime.strptime(event['timestamp'], "%Y-%m-%d_%H-%M-%S")
            time_str = dt.strftime("%H:%M:%S")
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            time_str = event['timestamp']
            date_str = event['timestamp']
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, time_str, ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 8, f"Date: {date_str}", ln=True)
        pdf.cell(0, 8, f"Content Type: {event.get('content_type', 'NSFW')}", ln=True)
        pdf.cell(0, 8, f"NSFW Score: {event['score']}", ln=True)
        screenshot_path = str(screenshot_dir / event['screenshot'])
        file_url = f"file://{screenshot_path}"
        # Add clickable link for screenshot
        pdf.set_text_color(0, 0, 255)
        pdf.cell(0, 8, f"Screenshot: {screenshot_path}", ln=True, link=file_url)
        pdf.set_text_color(0, 0, 0)
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
            if ctk:
                ctk.CTkMessageBox(title="Report Saved", message=f"Report saved to {pdf_path}")
            else:
                messagebox.showinfo("Report Saved", f"Report saved to {pdf_path}") 