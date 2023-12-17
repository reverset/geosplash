import subprocess
import os
import platform

from zipfile import ZipFile

"""
For linux, you need python headers insatlled (ex: dnf install python3.11-devel), or else
Nuitka will complain about a missing python header.

For MacOS, make sure you have imageio installed (pip install imageio)
"""

APP_NAME = "geo"
AS_MODULE = False

plat = platform.system()
if plat == "Windows":
    COMMAND = "nuitka --onefile --windows-icon-from-ico=./icons/Geometry_Splash_Logo.ico ./geo.py"
elif plat == "Linux":
    COMMAND = "nuitka --onefile --linux-icon=./icons/Geometry_Splash_Logo.png ./geo.py -o geo"
elif plat == "Darwin":
    COMMAND = "nuitka --standalone --macos-create-app-bundle ./geo.py --macos-app-icon=./icons/Geometry_Splash_Logo.png"

PYTHON_CMD = "python3.11"

def get_all_in_folder(folder):
    f = []
    for root, _, files in os.walk(folder):
        for filename in files:
            path = os.path.join(root, filename)
            f.append(path)
    return f

def get_main_executable():
    if plat == "Windows":
        return APP_NAME + ".exe"
    elif plat == "Linux":
        return APP_NAME
    elif plat == "Darwin":
        return APP_NAME + ".app"

def get_relevant_files():
    files = [get_main_executable(), "./custom_levels/"]
    files += get_all_in_folder("./textures")
    files += get_all_in_folder("./levels")
    
    return files

if AS_MODULE:
    output = subprocess.run(PYTHON_CMD + " -m " + COMMAND, shell=True)
else:
    output = subprocess.run(COMMAND, shell=True)

if output.stderr is not None and "FATAL" in output.stderr.decode('utf-8'): # FIXME
    raise RuntimeError("Zipping prevented... see nuitka errors")


print("Zipping the following files:")
desired_files = get_relevant_files()

for file in desired_files:
    print("=>", file)

with ZipFile('geosplash.zip', 'w') as zip:
    for file in desired_files:
        zip.write(file)

print("Zipped all files!")