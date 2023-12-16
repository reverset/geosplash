import subprocess
import os

from zipfile import ZipFile

def get_all_in_folder(folder):
    f = []
    for root, _, files in os.walk(folder):
        for filename in files:
            path = os.path.join(root, filename)
            f.append(path)
    return f

def get_relevant_files():
    files = ["geo.exe"]
    files += get_all_in_folder("textures")
    files += get_all_in_folder("levels")
    
    return files

output = subprocess.run("nuitka --onefile --windows-icon-from-ico=icons/Geometry_Splash_Logo.ico ./geo.py", shell=True)

print("Zipping the following files:")
desired_files = get_relevant_files()

for file in desired_files:
    print("=>", file)

with ZipFile('geosplash.zip', 'w') as zip:
    for file in desired_files:
        zip.write(file)

print("Zipped all files!")