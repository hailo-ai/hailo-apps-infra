#!/usr/bin/env python3
"""
install.py - Python equivalent of install.sh
"""

import os
import sys
import subprocess
import platform
import pwd
import grp
import getpass


def load_defaults():
    venv_name = os.environ.get("VENV_NAME", "hailo_infra_venv")
    return {
        "VENV_NAME": venv_name,
        "PIP_CMD": "pip3",
        "PYTHON_CMD": "python3",
        "PY_INSTALLER": os.path.join(
            "hailo_apps_infra", "installation", "hailo_installation", "python_installation.py"
        ),
        "RESOURCE_BASE": "/usr/local/hailo/resources",
    }


def detect_architecture():
    arch = platform.machine()
    if arch.startswith(("arm", "aarch64")):
        sys_pkg = "hailo-all"
        tappas_pkg = "hailo-tappas-core-python-binding"
        print(f"🔍 Detected ARM architecture ({arch}): will check for 'hailo-all' and RPi Python binding")
    else:
        sys_pkg = "hailort-pcie-driver"
        tappas_pkg = "hailo-tappas-core"
        print(f"🔍 Detected x86 architecture ({arch}): will check for 'hailort-pcie-driver' and x86 Python binding")
    return arch, sys_pkg, tappas_pkg


def parse_args():
    install_gstreamer = True
    install_pipelines = True
    args = sys.argv[1:]
    for arg in args:
        if arg == "--gstreamer-only":
            install_gstreamer = True
        elif arg == "--pipelines-only":
            install_gstreamer = True
            install_pipelines = True
        elif arg == "--all":
            install_gstreamer = True
            install_pipelines = True
        else:
            print(f"⚠️  Ignoring unknown flag: {arg}")
    return install_gstreamer, install_pipelines


