# Configuration storage
CONFIG = {
    "close_tab_action": ["ctrl", "w"]  # Default: Ctrl+W
}

def get_close_tab_action():
    """Return the current close tab action as a list of keys."""
    return CONFIG["close_tab_action"]

def set_close_tab_action(keys):
    """Set the close tab action from a list of keys."""
    if isinstance(keys, list) and all(isinstance(k, str) for k in keys):
        CONFIG["close_tab_action"] = keys
    else:
        raise ValueError("Action must be a list of strings")