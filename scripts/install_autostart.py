import os
import sys
from pathlib import Path

def setup_autostart():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        print("Error: APPDATA environment variable not found")
        return False
    startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    startup_dir.mkdir(parents=True, exist_ok=True)
    
    vbs_path = startup_dir / "TVHub_Autostart.vbs"
    py_exe = sys.executable
    repo_dir = Path(__file__).resolve().parent.parent
    
    vbs_script = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{repo_dir}"
WshShell.Run """{py_exe}"" run.py", 0, False
'''
    vbs_path.write_text(vbs_script, encoding="ascii")
    print(f"Successfully installed TV Hub silent autostart to: {vbs_path}")
    print(f"Startup working directory: {repo_dir}")
    print(f"Python executable: {py_exe}")
    return True

if __name__ == "__main__":
    setup_autostart()
