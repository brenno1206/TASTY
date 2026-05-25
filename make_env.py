import os
import subprocess

powershell_script = r"""
if (-Not (Test-Path "venv")) {
    py -m venv venv
}

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

. .\\venv\Scripts\Activate.ps1

py -m pip install --upgrade pip
pip install invoke
pip install dotenv
"""

linux_macos_script = r"""
#!/bin/bash

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

python -m pip install --upgrade pip
pip install invoke
pip install dotenv
"""

if os.name == "nt":
    script_name = "temp_script.ps1"

    with open(script_name, "w", encoding="utf-8") as f:
        f.write(powershell_script)

    subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_name], check=True
    )

    os.remove(script_name)

else:
    script_name = "temp_script.sh"

    with open(script_name, "w", encoding="utf-8") as f:
        f.write(linux_macos_script)

    os.chmod(script_name, 0o755)

    subprocess.run(["bash", script_name], check=True)

    os.remove(script_name)
