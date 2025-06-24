import os
import logging
from pathlib import Path
import platform

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def setup_auto_start(enable: bool, script_path: str) -> None:
    system = platform.system()
    app_name = "ShieldSight"
    
    if system == "Windows":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if enable:
                command = f'"{script_path}" --background'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
                logging.info(f"Windows auto-start enabled with command: {command}")
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                    logging.info("Windows auto-start disabled")
                except FileNotFoundError:
                    logging.debug("Windows auto-start entry not found, no action needed")
            winreg.CloseKey(key)
        except OSError as e:
            logging.error(f"Error setting up Windows auto-start: {e}")
    
    elif system == "Linux":
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop_file = autostart_dir / "shieldsight.desktop"
        
        if enable:
            # Determine if running as PyInstaller executable or Python script
            if script_path.endswith(".exe") or getattr(sys, 'frozen', False):
                command = f'"{script_path}" --background'
            else:
                command = f'python3 "{script_path}" --background'
            
            desktop_content = f"""[Desktop Entry]
Type=Application
Name={app_name}
Exec={command}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            try:
                with open(desktop_file, "w") as f:
                    f.write(desktop_content)
                os.chmod(desktop_file, 0o755)  # Make executable
                logging.info(f"Linux auto-start enabled with .desktop file: {desktop_file}")
            except OSError as e:
                logging.error(f"Error creating Linux auto-start .desktop file: {e}")
        else:
            try:
                if desktop_file.exists():
                    desktop_file.unlink()
                    logging.info("Linux auto-start disabled")
                else:
                    logging.debug("Linux auto-start .desktop file not found, no action needed")
            except OSError as e:
                logging.error(f"Error removing Linux auto-start .desktop file: {e}")
    
    else:
        logging.warning(f"Auto-start not supported on platform: {system}")

# Existing functions (unchanged)
def get_close_tab_action() -> list:
    return ["Ctrl", "w"]  # Placeholder, replace with actual implementation

def set_close_tab_action(keys: list) -> None:
    pass  # Placeholder, replace with actual implementation