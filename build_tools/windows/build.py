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

print(f"\nBuild complete! Executable should be in: {DIST_DIR}")
