import subprocess
import os
import platform
import sys
import shutil

from zipfile import ZipFile

"""
For linux, you need python headers insatlled (ex: dnf install python3.11-devel), or else
Nuitka will complain about a missing python header.

For MacOS, make sure you have imageio installed (pip install imageio)
"""

APP_NAME = "geo"
DESTINATION = "./geo.dist/"
AS_MODULE = False
PYTHON_CMD = "python3.11"
ZIP_ONLY = False

if len(sys.argv) > 1:
    args = sys.argv[1:]
    if args[0] == "module":
        AS_MODULE = True
    elif args[0] == "zip":
        ZIP_ONLY = True
    elif args[0] == "clean":
        print("Removing destination & build directories ...")
        shutil.rmtree(DESTINATION)
        shutil.rmtree("./geo.build/")
        print("Done!")
        exit()

plat = platform.system()
if plat == "Windows":
    COMMAND = "nuitka ./geo.py --standalone --windows-icon-from-ico=./icons/Geometry_Splash_Logo.ico"
elif plat == "Linux":
    COMMAND = "nuitka ./geo.py --standalone --linux-icon=./icons/Geometry_Splash_Logo.png -o geo"
elif plat == "Darwin":
    COMMAND = "nuitka --standalone --macos-create-app-bundle ./geo.py --macos-app-icon=./icons/Geometry_Splash_Logo.png"


def get_all_in_folder(folder):
    f = []
    for root, _, files in os.walk(folder):
        for filename in files:
            path = os.path.join(root, filename)
            f.append(path)
    return f

def get_main_executable():
    if plat == "Windows":
        return "./geo/" + APP_NAME + ".exe"
    elif plat == "Linux":
        return "./geo/" + APP_NAME
    elif plat == "Darwin":
        return APP_NAME + ".app"

def copy_resources(src, dst):
    print("RESOURCE: Copying files ...")
    shutil.copytree(src + "/custom_levels/", dst + "/custom_levels/", dirs_exist_ok=True)
    shutil.copytree(src + "/levels/", dst + "/levels/", dirs_exist_ok=True)
    shutil.copytree(src + "/textures/", dst + "/textures/", dirs_exist_ok=True)
    print("RESOURCE: All files copied.")
        

def get_relevant_files(): # When this function is called, the current working directory should be set to DESTINATION
    print(f"Working dir: {os.getcwd()}")
    files = []
    if plat == "Windows" or plat == "Linux":
        copy_resources("..", ".")
        files += get_all_in_folder("./")
    else:
        # TODO since I am creating an app bundle, I shouldn't copy the resources all into it.
        raise NotImplementedError("MACOS TODO")
    
    return files

if not ZIP_ONLY:
    if AS_MODULE:
        output = subprocess.run(PYTHON_CMD + " -m " + COMMAND, shell=True)
    else:
        output = subprocess.run(COMMAND, shell=True)


print("Zipping the following files:")
os.chdir(DESTINATION)
desired_files = get_relevant_files()

for file in desired_files:
    print("=>", file)

with ZipFile('../geosplash.zip', 'w') as zip:
    for file in desired_files:
        zip.write(file)

print("Zipped all files!")