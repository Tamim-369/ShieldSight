import os
import sys
import psutil
import platform
from pathlib import Path

def check_existing_process(script_path):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if script_path in ' '.join(proc.info['cmdline'] or []):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def setup_auto_start(enable, script_path):
    if platform.system() == "Windows":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
        try:
            if enable:
                venv_python = Path(sys.executable).absolute()
                winreg.SetValueEx(key, "NSFWScreenMonitor", 0, winreg.REG_SZ, f'"{venv_python}" "{script_path}"')
            else:
                winreg.DeleteValue(key, "NSFWScreenMonitor")
        except Exception:
            pass
        finally:
            winreg.CloseKey(key)
    else:  # Linux
        autostart_dir = Path.home() / ".config/autostart"
        autostart_dir.mkdir(exist_ok=True)
        desktop_file = autostart_dir / "nsfw-screen-monitor.desktop"
        if enable:
            with open(desktop_file, "w") as f:
                f.write("[Desktop Entry]\n")
                f.write("Name=NSFW Screen Monitor\n")
                f.write(f"Exec=/usr/bin/python3 {script_path}\n")
                f.write("Type=Application\n")
                f.write("Terminal=false\n")
                f.write("Hidden=false\n")
                f.write("NoDisplay=false\n")
                f.write("X-GNOME-Autostart-enabled=true\n")
        elif desktop_file.exists():
            os.remove(desktop_file)