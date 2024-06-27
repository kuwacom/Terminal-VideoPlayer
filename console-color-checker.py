import os
import sys

def supports_color():
    if sys.platform == 'win32':
        # Windows supports color in cmd or powershell from Windows 10
        return os.getenv('ANSICON') is not None or \
            os.getenv('WT_SESSION') is not None or \
            os.getenv('ConEmuANSI') == 'ON' or \
            os.getenv('TERM_PROGRAM') == 'vscode'
    elif sys.platform == 'linux' or sys.platform == 'darwin':
        # Linux and macOS terminal generally support color
        return True
    return False

print(f"Supports color: {supports_color()}")