def detect_system_pkg_version(pkg):
    res = subprocess.run(
        ["dpkg-query", "-W", "-f=${Version}", pkg],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    return res.stdout.strip() if res.returncode == 0 else ""


def detect_pip_pkg_version(pip_cmd, pkg):
    res = subprocess.run(
        [pip_cmd, "show", pkg],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True
    )
    if res.returncode == 0:
        for line in res.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    return ""


def check_system_pkg(pkg):
    ver = detect_system_pkg_version(pkg)
    if not ver:
        print(f"❌ System package '{pkg}' not found. Please install it before proceeding.", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"✅ {pkg} (system) version: {ver}")


def setup_resource_dirs(base, subs):
    sudo = ["sudo"]
    for sub in subs:
        path = os.path.join(base, sub)
        subprocess.run(sudo + ["mkdir", "-p", path], check=True)
    install_user = os.environ.get("SUDO_USER") or getpass.getuser()
    pw = pwd.getpwnam(install_user)
    install_group = grp.getgrgid(pw.pw_gid).gr_name
    subprocess.run(sudo + ["chown", "-R", f"{install_user}:{install_group}", base], check=True)
    subprocess.run(sudo + ["chmod", "-R", "755", base], check=True)
    print(f"🔧 Created and set permissions on {base} subdirs")


def check_tappas_core():
    ht1 = detect_system_pkg_version("hailo-tappas")
    ht2 = detect_system_pkg_version("hailo-tappas-core")
    if ht1:
        print(f"✅ hailo-tappas version: {ht1}")
        return ht1
    elif ht2:
        print(f"✅ hailo-tappas-core version: {ht2}")
        return ht2
    else:
        print("❌ Neither hailo-tappas nor hailo-tappas-core is installed.", file=sys.stderr)
        sys.exit(1)


def create_and_prepare_venv(python_cmd, venv_name, use_system):
    if os.path.isdir(venv_name):
        print(f"✅ Virtualenv '{venv_name}' exists. Activating…")
    else:
        print(f"🔧 Creating virtualenv '{venv_name}'…")
        cmd = [python_cmd, "-m", "venv"]
        if use_system:
            cmd += ["--system-site-packages"]
        cmd += [venv_name]
        subprocess.run(cmd, check=True)
        print("✅ Created.")
    venv_py = os.path.join(venv_name, "bin", "python3")
    return venv_py


def install_bindings(venv_py, installer, install_pyhailort, install_tappas_core, hrt_ver, htc_ver):
    if install_pyhailort or install_tappas_core:
        print("🔧 Installing Hailo Python bindings via installer script…")
        cmd = [venv_py, installer, "--venv-path", os.path.dirname(venv_py)]
        if install_pyhailort:
            cmd += ["--install-pyhailort", "--pyhailort-version", hrt_ver]
        if install_tappas_core:
            cmd += ["--install-tappas-core", "--tappas-version", htc_ver]
        subprocess.run(cmd, check=True)
    else:
        print("✅ All required pip packages present.")


def bootstrap_env_file(env_path):
    if not os.path.exists(env_path):
        print(f"🔧 Creating .env file at {env_path}")
        open(env_path, "w").close()
    else:
        print(f"✅ .env already exists at {env_path}")
    os.chmod(env_path, 0o666)


def install_local_modules(venv_py, install_gstreamer, install_pipelines):
    # Upgrade packaging tools
    subprocess.run([venv_py, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], check=True)
    print("📦 Upgraded pip/setuptools/wheel")
    # Core modules
    subprocess.run([
        venv_py, "-m", "pip", "install", "-e",
        "./hailo_apps_infra/common",
        "-e", "./hailo_apps_infra/config",
        "-e", "./hailo_apps_infra/installation"
    ], check=True)
    # Optional modules
    if install_gstreamer:
        print("📦 Installing gstreamer…")
        subprocess.run([venv_py, "-m", "pip", "install", "-e", "./hailo_apps_infra/gstreamer"], check=True)
    if install_pipelines:
        print("📦 Installing pipelines…")
        subprocess.run([venv_py, "-m", "pip", "install", "-e", "./hailo_apps_infra/pipelines"], check=True)
    print("📦 Installing shared runtime deps…")
    subprocess.run([venv_py, "-m", "pip", "install", "-r", "requirements.txt"], check=True)


def run_post_install(venv_py):
    print("⚙️  Running post-install…")
    subprocess.run([venv_py, "-m", "hailo_installation.post_install"], check=True)


def main():
    cfg = load_defaults()
    python_cmd = cfg["PYTHON_CMD"]
    pip_cmd = cfg["PIP_CMD"]

    # Detect architecture & packages
    print()
    arch, sys_pkg, tappas_pkg = detect_architecture()

    # Parse flags
    install_gstreamer, install_pipelines = parse_args()

    # Resource directories
    print()
    setup_resource_dirs(cfg["RESOURCE_BASE"], ["models/hailo8", "models/hailo8l", "videos", "so"])

    # System package checks
    print()
    print("📋 Checking required system packages…")
    check_system_pkg(sys_pkg)
    check_system_pkg("hailort")

    # HailoRT / Tappas core system version
    print()
    print("📋 Checking for HailoRT system version")
    hrt_ver = detect_system_pkg_version("hailort")
    print("📋 Checking for hailo-tappas vs hailo-tappas-core…")
    htc_ver = check_tappas_core()

    # Host-Python pip checks
    print()
    print("📋 Checking host-Python pip packages…")
    install_pyhailort = False
    install_tappas_core = False
    host_py = detect_pip_pkg_version(pip_cmd, "hailort")
    if not host_py:
        print("⚠️  pip 'hailort' missing; will install in venv.")
        install_pyhailort = True
    else:
        print(f"✅ pip 'hailort' version: {host_py}")
    host_tc = detect_pip_pkg_version(pip_cmd, tappas_pkg)
    if not host_tc:
        print(f"⚠️  pip '{tappas_pkg}' missing; will install in venv.")
        install_tappas_core = True
    else:
        print(f"✅ pip '{tappas_pkg}' version: {host_tc}")

    # Virtualenv setup
    print()
    use_system = not (install_pyhailort and install_tappas_core)
    venv_py = create_and_prepare_venv(python_cmd, cfg["VENV_NAME"], use_system)

    # Re-check inside venv
    if subprocess.run([venv_py, "-m", "pip", "show", "hailort"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        install_pyhailort = True
    if subprocess.run([venv_py, "-m", "pip", "show", tappas_pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
        install_tappas_core = True

    # Install missing pip bindings
    print()
    install_bindings(venv_py, cfg["PY_INSTALLER"], install_pyhailort, install_tappas_core, hrt_ver, htc_ver)

    # .env file
    bootstrap_env_file(os.path.join(os.getcwd(), ".env"))

    # Local modules & deps
    print()
    install_local_modules(venv_py, install_gstreamer, install_pipelines)

    # Post-install hook
    print()
    run_post_install(venv_py)

    # Finish
    print(f"\n🎉  All done!\n\nTo reactivate your environment later:\n    source {cfg['VENV_NAME']}/bin/activate\n")


if __name__ == "__main__":
    main()
