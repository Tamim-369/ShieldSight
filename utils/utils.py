import winreg
import os
import logging
import psutil

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

def check_existing_process(script_path):
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            if script_path in ' '.join(proc.info['cmdline'] or []):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False


def setup_auto_start(enable: bool, script_path: str) -> None:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        app_name = "ShieldSight"
        if enable:
            # Include --background flag in the command
            command = f'"{script_path}" --background'
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
            logging.info(f"Auto-start enabled with command: {command}")
        else:
            try:
                winreg.DeleteValue(key, app_name)
                logging.info("Auto-start disabled")
            except FileNotFoundError:
                logging.debug("Auto-start entry not found, no action needed")
        winreg.CloseKey(key)
    except OSError as e:
        logging.error(f"Error setting up auto-start: {e}")