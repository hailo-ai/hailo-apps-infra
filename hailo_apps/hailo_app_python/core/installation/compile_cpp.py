import sys, subprocess, logging
from pathlib import Path

logger = logging.getLogger(__name__)

def compile_postprocess():
    # 1) locate hailo_apps_infra package
    here     = Path(__file__).resolve()    
    pkg_root = here.parents[3]             

    # 2) point at the correct folder structure: hailo_app_python/core/cpp_postprocess
    pp_dir   = pkg_root / "hailo_app_python" / "core" / "cpp_postprocess"
    if not (pp_dir / "meson.build").exists():
        logger.error(f"meson.build not found in {pp_dir}")
        sys.exit(1)

    # 3) call the script from there
    script = pp_dir / "compile_postprocess.sh"
    ret = subprocess.run(
        ["bash", str(script), "release"],
        cwd=str(pp_dir),
        check=False
    )
    if ret.returncode:
        logger.error(f"C++ postprocess build failed (exit {ret.returncode})")
        sys.exit(ret.returncode)