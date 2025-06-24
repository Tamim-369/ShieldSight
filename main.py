import customtkinter as ctk
import threading
import sys
import os
import json
from monitor import main, stop_monitoring, load_model, loading_complete, loading_error, set_nsfw_threshold, NSFW_THRESHOLD
from utils import setup_auto_start, check_existing_process, get_close_tab_action, set_close_tab_action
import pystray
from pystray import Menu, MenuItem
from PIL import Image, ImageTk
import platform
import time
import argparse
from pathlib import Path
import ctypes

# Set appearance and theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

__version__ = "1.0"
__publisher__ = "Automnex Team"
__publish_date__ = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

class App:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()  # Hide main window by default
        self.root.title(f"ShieldSight v{__version__}")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
        if os.path.exists(icon_path):
            try:
                self.root.wm_iconbitmap(icon_path)  # for .ico window icon
                icon_img = Image.open(icon_path).convert("RGB")
                photo = ImageTk.PhotoImage(icon_img.resize((16, 16), Image.Resampling.LANCZOS))
                self.root.iconphoto(True, photo)  # taskbar + alt+tab icon
            except Exception as e:
                print(f"Failed to set icon: {e}")
        else:
            print(f"Icon file not found at: {icon_path}, skipping icon")
        self.running_thread = None
        self.run_in_background = ctk.BooleanVar(value=True)
        self.script_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__)) + ('/main.exe' if getattr(sys, 'frozen', False) else sys.argv[0])
        self.is_visible = False
        self.status = "Stopped"
        self.loading_progress = 0
        self.loading_in_progress = False
        self.model_loaded_once = False
        self.loader_frames = ["|", "/", "-", "\\"]  # Text-based spinner
        self.loader_index = 0

        # Create .shieldsight directory and config path
        self.config_dir = Path.home() / ".shieldsight"
        self.config_dir.mkdir(exist_ok=True)
        self.config_path = self.config_dir / "config.json"
        self.load_config()

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
        self.box_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=0)
        self.box_frame.grid_columnconfigure((0, 1), weight=1)

        # Title Label
        self.title_label = ctk.CTkLabel(
            self.box_frame,
            text=f"ShieldSight v{__version__}",
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
            text="© 2025 ShieldSight",
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

        # Initial setup or automatic start
        if not os.path.exists(self.config_path):
            self.show_restart_prompt()
        elif getattr(sys, 'background', False) and self.isStarted and not self.running_thread:
            self.hide_window(None, None)
            self.toggle_monitoring()  # Auto-start monitoring after restart

    def load_config(self):
        global NSFW_THRESHOLD
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    NSFW_THRESHOLD = float(config.get("nsfw_threshold", 0.01))
                    close_tab_action = config.get("close_tab_action", ["Ctrl", "w"])
                    self.isStarted = config.get("isStarted", False)
                    set_close_tab_action(close_tab_action)
                    print(f"Loaded config: nsfw_threshold={NSFW_THRESHOLD}, close_tab_action={close_tab_action}, isStarted={self.isStarted}")
            else:
                self.isStarted = False
                NSFW_THRESHOLD = 0.01
                set_close_tab_action(["Ctrl", "w"])
                self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted)
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            self.isStarted = False
            NSFW_THRESHOLD = 0.01
            set_close_tab_action(["Ctrl", "w"])
            self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted)

    def save_config(self, threshold, close_tab_action, is_started):
        try:
            config = {
                "nsfw_threshold": float(threshold),
                "close_tab_action": close_tab_action if close_tab_action else ["Ctrl", "w"],
                "isStarted": bool(is_started)
            }
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
            print(f"Saved config: {config}")
        except Exception as e:
            print(f"Error saving config: {e}")

    def show_loading_dialog(self):
        loading_dialog = ctk.CTkToplevel()
        loading_dialog.title("Loading Model")
        loading_dialog.geometry("300x100")
        loading_dialog.resizable(False, False)
        loading_dialog.transient(self.root)
        loading_dialog.grab_set()

        label = ctk.CTkLabel(loading_dialog, text="Loading Model...", font=ctk.CTkFont("Segoe UI", 12))
        label.pack(pady=20)

        def update_loader():
            if self.loading_in_progress:
                self.loader_index = (self.loader_index + 1) % len(self.loader_frames)
                label.configure(text=f"Loading Model... {self.loader_frames[self.loader_index]}")
                loading_dialog.after(200, update_loader)

        loading_dialog.after(200, update_loader)
        return loading_dialog

    def show_restart_prompt(self):
        restart_dialog = ctk.CTkToplevel()
        restart_dialog.title("Setup Required")
        restart_dialog.geometry("300x150")
        restart_dialog.resizable(False, False)
        restart_dialog.transient(self.root)
        restart_dialog.grab_set()

        label = ctk.CTkLabel(restart_dialog, text="You need to restart your PC to run this app properly.", font=ctk.CTkFont("Segoe UI", 12))
        label.pack(pady=20)

        ok_button = ctk.CTkButton(restart_dialog, text="OK", command=lambda: [restart_dialog.destroy(), self.restart_pc()], font=ctk.CTkFont("Segoe UI", 12), fg_color="#2e89ff", hover_color="#1e5fc1")
        ok_button.pack(pady=10)

        restart_dialog.mainloop()  # Use dialog's mainloop to block until closed

    def restart_pc(self):
        ctypes.windll.shell32.ShellExecuteW(None, "runas", "shutdown", "/r /t 0", None, 0)  # Restart immediately

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
        self.icon = pystray.Icon("ShieldSight", image, "ShieldSight", menu)
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
        self.save_config(NSFW_THRESHOLD, get_close_tab_action(), False)  # Reset isStarted on exit
        self.icon.stop()
        self.root.destroy()
        sys.exit(0)

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x200")  # Adjusted size
        settings_window.transient(self.root)
        settings_window.update_idletasks()
        settings_window.grab_set()

        # Configure window to be resizable
        settings_window.grid_rowconfigure(0, weight=1)
        settings_window.grid_rowconfigure(1, weight=1)
        settings_window.grid_rowconfigure(2, weight=1)
        settings_window.grid_columnconfigure(0, weight=1)
        settings_window.grid_columnconfigure(1, weight=1)

        # Close Tab Action
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

        # Sensitivity Threshold
        sensitivity_label = ctk.CTkLabel(
            settings_window,
            text="Sensitivity Threshold (0-1):",
            font=ctk.CTkFont("Segoe UI", 14),
            text_color="white"
        )
        sensitivity_label.grid(row=1, column=0, pady=10, padx=10, sticky="w")

        sensitivity_entry = ctk.CTkEntry(
            settings_window,
            font=ctk.CTkFont("Segoe UI", 12),
            placeholder_text=str(NSFW_THRESHOLD)  # Use current NSFW_THRESHOLD
        )
        sensitivity_entry.grid(row=1, column=1, pady=10, padx=10, sticky="ew")

        # Save Button
        save_button = ctk.CTkButton(
            settings_window,
            text="Save",
            command=lambda: self.save_action(action_entry.get(), sensitivity_entry.get(), sensitivity_entry, action_entry, settings_window),
            width=100,
            height=30,
            font=ctk.CTkFont("Segoe UI", 12, weight="bold"),
            fg_color="#2e89ff",
            hover_color="#1e5fc1"
        )
        save_button.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="n")

    def save_action(self, action_str, sensitivity_str, sensitivity_entry, action_entry, window):
        try:
            # Validate and save sensitivity threshold first
            threshold_updated = False
            if sensitivity_str:
                threshold = float(sensitivity_str)
                if not 0 <= threshold <= 1:
                    raise ValueError("Threshold must be between 0 and 1")
                set_nsfw_threshold(threshold)  # Update in program
                threshold_updated = True
            elif not threshold_updated:
                set_nsfw_threshold(0.01)  # Default if empty

            # Validate and save close tab action
            action_updated = False
            if action_str.strip():
                keys = [k.strip().lower() if k.lower() in ["ctrl", "alt", "shift"] else k.upper() for k in action_str.split("+")]
                if not keys or any(not k for k in keys):
                    raise ValueError("Invalid action format. Use format like 'Ctrl+Shift+Q' or 'Alt+F4'")
                valid_modifiers = {"ctrl", "alt", "shift", "win", "cmd"}
                valid_keys = {chr(i) for i in range(ord('a'), ord('z')+1)} | {str(i) for i in range(1, 13)} | {"f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "esc", "w", "q"}
                if not any(k.lower() in valid_modifiers for k in keys) or not any(k.lower() not in valid_modifiers for k in keys):
                    raise ValueError("Action must include at least one modifier (Ctrl, Alt, Shift) and one key (a-z, F1-F12, Esc, W, Q)")
                set_close_tab_action(keys)
                action_entry.configure(placeholder_text=action_str)
                action_updated = True
            elif not action_updated:
                set_close_tab_action(["Ctrl", "w"])
                action_entry.configure(placeholder_text="Ctrl+w")

            # Save all to config
            self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted)

            window.destroy()
        except ValueError as e:
            ctk.CTkLabel(
                window,
                text=str(e),
                font=ctk.CTkFont("Segoe UI", 12),
                text_color="red"
            ).grid(row=3, column=0, columnspan=2, pady=5)
            if "Threshold" not in str(e) and not threshold_updated:
                set_nsfw_threshold(0.01)  # Reset only if action error and threshold not set
            if "Action" in str(e) and not action_updated:
                set_close_tab_action(["Ctrl", "w"])
                action_entry.configure(placeholder_text="Ctrl+w")

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
                self.show_loading_dialog()
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
                self.isStarted = True
                self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted)
        else:
            stop_monitoring()
            if self.running_thread:
                self.running_thread.join(timeout=2)
            self.status = "Stopped"
            self.status_label.configure(text=f"Status: {self.status}")
            self.start_stop_button.configure(text="Start")
            self.check_existing_process()
            self.isStarted = False
            self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted)

    def show_progress_bar(self):
        def update_loader():
            if self.loading_in_progress:
                self.loader_index = (self.loader_index + 1) % len(self.loader_frames)
                self.loading_dialog_label.configure(text=f"Loading Model... {self.loader_frames[self.loader_index]}")
                self.loading_dialog.after(200, update_loader)

        def update_progress(value, message):
            print(f"Progress: {value}, Message: {message}")  # Debug print
            if value == 0:
                self.loading_dialog.after(200, update_loader)  # Start animation
            if value == 100:
                self.loading_in_progress = False
                self.loading_dialog.destroy()  # Dismiss dialog
                if loading_error:
                    ctk.CTkLabel(self.box_frame, text=f"Error: {loading_error}", font=ctk.CTkFont("Segoe UI", 12), text_color="red").grid(row=3, column=0, columnspan=2, pady=10, padx=10)
                else:
                    self.model_loaded_once = True
                    self.start_stop_button.configure(state="normal")
                    self.toggle_monitoring()
                self.root.update()

        self.loading_dialog = self.show_loading_dialog()
        self.loading_dialog_label = self.loading_dialog.children["!label"]
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
        self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted)

    def on_closing(self):
        self.save_config(NSFW_THRESHOLD, get_close_tab_action(), self.isStarted)
        if self.run_in_background.get() and self.status == "Running":
            self.hide_window(None, None)
        else:
            stop_monitoring()
            if self.running_thread:
                self.running_thread.join(timeout=2)
            self.root.destroy()
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--background", action="store_true", help="Run in background mode")
    args = parser.parse_args()

    # Set background flag for auto-start
    if args.background:
        setattr(sys, 'background', True)

    root = ctk.CTk()
    app = App(root)

    if args.background and app.isStarted:
        app.hide_window(None, None)
        if not app.running_thread or not app.running_thread.is_alive():
            app.toggle_monitoring()
    else:
        app.root.mainloop()