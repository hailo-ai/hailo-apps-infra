import subprocess
import logging
import pathlib

logger = logging.getLogger("cpp-compiler")

def compile_postprocess(mode="release"):
    script_path = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "compile_postprocess.sh"
    cmd = [str(script_path)]
    if mode in ("debug", "clean"):
        cmd.append(mode)

    logger.info(f"Running C++ build: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
