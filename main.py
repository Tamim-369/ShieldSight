import customtkinter as ctk
import threading
import sys
import os
from monitor import main, stop_monitoring, load_model, loading_complete, loading_error
from utils import setup_auto_start, check_existing_process, get_close_tab_action, set_close_tab_action
import pystray
from pystray import Menu, MenuItem
from PIL import Image
import platform
import time

# Set appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

__version__ = "1.0"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(f"mindWallX v{__version__}")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")  # Changed to .ico
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print(f"Failed to set iconbitmap: {e}, skipping icon")
        else:
            print(f"Icon file not found at: {icon_path}, skipping icon")
        self.running_thread = None
        self.run_in_background = ctk.BooleanVar(value=True)
        self.script_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__)) + ('/main.exe' if platform.system() == 'Windows' else '/main') if getattr(sys, 'frozen', False) else sys.argv[0]
        self.is_visible = True
        self.status = "Stopped"
        self.loading_progress = 0
        self.loading_in_progress = False
        self.model_loaded_once = False
        self.loader_frames = ["|", "/", "-", "\\"]  # Text-based spinner
        self.loader_index = 0

        # Center layout config
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Beautiful box frame
        self.box_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#1e1e1e",
            corner_radius=20,
            border_width=2,
            border_color="#3a3a3a"
        )
        self.box_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.box_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6), weight=0)  # Added row 6 for potential error
        self.box_frame.grid_columnconfigure((0, 1), weight=1)

        # Title Label
        self.title_label = ctk.CTkLabel(
            self.box_frame,
            text=f"mindWallX v{__version__}",
            font=ctk.CTkFont("Segoe UI", 24, weight="bold"),
            text_color="white"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(10, 5), padx=10, sticky="n")

        # Status Label
        self.status_label = ctk.CTkLabel(
            self.box_frame,
            text=f"Status: {self.status}",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color="lightgray"
        )
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), padx=10, sticky="n")

        # Start/Stop Button
        self.start_stop_button = ctk.CTkButton(
            self.box_frame,
            text="Start",
            command=self.toggle_monitoring,
            width=220,
            height=50,
            font=ctk.CTkFont("Segoe UI", 18, weight="bold"),
            corner_radius=12,
            fg_color="#2e89ff",
            hover_color="#1e5fc1"
        )
        self.start_stop_button.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="n")

        # Loader Label
        self.loader_label = ctk.CTkLabel(self.box_frame, text="", font=ctk.CTkFont("Segoe UI", 12))
        self.loader_label.grid(row=3, column=0, columnspan=2, pady=(0, 10), padx=10, sticky="n")

        # Background checkbox
        self.background_check = ctk.CTkCheckBox(
            self.box_frame,
            text="Run in Background",
            variable=self.run_in_background,
            command=self.update_background,
            font=ctk.CTkFont("Segoe UI", 12),
            checkbox_height=22,
            checkbox_width=22,
            corner_radius=6,
            border_width=2
        )
        self.background_check.grid(row=4, column=0, columnspan=2, pady=10, padx=10, sticky="n")

        # Footer
        self.footer = ctk.CTkLabel(
            self.box_frame,
            text="© 2025 mindWallX",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color="#888"
        )
        self.footer.grid(row=5, column=0, columnspan=2, pady=(15, 5), padx=10, sticky="n")

        # Settings Icon
        self.settings_button = ctk.CTkButton(
            self.box_frame,
            text="⚙",
            command=self.open_settings,
            width=30,
            height=30,
            font=ctk.CTkFont("Segoe UI", 14),
            fg_color="transparent",
            hover_color="#3a3a3a",
            corner_radius=15
        )
        self.settings_button.grid(row=0, column=1, pady=(10, 5), padx=(0, 10), sticky="ne")

        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_tray()
        self.check_existing_process()

    def setup_tray(self):
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
        if os.path.exists(icon_path):
            image = Image.open(icon_path).resize((16, 16), Image.Resampling.LANCZOS)
        else:
            image = Image.new("RGBA", (16, 16), (0, 0, 0, 0))  # Fallback if icon missing
        menu = Menu(
            MenuItem("Show", self.show_window),
            MenuItem("Hide", self.hide_window),
            MenuItem("Exit", self.exit_app),
            MenuItem(f"Status: {self.status}", lambda icon, item: None, enabled=False)
        )
        self.icon = pystray.Icon("mindWallX", image, "mindWallX", menu)
        def on_left_click(icon, data):
            if not self.is_visible:
                self.show_window(icon, None)
        self.icon.on_click = on_left_click
        self.icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.icon_thread.start()

    def update_tray_status(self):
        if hasattr(self, 'icon') and self.icon:
            self.icon.menu = Menu(
                MenuItem("Show", self.show_window),
                MenuItem("Hide", self.hide_window),
                MenuItem("Exit", self.exit_app),
                MenuItem(f"Status: {self.status}", lambda icon, item: None, enabled=False)
            )
            self.icon.update_menu()

    def show_window(self, icon, item):
        if not self.is_visible:
            self.root.deiconify()
            self.is_visible = True

    def hide_window(self, icon, item):
        if self.is_visible:
            self.root.withdraw()
            self.is_visible = False

    def exit_app(self, icon, item):
        stop_monitoring()
        if self.running_thread:
            self.running_thread.join(timeout=2)
        self.icon.stop()
        self.root.destroy()
        sys.exit(0)

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("300x150")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.update_idletasks()
        settings_window.grab_set()

        action_label = ctk.CTkLabel(
            settings_window,
            text="Close Tab Action:",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color="white"
        )
        action_label.grid(row=0, column=0, pady=10, padx=10, sticky="w")

        current_action = "+".join(get_close_tab_action())
        action_entry = ctk.CTkEntry(
            settings_window,
            font=ctk.CTkFont("Segoe UI", 12),
            placeholder_text=current_action
        )
        action_entry.grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        save_button = ctk.CTkButton(
            settings_window,
            text="Save",
            command=lambda: self.save_action(action_entry.get(), settings_window),
            width=100,
            height=30,
            font=ctk.CTkFont("Segoe UI", 12, weight="bold"),
            fg_color="#2e89ff",
            hover_color="#1e5fc1"
        )
        save_button.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="n")

    def save_action(self, action_str, window):
        try:
            keys = [k.strip().lower() if k.lower() in ["ctrl", "alt", "shift"] else k.upper() for k in action_str.split("+")]
            if not keys or any(not k for k in keys):
                raise ValueError("Invalid action format. Use format like 'Ctrl+Shift+Q' or 'Alt+F4'")
            valid_modifiers = {"ctrl", "alt", "shift"}
            valid_keys = {chr(i) for i in range(ord('a'), ord('z')+1)} | {str(i) for i in range(1, 13)} | {"f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "esc", "w", "q"}
            if not any(k.lower() in valid_modifiers for k in keys) or not any(k.lower() not in valid_modifiers for k in keys):
                raise ValueError("Action must include at least one modifier (Ctrl, Alt, Shift) and one key (a-z, F1-F12, Esc, W, Q)")
            set_close_tab_action(keys)
            window.destroy()
        except ValueError as e:
            ctk.CTkLabel(
                window,
                text=str(e),
                font=ctk.CTkFont("Segoe UI", 12),
                text_color="red"
            ).grid(row=2, column=0, columnspan=2, pady=5)

    def check_existing_process(self):
        if check_existing_process(self.script_path):
            if getattr(self, 'running_thread', None) and self.running_thread.is_alive():
                self.status = "Running"
                self.status_label.configure(text=f"Status: {self.status}")
                self.start_stop_button.configure(text="Stop", state="normal")
            else:
                self.status = "Stopped"
                self.status_label.configure(text=f"Status: {self.status}")
                self.start_stop_button.configure(text="Start", state="normal")
        else:
            self.status = "Stopped"
            self.status_label.configure(text=f"Status: {self.status}")
            self.start_stop_button.configure(text="Start", state="normal")
        self.update_tray_status()

    def toggle_monitoring(self):
        if self.start_stop_button.cget("text") == "Start":
            if not loading_complete and not self.loading_in_progress and not self.model_loaded_once:
                self.loading_in_progress = True
                self.start_stop_button.configure(state="disabled")  # Disable button
                self.show_progress_bar()
            elif loading_complete or self.model_loaded_once:
                self.running_thread = threading.Thread(target=main, daemon=True)
                self.running_thread.start()
                self.status = "Running"
                self.status_label.configure(text=f"Status: {self.status}")
                self.start_stop_button.configure(text="Stop")
                self.hide_window(None, None)
                if self.run_in_background.get():
                    setup_auto_start(True, self.script_path)
        else:
            stop_monitoring()
            if self.running_thread:
                self.running_thread.join(timeout=2)
            self.status = "Stopped"
            self.status_label.configure(text=f"Status: {self.status}")
            self.start_stop_button.configure(text="Start")
            self.check_existing_process()

    def show_progress_bar(self):
        self.loader_label.configure(text="Loading Model... |")

        def update_loader():
            if self.loading_in_progress:
                self.loader_index = (self.loader_index + 1) % len(self.loader_frames)
                self.loader_label.configure(text=f"Loading Model... {self.loader_frames[self.loader_index]}")
                self.root.after(200, update_loader)

        def update_progress(value, message):
            if value == 0:
                self.root.after(200, update_loader)  # Start animation
            if value == 100:
                self.loading_in_progress = False
                self.loader_label.configure(text="")  # Clear loader
                if loading_error:
                    ctk.CTkLabel(self.box_frame, text=f"Error: {loading_error}", font=ctk.CTkFont("Segoe UI", 12), text_color="red").grid(row=3, column=0, columnspan=2, pady=10, padx=10)
                else:
                    self.model_loaded_once = True
                    self.start_stop_button.configure(state="normal")
                    self.toggle_monitoring()
                self.root.update()

        load_thread = threading.Thread(target=load_model, args=(update_progress,), daemon=True)
        load_thread.start()

    def update_background(self):
        if not self.run_in_background.get() and self.status == "Running":
            self.hide_window(None, None)
            stop_monitoring()
            if self.running_thread:
                self.running_thread.join(timeout=2)
            self.status = "Stopped"
            self.status_label.configure(text=f"Status: {self.status}")
            self.start_stop_button.configure(text="Start")
        setup_auto_start(self.run_in_background.get(), self.script_path)

    def on_closing(self):
        if self.run_in_background.get() and self.status == "Running":
            self.hide_window(None, None)
        else:
            stop_monitoring()
            if self.running_thread:
                self.running_thread.join(timeout=2)
            self.root.destroy()
            sys.exit(0)

if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()