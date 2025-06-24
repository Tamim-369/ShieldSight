import winreg
import os
import psutil
import logging
import sys

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

def check_existing_process(script_path: str) -> bool:
    try:
        current_pid = os.getpid()
        script_name = os.path.basename(script_path).lower()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.pid != current_pid and proc.name().lower() == script_name:
                    cmdline = proc.cmdline()
                    if cmdline and any(script_path.lower() in arg.lower() for arg in cmdline):
                        logging.info(f"Found existing process: PID={proc.pid}, cmdline={cmdline}")
                        return True
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        logging.debug("No existing process found")
        return False
    except Exception as e:
        logging.error(f"Error checking existing process: {e}")
        return False