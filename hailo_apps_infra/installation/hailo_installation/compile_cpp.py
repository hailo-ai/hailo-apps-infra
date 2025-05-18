#!/usr/bin/env python3
import subprocess
import logging
import pathlib
import argparse
from hailo_apps_infra.common.hailo_common.defines import REPO_ROOT

logger = logging.getLogger("cpp-compiler")

def compile_postprocess(repo_root: pathlib.Path, mode: str = "release"):
    """
    Run the C++ post-process compilation script.

    Parameters:
    - repo_root: Path to the repository root directory.
    - mode: Build mode ("release", "debug", or "clean").
    """
    repo_root = pathlib.Path(repo_root)
    script_path = repo_root / "scripts" / "compile_postprocess.sh"
    # Pass repo_root via -p flag to the shell script
    cmd = [str(script_path), "-p", str(repo_root)]
    if mode in ("debug", "clean", "release"):
        # clean and debug require special behavior; release can be passed or omitted
        cmd.append(mode)

    logger.info(f"Running C++ build: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser(
        description="Compile C++ postprocess code via external script"
    )
    parser.add_argument(
        "--repo-root", "-r",
        type=pathlib.Path,
        default=REPO_ROOT,
        help="Path to the repository root (defaults to compiled-in REPO_ROOT)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["release", "debug", "clean"],
        default="release",
        help="Build mode: release (default), debug, or clean"
    )
    args = parser.parse_args()

    compile_postprocess(args.repo_root, args.mode)


if __name__ == "__main__":
    main()
