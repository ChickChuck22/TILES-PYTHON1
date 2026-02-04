# 🛠️ Build Tools

This folder contains scripts and configurations to build **Titanium Piano** for Windows.

## 🪟 Windows (.exe)

We use **PyInstaller** to create a standalone executable.

### Prerequisites
```bash
pip install pyinstaller
```

### How to Build
Run the build script from the project root or any folder:

```bash
python build_tools/windows/build.py
```

The executable will be generated in the `dist` folder at the project root.
