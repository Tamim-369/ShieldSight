import customtkinter as ctk
import threading
import sys
import os
import json
from monitor import main, stop_monitoring, load_model, loading_complete, loading_error, set_nsfw_threshold, NSFW_THRESHOLD
from utils import setup_auto_start, get_close_tab_action, set_close_tab_action
import pystray
from pystray import Menu, MenuItem
from PIL import Image, ImageTk
import platform
import time
import argparse
from pathlib import Path
import ctypes
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Set appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

__version__ = "1.0"
__publisher__ = "Automnex Team"
__publish_date__ = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class App:
    def __init__(self, root: ctk.CTk) -> None:
        self.root = root
        self.root.title(f"Guard v{__version__}")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Hide window initially and sync state
        self.root.withdraw()
        self.root.update()

        # Determine script path (handle PyInstaller)
        self.script_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])

        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
        if os.path.exists(icon_path):
            try:
                if platform.system() == "Windows":
                    self.root.wm_iconbitmap(icon_path)
                icon_img = Image.open(icon_path).convert("RGB")
                photo = ImageTk.PhotoImage(icon_img.resize((16, 16), Image.Resampling.LANCZOS))
                self.root.iconphoto(True, photo)
            except Exception as e:
                logging.error(f"Failed to set icon: {e}")
        else:
            logging.warning(f"Icon file not found at: {icon_path}")

        self.running_thread = None
        self.run_in_background = ctk.BooleanVar(value=True)
        self.is_visible = False
        self.status = "Stopped"
        self.model_loaded_once = False
        self.last_toggle_time = 0
        self.motivational_url = "https://www.youtube.com/shorts/aq8lM9HMe4E"
        self.enable_redirect = True
        self.parent_mode = False
        self.parent_password = ""
        self.parent_mode_first_time = True

        # Config setup
        self.config_dir = Path.home() / ".Guard"
        self.config_dir.mkdir(exist_ok=True)
        self.config_path = self.config_dir / "config.json"
        self.load_config()

        # Show window only on first run (isStarted=False and not background)
        if not self.isStarted and not getattr(sys, 'background', False):
            self.root.deiconify()
            self.root.update()
            self.is_visible = True
            logging.info("First run: Window shown")
        else:
            self.root.withdraw()
            self.is_visible = False
            logging.info("isStarted=True or background mode, window hidden")

        # Center layout
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Box frame
        self.box_frame = ctk.CTkFrame(
            self.main_frame, fg_color="#1e1e1e", corner_radius=20, border_width=2, border_color="#3a3a3a"
        )
        self.box_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=40)
        self.box_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=0)
        self.box_frame.grid_columnconfigure((0, 1), weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self.box_frame, text=f"Guard v{__version__}", font=ctk.CTkFont("Segoe UI", 24, weight="bold"), text_color="white"
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(10, 5), padx=10, sticky="n")

        # Status
        self.status_label = ctk.CTkLabel(
            self.box_frame, text=f"Status: {self.status}", font=ctk.CTkFont("Segoe UI", 14), text_color="lightgray"
        )
        self.status_label.grid(row=1, column=0, columnspan=2, pady=(0, 10), padx=10, sticky="n")

        # Start/Stop Button
        self.start_stop_button = ctk.CTkButton(
            self.box_frame, text="Start", command=self.toggle_monitoring, width=220, height=50,
            font=ctk.CTkFont("Segoe UI", 18, weight="bold"), corner_radius=12, fg_color="#2e89ff", hover_color="#1e5fc1"
        )
        self.start_stop_button.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="n")

        # Loader/Error Label
        self.loader_label = ctk.CTkLabel(self.box_frame, text="", font=ctk.CTkFont("Segoe UI", 12))
        self.loader_label.grid(row=3, column=0, columnspan=2, pady=(0, 10), padx=10, sticky="n")

        # Background checkbox
        self.background_check = ctk.CTkCheckBox(
            self.box_frame, text="Run in Background", variable=self.run_in_background, command=self.update_background,
            font=ctk.CTkFont("Segoe UI", 12), checkbox_height=22, checkbox_width=22, corner_radius=6, border_width=2
        )
        self.background_check.grid(row=4, column=0, columnspan=2, pady=10, padx=10, sticky="n")

        # Footer
        self.footer = ctk.CTkLabel(
            self.box_frame, text="© 2025 Guard", font=ctk.CTkFont("Segoe UI", 10), text_color="#888"
        )
        self.footer.grid(row=5, column=0, columnspan=2, pady=(15, 5), padx=10, sticky="n")

        # Settings Button
        self.settings_button = ctk.CTkButton(
            self.box_frame, text="⚙", command=self.open_settings, width=30, height=30,
            font=ctk.CTkFont("Segoe UI", 14), fg_color="transparent", hover_color="#3a3a3a", corner_radius=15
        )
        self.settings_button.grid(row=0, column=1, pady=(10, 5), padx=(0, 10), sticky="ne")

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.setup_tray()

        # Auto-start monitoring if isStarted=True
        if self.isStarted and self.status != "Running":
            logging.info("isStarted=True, starting monitoring immediately")
            self.start_monitoring()

    def load_config(self) -> None:
        global NSFW_THRESHOLD
        default_config = {
            "nsfw_threshold": 0.5,
            "close_tab_action": ["Ctrl", "w"],
            "isStarted": False,
            "motivational_url": "https://www.youtube.com/shorts/8SVZLF75P2M",
            "enable_redirect": True,
            "parent_mode": False,
            "parent_password": "",
            "parent_mode_first_time": True
        }
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    NSFW_THRESHOLD = float(config.get("nsfw_threshold", default_config["nsfw_threshold"]))
                    close_tab_action = config.get("close_tab_action", default_config["close_tab_action"])
                    self.isStarted = config.get("isStarted", default_config["isStarted"])
                    self.motivational_url = config.get("motivational_url", default_config["motivational_url"])
                    self.enable_redirect = config.get("enable_redirect", default_config["enable_redirect"])
                    self.parent_mode = config.get("parent_mode", default_config["parent_mode"])
                    self.parent_password = config.get("parent_password", default_config["parent_password"])
                    self.parent_mode_first_time = config.get("parent_mode_first_time", default_config["parent_mode_first_time"])
                    set_close_tab_action(close_tab_action)
                    logging.info(f"Loaded config: nsfw_threshold={NSFW_THRESHOLD}, close_tab_action={close_tab_action}, isStarted={self.isStarted}, motivational_url={self.motivational_url}, enable_redirect={self.enable_redirect}, parent_mode={self.parent_mode}, parent_mode_first_time={self.parent_mode_first_time}")
            else:
                logging.info("Config file not found, creating with defaults")
                self.isStarted = default_config["isStarted"]
                NSFW_THRESHOLD = default_config["nsfw_threshold"]
                self.motivational_url = default_config["motivational_url"]
                self.enable_redirect = default_config["enable_redirect"]
                self.parent_mode = default_config["parent_mode"]
                self.parent_password = default_config["parent_password"]
                self.parent_mode_first_time = default_config["parent_mode_first_time"]
                set_close_tab_action(default_config["close_tab_action"])
                self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)
        except Exception as e:
            logging.error(f"Error loading config from {self.config_path}: {e}, using defaults")
            self.isStarted = default_config["isStarted"]
            NSFW_THRESHOLD = default_config["nsfw_threshold"]
            self.motivational_url = default_config["motivational_url"]
            self.enable_redirect = default_config["enable_redirect"]
            self.parent_mode = default_config["parent_mode"]
            self.parent_password = default_config["parent_password"]
            self.parent_mode_first_time = default_config["parent_mode_first_time"]
            set_close_tab_action(default_config["close_tab_action"])
            self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)

    def save_config(self, threshold: float, close_tab_action: list, is_started: bool, motivational_url: str, enable_redirect: bool, parent_mode: bool, parent_password: str, parent_mode_first_time: bool) -> None:
        try:
            config = {
                "nsfw_threshold": float(threshold),
                "close_tab_action": close_tab_action,
                "isStarted": bool(is_started),
                "motivational_url": motivational_url,
                "enable_redirect": enable_redirect,
                "parent_mode": parent_mode,
                "parent_password": parent_password,
                "parent_mode_first_time": parent_mode_first_time
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logging.info(f"Saved config to {self.config_path}: {config}")
        except Exception as e:
            logging.error(f"Error saving config to {self.config_path}: {e}")

    def setup_tray(self) -> None:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
        image = Image.open(icon_path).resize((16, 16), Image.Resampling.LANCZOS) if os.path.exists(icon_path) else Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        menu = Menu(
            MenuItem("Toggle Window", self.toggle_window),
            MenuItem("Exit", self.exit_app),
            MenuItem(f"Status: {self.status}", lambda icon, item: None, enabled=False)
        )
        self.icon = pystray.Icon("Guard", image, "Guard", menu)
        self.icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        self.icon_thread.start()

    def update_tray_status(self) -> None:
        if hasattr(self, 'icon') and self.icon:
            self.icon.menu = Menu(
                MenuItem("Toggle Window", self.toggle_window),
                MenuItem("Exit", self.exit_app),
                MenuItem(f"Status: {self.status}", lambda icon, item: None, enabled=False)
            )
            self.icon.update_menu()

    def toggle_window(self, icon=None, item=None) -> None:
        current_time = time.time()
        if current_time - self.last_toggle_time < 0.5:
            logging.debug("Toggle debounced")
            return
        self.last_toggle_time = current_time

        actual_visible = self.root.winfo_viewable()
        if self.is_visible != actual_visible:
            logging.warning(f"State mismatch: is_visible={self.is_visible}, actual_visible={actual_visible}")
            self.is_visible = actual_visible

        if self.is_visible:
            self.root.withdraw()
            self.root.update()
            self.is_visible = False
            logging.info("Window hidden via toggle")
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.update()
            self.is_visible = True
            logging.info("Window shown via toggle")

    def exit_app(self, icon=None, item=None) -> None:
        stop_monitoring()
        if self.running_thread and self.running_thread.is_alive():
            self.running_thread.join(timeout=2)
        self.save_config(NSFW_THRESHOLD, get_close_tab_action(), False, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)
        if hasattr(self, 'icon'):
            self.icon.stop()
        self.root.destroy()
        sys.exit(0)

    def open_settings(self) -> None:
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            return
        self.settings_window: ctk.CTkToplevel = ctk.CTkToplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("400x400")
        self.settings_window.transient(self.root)
        self.settings_window.grab_set()

        for row in range(7):
            self.settings_window.grid_rowconfigure(row, weight=1)
        self.settings_window.grid_columnconfigure(0, weight=1)
        self.settings_window.grid_columnconfigure(1, weight=1)

        action_label = ctk.CTkLabel(self.settings_window, text="Close Tab Action:", font=ctk.CTkFont("Segoe UI", 14), text_color="white")
        action_label.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        action_entry = ctk.CTkEntry(self.settings_window, font=ctk.CTkFont("Segoe UI", 12))
        action_entry.insert(0, "+".join(get_close_tab_action()))
        action_entry.grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        sensitivity_label = ctk.CTkLabel(self.settings_window, text="Sensitivity Threshold (as %):", font=ctk.CTkFont("Segoe UI", 14), text_color="white")
        sensitivity_label.grid(row=1, column=0, pady=10, padx=10, sticky="w")
        sensitivity_entry = ctk.CTkEntry(self.settings_window, font=ctk.CTkFont("Segoe UI", 12))
        sensitivity_entry.insert(0, str(int(NSFW_THRESHOLD * 100)))
        sensitivity_entry.grid(row=1, column=1, pady=10, padx=10, sticky="ew")

        redirect_label = ctk.CTkLabel(self.settings_window, text="Motivational Redirect URL:", font=ctk.CTkFont("Segoe UI", 14), text_color="white")
        redirect_label.grid(row=2, column=0, pady=10, padx=10, sticky="w")
        redirect_entry = ctk.CTkEntry(self.settings_window, font=ctk.CTkFont("Segoe UI", 12))
        redirect_entry.insert(0, self.motivational_url)
        redirect_entry.grid(row=2, column=1, pady=10, padx=10, sticky="ew")

        enable_redirect_var = ctk.BooleanVar(value=self.enable_redirect)
        enable_redirect_check = ctk.CTkCheckBox(self.settings_window, text="Enable Motivational Redirect", variable=enable_redirect_var, font=ctk.CTkFont("Segoe UI", 12))
        enable_redirect_check.grid(row=3, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        parent_mode_var = ctk.BooleanVar(value=self.parent_mode)
        parent_mode_check = ctk.CTkCheckBox(self.settings_window, text="Enable Parent Mode", variable=parent_mode_var, font=ctk.CTkFont("Segoe UI", 12))
        parent_mode_check.grid(row=4, column=0, columnspan=2, pady=10, padx=10, sticky="w")

        def on_get_report():
            # Ensure monitoring is stopped before generating the report
            if self.status == "Running":
                self.toggle_monitoring()  # Only stop if running
                self.isStarted = False
                self.status = "Stopped"
                self.status_label.configure(text=f"Status: {self.status}")
                self.start_stop_button.configure(text="Start", state="normal")
                self.loader_label.configure(text="")
                self.update_tray_status()
                self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)
            # Prompt for password
            import tkinter.simpledialog
            pw = tkinter.simpledialog.askstring("Parent Password", "Enter parent password:", show='*', parent=self.settings_window)
            if pw == self.parent_password:
                from utils.parent_report import generate_parent_report_pdf
                generate_parent_report_pdf()
            else:
                import tkinter.messagebox
                tkinter.messagebox.showerror("Error", "Incorrect password.")

        get_report_button = ctk.CTkButton(self.settings_window, text="Get Report", command=on_get_report, width=100, height=30, font=ctk.CTkFont("Segoe UI", 12, weight="bold"), fg_color="#2e89ff", hover_color="#1e5fc1")
        if self.parent_mode:
            get_report_button.grid(row=5, column=0, columnspan=2, pady=10, padx=10, sticky="n")

        save_button = ctk.CTkButton(
            self.settings_window, text="Save", command=lambda: self.save_action(action_entry.get(), sensitivity_entry.get(), redirect_entry.get(), enable_redirect_var.get(), parent_mode_var.get(), self.settings_window),
            width=100, height=30, font=ctk.CTkFont("Segoe UI", 12, weight="bold"), fg_color="#2e89ff", hover_color="#1e5fc1"
        )
        save_button.grid(row=6, column=0, columnspan=2, pady=10, padx=10, sticky="n")

    def save_action(self, action_str: str, sensitivity_str: str, redirect_url: str, enable_redirect: bool, parent_mode: bool, settings_window: ctk.CTkToplevel) -> None:
        try:
            global NSFW_THRESHOLD
            threshold = NSFW_THRESHOLD
            if sensitivity_str.strip():
                # Convert percent to float
                threshold_percent = float(sensitivity_str)
                if not 0 <= threshold_percent <= 100:
                    raise ValueError("Threshold must be between 0 and 100")
                threshold = threshold_percent / 100.0
                set_nsfw_threshold(threshold)
                NSFW_THRESHOLD = threshold
                logging.info(f"Updated NSFW_THRESHOLD to {threshold}")

            close_tab_action = get_close_tab_action()
            if action_str.strip():
                keys = [k.strip().lower() if k.lower() in ["ctrl", "alt", "shift"] else k.upper() for k in action_str.split("+")]
                if not any(k.lower() in {"ctrl", "alt", "shift", "win", "cmd"} for k in keys) or not any(k.lower() not in {"ctrl", "alt", "shift", "win", "cmd"} for k in keys):
                    raise ValueError("Action must include a modifier and a key")
                set_close_tab_action(keys)
                close_tab_action = keys
                logging.info(f"Updated close_tab_action to {keys}")

            self.motivational_url = redirect_url.strip()
            self.enable_redirect = enable_redirect
            # Handle parent mode password prompt
            if parent_mode and not self.parent_mode:
                # Enabling parent mode for the first time
                import tkinter.simpledialog
                pw1 = tkinter.simpledialog.askstring("Set Parent Password", "Set a parent password:", show='*', parent=settings_window)
                pw2 = tkinter.simpledialog.askstring("Confirm Password", "Confirm parent password:", show='*', parent=settings_window)
                if pw1 != pw2 or not pw1:
                    import tkinter.messagebox
                    tkinter.messagebox.showerror("Error", "Passwords do not match or are empty.")
                    return
                self.parent_password = pw1
                self.parent_mode_first_time = False
            self.parent_mode = parent_mode
            self.save_config(threshold, close_tab_action, self.isStarted, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)
            settings_window.destroy()
        except ValueError as e:
            error_label = ctk.CTkLabel(settings_window, text=str(e), font=ctk.CTkFont("Segoe UI", 12), text_color="red")
            error_label.grid(row=7, column=0, columnspan=2, pady=5)

    def start_monitoring(self) -> None:
        if self.status == "Running":
            logging.info("Monitoring already running, skipping start")
            return

        self.status = "Starting"
        self.status_label.configure(text=f"Status: {self.status}")
        self.start_stop_button.configure(state="disabled")
        self.update_tray_status()
        self.root.update()
        logging.info("Starting model loading and monitoring")

        def load_model_thread():
            try:
                start_time = time.time()
                load_model()
                elapsed_time = time.time() - start_time
                self.root.after(0, lambda: self.handle_model_loaded(elapsed_time))
            except Exception as e:
                self.root.after(0, lambda: self.handle_model_error(str(e)))

        self.running_thread = threading.Thread(target=load_model_thread, daemon=True)
        self.running_thread.start()

    def handle_model_loaded(self, elapsed_time: float) -> None:
        if loading_error:
            self.handle_model_error(loading_error)
        else:
            logging.info(f"Model loaded in {elapsed_time:.2f} seconds")
            self.model_loaded_once = True
            # Pass motivational_url and enable_redirect and parent_mode to monitor
            import monitor.monitor as monitor_mod
            monitor_mod.MOTIVATIONAL_URL = self.motivational_url
            monitor_mod.ENABLE_REDIRECT = self.enable_redirect
            monitor_mod.PARENT_MODE = self.parent_mode
            monitor_mod.PARENT_REPORT_PATH = str(self.config_dir / "parent_report.json")
            monitor_mod.PARENT_SCREENSHOT_DIR = str(self.config_dir / "screenshots")
            self.running_thread = threading.Thread(target=main, daemon=True)
            self.running_thread.start()
            self.status = "Running"
            self.status_label.configure(text=f"Status: {self.status}")
            self.start_stop_button.configure(text="Stop", state="normal")
            self.loader_label.configure(text=f"Model loaded in {elapsed_time:.2f} seconds", text_color="green")
            self.update_tray_status()
            if self.run_in_background.get():
                setup_auto_start(True, self.script_path)
                if self.is_visible:
                    self.toggle_window()
            self.isStarted = True
            self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)

    def handle_model_error(self, error_msg: str) -> None:
        self.status = "Stopped"
        self.status_label.configure(text=f"Status: {self.status}")
        self.loader_label.configure(text=f"Error: {error_msg}", text_color="red")
        self.start_stop_button.configure(state="normal")
        self.update_tray_status()
        logging.error(f"Model loading error: {error_msg}")

    def toggle_monitoring(self) -> None:
        if self.status == "Running":
            stop_monitoring()
            if self.running_thread and self.running_thread.is_alive():
                self.running_thread.join(timeout=2)
            self.running_thread = None
            self.status = "Stopped"
            self.status_label.configure(text=f"Status: {self.status}")
            self.start_stop_button.configure(text="Start", state="normal")
            self.loader_label.configure(text="")
            self.update_tray_status()
            self.isStarted = False
            self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)
            logging.info("Monitoring stopped")
        else:
            self.start_monitoring()

    def update_background(self) -> None:
        setup_auto_start(self.run_in_background.get(), self.script_path)
        if not self.run_in_background.get() and self.status == "Running":
            self.toggle_monitoring()
            self.toggle_window()
        self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted, self.motivational_url, self.enable_redirect, self.parent_mode, self.parent_password, self.parent_mode_first_time)

    def on_closing(self) -> None:
        if self.run_in_background.get() and self.status == "Running":
            self.toggle_window()
        else:
            self.exit_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", action="store_true", help="Run in background mode")
    args = parser.parse_args()

    if args.background:
        setattr(sys, 'background', True)

    root = ctk.CTk()
    app = App(root)
    root.mainloop()