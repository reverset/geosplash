import subprocess
import os
import platform
import sys

from zipfile import ZipFile

"""
For linux, you need python headers insatlled (ex: dnf install python3.11-devel), or else
Nuitka will complain about a missing python header.

For MacOS, make sure you have imageio installed (pip install imageio)
"""

APP_NAME = "geo"
AS_MODULE = False
PYTHON_CMD = "python3.11"

if len(sys.argv) > 1:
    args = sys.argv[1:]
    if args[0] == "module":
        AS_MODULE = True

plat = platform.system()
if plat == "Windows":
    COMMAND = "pyinstaller --onefile ./geo.py --icon=./icons/Geometry_Splash_Logo.ico --distpath=."
elif plat == "Linux":
    COMMAND = "pyinstaller --onefile ./geo.py --icon=./icons/Geometry_Splash_Logo.png --distpath=."
elif plat == "Darwin":
    COMMAND = "pyinstaller --onefile ./geo.py --icon=./icons/Geometry_Splash_Logo.png --distpath=."


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
    files = [get_main_executable()]
    files += get_all_in_folder("./textures")
    files += get_all_in_folder("./levels")
    files += get_all_in_folder("./custom_levels/")
    
    return files

if AS_MODULE: # remove me
    output = subprocess.run(PYTHON_CMD + " -m " + COMMAND, shell=True)
else:
    output = subprocess.run(COMMAND, shell=True)


print("Zipping the following files:")
desired_files = get_relevant_files()

for file in desired_files:
    print("=>", file)

with ZipFile('geosplash.zip', 'w') as zip:
    for file in desired_files:
        zip.write(file)

print("Zipped all files!")