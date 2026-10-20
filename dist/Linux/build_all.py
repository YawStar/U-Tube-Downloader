#!/usr/bin/env python3
import subprocess
import sys

# List of build scripts in the exact order requested
BUILD_SCRIPTS = [
    "build_appimage.py",
    "build_deb.py",
    "build_rpm.py",
    "build_tar_gz.py"
]

def main():
    print("=" * 50)
    print("Starting Complete Build Process")
    print("=" * 50 + "\n")

    for index, script in enumerate(BUILD_SCRIPTS, start=1):
        print(f"[{index}/4] Running {script}...")
        
        try:
            # Run the script using the current python interpreter (sys.executable)
            # check=True will raise a CalledProcessError if the script exits with a non-zero code
            subprocess.run([sys.executable, script], check=True)
            print(f"✔ Successfully finished: {script}\n")
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ [ERROR] Build failed while running: {script}")
            print(f"Process exited with error code: {e.returncode}")
            sys.exit(e.returncode)
            
        except FileNotFoundError:
            print(f"\n❌ [ERROR] Could not find the script file: {script}")
            print("Please ensure it is in the same directory as build_all.py.")
            sys.exit(1)

    print("=" * 50)
    print("🎉 All builds completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    main()
