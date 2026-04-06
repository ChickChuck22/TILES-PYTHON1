import PyInstaller.__main__
import os
import shutil

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIST_DIR = os.path.join(BASE_DIR, "dist")
WORK_DIR = os.path.join(BASE_DIR, "build")

print(f"Project Base Directory: {BASE_DIR}")

# Clean previous builds
if os.path.exists(DIST_DIR):
    shutil.rmtree(DIST_DIR)
if os.path.exists(WORK_DIR):
    shutil.rmtree(WORK_DIR)

# PyInstaller arguments
args = [
    os.path.join(BASE_DIR, "main.py"),  # Script to build
    '--name=TitaniumPiano',
    '--noconfirm',
    '--windowed',  # No console window
    '--onefile',   # Single executable file
    f'--icon={os.path.join(BASE_DIR, "assets", "icon.png")}',
    
    # Add data folders (source:destination)
    f'--add-data={os.path.join(BASE_DIR, "assets")}{os.pathsep}assets',
    f'--add-data={os.path.join(BASE_DIR, "src")}{os.pathsep}src',
    
    # Imports hidden (sometimes needed for dynamic imports)
    '--hidden-import=pygame',
    '--hidden-import=PyQt5',
    '--hidden-import=librosa',
    '--hidden-import=numpy',
]

print("Starting Build Process...")
print(f"Arguments: {args}")

PyInstaller.__main__.run(args)

print(f"\nBuild complete! Executable is in: {DIST_DIR}")

# Optional: Try to run Inno Setup Compiler if available
import subprocess
iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if os.path.exists(iscc_path):
    print("\nFound Inno Setup! Generating installer...")
    iss_script = os.path.join(BASE_DIR, "build_tools", "windows", "installer_script.iss")
    try:
        subprocess.run([iscc_path, iss_script], check=True)
        print("Installer generated successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Failed to generate installer: {e}")
else:
    print("\nInno Setup (ISCC.exe) not found at default path. Please generate the installer manually using 'installer_script.iss'.")
