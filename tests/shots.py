"""Takes in-game screenshots of a showcase scene (opens a Factorio window briefly).

Usage: python tests/shots.py [out_dir]   (default: previews/shots)
"""
import os
import shutil
import sys

import run

HARNESS = "turret-wagon-shots"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(run.ROOT, "previews", "shots")


def main():
    run.HARNESS = HARNESS
    run.prepare(True)
    save = os.path.join(run.ENV, "shots.zip")
    created = run.run(run.DEFAULT_EXE, "--create", save)
    if not os.path.exists(save):
        print(created.stdout[-3000:])
        sys.exit("map creation failed")
    result = run.run(run.DEFAULT_EXE, "--benchmark-graphics", save, "--benchmark-ticks", "400")
    shots = os.path.join(run.ENV, "write", "script-output", "wagon-shots")
    if not os.path.isdir(shots):
        print(result.stdout[-3000:])
        sys.exit("no screenshots taken")
    os.makedirs(OUT, exist_ok=True)
    for name in sorted(os.listdir(shots)):
        shutil.copy(os.path.join(shots, name), OUT)
        print(os.path.join(OUT, name))


if __name__ == "__main__":
    main()
