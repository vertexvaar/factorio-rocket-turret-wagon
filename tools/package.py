"""Builds dist/<name>_<version>.zip for the mod portal.

Usage: python tools/package.py
"""
import json
import os
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FILES = ["info.json", "data.lua", "control.lua", "config.lua", "changelog.txt", "thumbnail.png", "README.md", "LICENSE"]
DIRS = ["prototypes", "graphics", "locale"]


def main():
    info = json.load(open(os.path.join(ROOT, "info.json")))
    folder = f"{info['name']}_{info['version']}"
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist", folder + ".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in FILES:
            if os.path.exists(os.path.join(ROOT, f)):
                z.write(os.path.join(ROOT, f), f"{folder}/{f}")
        for d in DIRS:
            for base, _, names in os.walk(os.path.join(ROOT, d)):
                for n in names:
                    path = os.path.join(base, n)
                    z.write(path, f"{folder}/{os.path.relpath(path, ROOT).replace(os.sep, '/')}")
    print(out, os.path.getsize(out))


if __name__ == "__main__":
    main()
