"""
Helper functions to run subprocesses safely.
"""
import subprocess


def run_command(cmd: list[str], error_msg: str) -> None:
    """Run a shell command, exit on non-zero."""
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"{error_msg} (exit {result.returncode})")
        exit(result.returncode)


def run_command_with_output(cmd: list[str]) -> str:
    """Run a shell command and return stdout."""
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result.stdout


def create_symlink(src: str, dst: str) -> None:
    """Create or replace a symlink."""
    import os
    if os.path.islink(dst) or os.path.exists(dst):
        os.remove(dst)
    os.symlink(src, dst)