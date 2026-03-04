import os
import sys
import zipfile
import urllib.request
import shutil
from pathlib import Path

# Configuration
BIN_DIR = Path(__file__).resolve().parent.parent / "bin"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
SOX_URL = "https://sourceforge.net/projects/sox/files/sox/14.4.2/sox-14.4.2-win32.zip/download"

def download_file(url, dest):
    print(f"Downloading {url}...")
    with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    print(f"Downloaded to {dest}")

def extract_zip(zip_path, extract_to):
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted to {extract_to}")

def setup_binaries():
    if not BIN_DIR.exists():
        BIN_DIR.mkdir(parents=True)
        print(f"Created directory: {BIN_DIR}")

    # 1. Setup FFmpeg
    ffmpeg_zip = BIN_DIR / "ffmpeg.zip"
    if not (BIN_DIR / "ffmpeg.exe").exists():
        download_file(FFMPEG_URL, ffmpeg_zip)
        extract_zip(ffmpeg_zip, BIN_DIR)
        
        # Move ffmpeg.exe, ffprobe.exe to bin root
        # Gyan.dev zip structure: ffmpeg-7.1-essentials_build/bin/ffmpeg.exe
        for p in BIN_DIR.glob("**/ffmpeg.exe"):
            shutil.move(str(p), str(BIN_DIR / "ffmpeg.exe"))
        for p in BIN_DIR.glob("**/ffprobe.exe"):
            shutil.move(str(p), str(BIN_DIR / "ffprobe.exe"))
        
        # Cleanup
        os.remove(ffmpeg_zip)
        # Remove the extracted (now mostly empty) folders
        for p in BIN_DIR.iterdir():
            if p.is_dir() and "ffmpeg" in p.name:
                shutil.rmtree(p)
    else:
        print("ffmpeg.exe already exists in bin/")

    # 2. Setup SoX
    sox_zip = BIN_DIR / "sox.zip"
    if not (BIN_DIR / "sox.exe").exists():
        download_file(SOX_URL, sox_zip)
        extract_zip(sox_zip, BIN_DIR)
        
        # SoX zip structure: sox-14.4.2/sox.exe
        for p in BIN_DIR.glob("**/sox.exe"):
            # Move all files from the sox folder to bin root (dlls are needed)
            sox_folder = p.parent
            for file in sox_folder.iterdir():
                dest = BIN_DIR / file.name
                if dest.exists():
                    if dest.is_dir(): shutil.rmtree(dest)
                    else: os.remove(dest)
                shutil.move(str(file), str(BIN_DIR))
            break # only one sox folder
        
        # Cleanup
        os.remove(sox_zip)
        for p in BIN_DIR.iterdir():
            if p.is_dir() and "sox" in p.name:
                shutil.rmtree(p)
    else:
        print("sox.exe already exists in bin/")

    print("\n" + "="*40)
    print("SUCCESS: Binaries are ready in " + str(BIN_DIR))
    print("="*40)

if __name__ == "__main__":
    try:
        setup_binaries()
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
