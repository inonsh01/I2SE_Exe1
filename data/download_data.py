"""Download the real NRRD volumes of the data set into this folder.

The files are 3D Slicer sample data, hosted on GitHub and identified by
their SHA256 checksum, so every download is verified.

Usage:
    python data/download_data.py            # all files (~115 MB)
    python data/download_data.py MRHead     # only the files you name
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/"

# name: (sha256, description)
DATASET = {
    "MRHead": ("cc211f0dfd9a05ca3841ce1141b292898b2dd2d3f08286affadf823a7e58df93",
               "MRI head, 256x256x130, int16, 6.6 MB"),
    "MRBrainTumor1": ("998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
                      "MRI brain with tumor, 256x256x112, int16, 4.9 MB"),
    "CTChest": ("4507b664690840abb6cb9af2d919377ffc4ef75b167cb6fd0f747befdb12e38e",
                "CT chest, 512x512x139, int32, 41 MB"),
    "CTACardio": ("3b0d4eb1a7d8ebb0c5a89cc0504640f76a030b4e869e33ff34c564c3d3b88ad2",
                  "CT angiography of the heart, 512x512x321, int16, 62 MB"),
}

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(name: str) -> None:
    checksum, description = DATASET[name]
    dest = HERE / f"{name}.nrrd"
    if dest.exists() and sha256(dest) == checksum:
        print(f"{name}: already downloaded")
        return
    print(f"{name}: downloading ({description}) ...")
    urllib.request.urlretrieve(BASE_URL + checksum, dest)
    if sha256(dest) != checksum:
        dest.unlink()
        raise SystemExit(f"{name}: checksum mismatch, file deleted")
    print(f"{name}: ok")


def main() -> None:
    names = sys.argv[1:] or list(DATASET)
    unknown = [n for n in names if n not in DATASET]
    if unknown:
        raise SystemExit(f"unknown name(s): {unknown}. Choose from: {list(DATASET)}")
    for name in names:
        download(name)


if __name__ == "__main__":
    main()
