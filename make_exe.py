import os
import subprocess
import sys
import platform

def is_venv():
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def main():
    print("🚀 Starting build process...")

    # 1. Check/Install PyInstaller
    try:
        import PyInstaller
    except ImportError:
        if not is_venv():
            print("🛑 Error: PyInstaller not found and not running inside a virtual environment.")
            print("   To avoid 'externally-managed-environment' errors, please either:")
            print("   1. Create and activate a virtual environment:")
            print("      python3 -m venv .venv")
            print("      source .venv/bin/activate")
            print("   2. Or install PyInstaller via your system package manager.")
            sys.exit(1)
            
        print("📦 PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # 2. Define assets to bundle
    assets = [
        "style.css",
        "code_highlight.css"
    ]
    
    # 3. Determine separator for --add-data (Windows uses ';', Linux/Unix uses ':')
    separator = ";" if platform.system() == "Windows" else ":"
    
    add_data_args = []
    for asset in assets:
        if os.path.exists(asset):
            # Format: source_file{separator}destination_folder
            add_data_args.append(f"--add-data={asset}{separator}.")
        else:
            print(f"⚠️  Warning: Asset '{asset}' not found. It won't be bundled.")

    # 4. Run PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=blogcraft",
        "--clean",
    ] + add_data_args + ["blogcraft.py"]
    
    print(f"🔨 Running PyInstaller: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    print("\n✅ Build complete!")
    print(f"   Executable location: {os.path.join('dist', 'blogcraft' + ('.exe' if platform.system() == 'Windows' else ''))}")

if __name__ == "__main__":
    main()