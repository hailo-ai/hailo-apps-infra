#!/usr/bin/env python3
import os
import sys
import argparse
import urllib.request
import platform
from pathlib import Path


# ─── config loading & env helpers ─────────────────────────────────────────────
from hailo_apps_infra.common.hailo_common.config_utils import (
    load_config,
    validate_config,
)
from hailo_apps_infra.common.hailo_common.core import (
    load_environment,
)

# ─── other imports ────────────────────────────────────────────────────────────
from hailo_apps_infra.common.hailo_common.defines import (
    HOST_ARCH_KEY,
    PACKAGE_ROOT,
    DEFAULT_CONFIG_PATH,
    RESOURCES_GROUP_ALL,
    HOST_ARCH_DEFAULT,
    HAILORT_VERSION_KEY,
    AUTO_DETECT,
    TAPPAS_POSTPROC_PATH_KEY,
    HAILORT_PACKAGE,
    HAILO_TAPPAS,
    HAILO_TAPPAS_CORE,
    TAPPAS_VERSION_KEY,
    TAPPAS_VARIANT_KEY,
    REPO_ROOT,
    TAPPAS_VERSION_DEFAULT,
    TAPPAS_VARIANT_DEFAULT,
    MODEL_ZOO_VERSION_KEY,
    MODEL_ZOO_VERSION_DEFAULT,
    VIRTUAL_ENV_NAME_KEY,
    VIRTUAL_ENV_NAME_DEFAULT,
    SERVER_URL_KEY,
    SERVER_URL_DEFAULT,
    RESOURCES_PATH_KEY,
    RESOURCES_PATH_DEFAULT,
    STORAGE_PATH_KEY,
    STORAGE_PATH_DEFAULT,
    RESOURCES_ROOT_PATH_DEFAULT,
    DEFAULT_RESOURCES_CONFIG_PATH,
    DEFAULT_DOTENV_PATH,
    PIP_CMD,
    HAILO_MODULE_NAMES,
    PYTHON_CMD,
    RESOURCES_GROUP_DEFAULT,
    HAILO_ARCH_KEY,
    HAILO_ARCH_DEFAULT,
    HAILO_TAPPAS_CORE_PYTHON,
)
from hailo_apps_infra.common.hailo_common.installation_utils import (
    detect_system_pkg_version,
    detect_hailo_arch,
    detect_host_arch,
    detect_pkg_installed,
    run_command_with_output,
    run_command,
    create_symlink,
)
from hailo_apps_infra.installation.hailo_installation.create_dirs import (
    setup_resource_dirs,
)
from hailo_apps_infra.installation.hailo_installation.download_resources import (
    download_resources,
)
from hailo_apps_infra.installation.hailo_installation.compile_cpp import (
    compile_postprocess,
)


ENV_PATH = Path(DEFAULT_DOTENV_PATH)


def load_and_validate_config(config_path: str) -> dict:
    """
    Load and validate the configuration file.
    Returns the loaded configuration as a dictionary.
    """
    cfg_path = Path(config_path or DEFAULT_CONFIG_PATH)
    config = load_config(cfg_path)
    if not validate_config(config):
        print("❌ Invalid configuration. Please check the config file.")
        sys.exit(1)
    return config


def handle_hailort_version(hailort_version: str) -> str:
    """
    Handle the hailort version based on the provided value.
    If AUTO_DETECT is specified, detect the version automatically.
    """
    if hailort_version == AUTO_DETECT or hailort_version is None:
        print("🔍 Auto-detecting HailoRT version...")
        hailort_version = detect_system_pkg_version(HAILORT_PACKAGE)
        if hailort_version is None:
            print("❌ HailoRT version not found. Please specify a valid version.")
            sys.exit(1)
    return hailort_version


def handle_hailo_arch(hailo_arch: str) -> str:
    """
    Handle the Hailo architecture based on the provided value.
    If AUTO_DETECT is specified, detect the architecture automatically.
    """
    if hailo_arch == AUTO_DETECT or hailo_arch is None:
        print("🔍 Auto-detecting Hailo architecture...")
        hailo_arch = detect_hailo_arch()
        if hailo_arch is None:
            print("❌ Hailo architecture not found. Please specify a valid architecture.")
            sys.exit(1)
    return hailo_arch


def handle_host_arch(host_arch: str) -> str:
    """
    Handle the host architecture based on the provided value.
    If AUTO_DETECT is specified, detect the architecture automatically.
    """
    if host_arch == AUTO_DETECT or host_arch is None:
        print("🔍 Auto-detecting host architecture...")
        host_arch = detect_host_arch()
        if host_arch is None:
            print("❌ Host architecture not found. Please specify a valid architecture.")
            sys.exit(1)
    return host_arch


def handle_tappas(tappas_version: str, tappas_variant: str) -> tuple:
    """
    Handle the TAPPAS version and variant based on the provided values.
    """
    if tappas_variant == AUTO_DETECT:
        print("⚠️ tappas_variant is set to 'auto'. Detecting TAPPAS variant...")
        if detect_pkg_installed(HAILO_TAPPAS):
            tappas_variant = HAILO_TAPPAS
            print("✅ Detected TAPPAS variant.")
        elif detect_pkg_installed(HAILO_TAPPAS_CORE):
            tappas_variant = HAILO_TAPPAS_CORE
            print("✅ Detected TAPPAS-CORE variant.")
        else:
            print("⚠ Could not detect TAPPAS variant, please install TAPPAS or TAPPAS-CORE.")
            sys.exit(1)

    if tappas_version == AUTO_DETECT:
        print("⚠️ tappas_version is set to 'auto'. Detecting TAPPAS version...")
        tappas_version = detect_system_pkg_version(
            HAILO_TAPPAS if tappas_variant == HAILO_TAPPAS else HAILO_TAPPAS_CORE
        )
        if tappas_version is None:
            print("⚠ Could not detect TAPPAS version.")
            sys.exit(1)
        print(f"✅ Detected TAPPAS version: {tappas_version}")

    if tappas_variant == HAILO_TAPPAS:
        # use a list so subprocess.run() finds the executable
        workspace = run_command_with_output(
            ["pkg-config", "--variable=tappas_workspace", HAILO_TAPPAS]
        )
        tappas_postproc_dir = f"{workspace}/apps/h8/gstreamer/libs/post_processes/"

    elif tappas_variant == HAILO_TAPPAS_CORE:
        tappas_postproc_dir = run_command_with_output(
            ["pkg-config", "--variable=tappas_postproc_lib_dir", HAILO_TAPPAS_CORE]
        )

    else:
        print("⚠ Could not detect TAPPAS variant.")
        sys.exit(1)
    return tappas_version, tappas_variant, tappas_postproc_dir


def handle_virtualenv(
    venv_name: str,
    python_cmd: str,
    tappas_variant: str
) -> tuple[bool, bool, str, str]:
    """
    Ensure a virtualenv exists (create if needed) using run_command,
    then re-check inside it whether 'hailort' and tappas_pip_pkg need installing
    via run_command_with_output.
    Returns updated flags: (install_pyhailort, install_tappas_core , venv_pip , venv_python ).
    """
    venv_path = Path(venv_name)

    install_tappas_core = True
    install_pyhailort = True
    if tappas_variant == HAILO_TAPPAS_CORE:
        tappas_variant = HAILO_TAPPAS_CORE_PYTHON

    try:
        run_command_with_output([PIP_CMD, "show", HAILORT_PACKAGE])
        install_pyhailort = False
    except Exception:
        print(1)
        install_pyhailort = True

    try:
        run_command_with_output([PIP_CMD, "show", tappas_variant])
        install_tappas_core = False
    except Exception:
        install_tappas_core = True

    # 1) Create or skip creation
    if venv_path.is_dir():
        print(f"✅ Virtualenv '{venv_name}' exists. Activating…")
    else:
        print(f"🔧 Creating virtualenv '{venv_name}'…")
        # build the venv command string
        cmd = f"{python_cmd} -m venv"
        if not (install_pyhailort and install_tappas_core):
            cmd += " --system-site-packages"
            print("Using system site packages")
        cmd += f" {venv_name}"
        run_command(cmd, f"Failed to create virtualenv '{venv_name}'")
        print("✅ Created. Activating…")

    # 2) Print activation instruction
    print(f"To activate, run:\n    source {venv_path/'bin'/'activate'}")

    # 3) Re-check inside venv with its pip
    venv_python = os.path.join(venv_path , "bin" , "python3")
    venv_pip = os.path.join(venv_path , "bin" , "pip3")

        # if we’re not already that interpreter, re‐exec
    if os.path.abspath(sys.executable) != os.path.abspath(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)

    try:
        run_command_with_output([venv_pip, "show", HAILORT_PACKAGE])
        install_pyhailort = False
        print(f"✅ HailoRT {HAILORT_PACKAGE} already installed.")
    except Exception:
        install_pyhailort = True

    try:
        run_command_with_output([venv_pip, "show", tappas_variant])
        install_tappas_core = False
        print(f"✅ TAPPAS {tappas_variant} already installed.")
    except Exception:
        install_tappas_core = True

    return install_pyhailort, install_tappas_core , venv_pip , venv_python


def handle_dot_env() -> None:
    if not ENV_PATH.is_file():
        print(f"🔧 Creating .env file at {ENV_PATH}")
        ENV_PATH.touch()
        os.chmod(ENV_PATH, 0o666)
    else:
        print(f"✅ .env already exists at {ENV_PATH}")
        os.chmod(ENV_PATH, 0o666)


def handle_set_and_persist_env(
    host_arch, hailo_arch, resources_path, tappas_postproc_dir,
    model_zoo_version, hailort_version, tappas_version,
    virtual_env_name, server_url, storage_dir, tappas_variant
) -> None:
    env_vars = {
        HOST_ARCH_KEY: host_arch,
        HAILO_ARCH_KEY: hailo_arch,
        RESOURCES_PATH_KEY: resources_path,
        TAPPAS_POSTPROC_PATH_KEY: tappas_postproc_dir,
        MODEL_ZOO_VERSION_KEY: model_zoo_version,
        HAILORT_VERSION_KEY: hailort_version,
        TAPPAS_VERSION_KEY: tappas_version,
        VIRTUAL_ENV_NAME_KEY: virtual_env_name,
        SERVER_URL_KEY: server_url,
        STORAGE_PATH_KEY: storage_dir,
        TAPPAS_VARIANT_KEY: tappas_variant
    }
    os.environ.update({k: v for k, v in env_vars.items() if v is not None})
    _persist_env_vars(env_vars)


def _persist_env_vars(env_vars: dict) -> None:
    if ENV_PATH.exists() and not os.access(ENV_PATH, os.W_OK):
        print("⚠️ .env not writable — fixing permissions...")
        try:
            ENV_PATH.chmod(0o666)
        except Exception as e:
            print(f"❌ Failed to fix .env perms: {e}")
            sys.exit(1)
    with open(ENV_PATH, 'w') as f:
        for key, value in env_vars.items():
            if value is not None:
                f.write(f"{key}={value}\n")
    print(f"✅ Persisted environment variables to {ENV_PATH}")


def install_core_modules(pip_cmd: str = PIP_CMD,hailo_apps_infra_path: str = None) -> None:
    # print("📦 Upgrading pip/setuptools/wheel…")
    # run_command(f"{pip_cmd} install --break-system-packages --upgrade pip setuptools wheel", "Failed to upgrade pip/tools")

    # print("📦 Installing Hailo Apps Infra…")
    if hailo_apps_infra_path is not None:
        run_command(f"{pip_cmd} install -e {hailo_apps_infra_path}", "Failed to install Hailo Apps Infra")
    else:
        run_command(f"{pip_cmd} install -e .", "Failed to upgrade pip")

    # print("📦 Installing requirements.txt…")
    # if req_file is None:
    #     req_file = Path(REPO_ROOT / 'requirements.txt')
    # if req_file.exists():
    #     run_command(f"{pip_cmd} install -r {req_file}", "Failed to install requirements")
    # else:
    #     print(f"No requirements.txt found at {req_file}, skipping.")

    # print("📦 Installing core Hailo modules…")
    # core_dirs = [str(Path(PACKAGE_ROOT) / module) for module in HAILO_MODULE_NAMES]
    # run_command(f"{pip_cmd} install -e {' '.join(core_dirs)}", "Failed to install core modules")


def download_wheel(url: str, dest_dir: Path) -> Path:
    """Download a wheel from a URL into dest_dir, returning the Path to the file."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    wheel_path = dest_dir / Path(url).name
    if not wheel_path.exists():
        print(f"⬇️ Downloading wheel from {url} to {dest_dir}...")
        try:
            urllib.request.urlretrieve(url, str(wheel_path))
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            sys.exit(1)
    else:
        print(f"✅ Wheel already present: {wheel_path}")
    return wheel_path


def install_wheel(wheel_path: Path) -> None:
    """Install a local wheel file via pip."""
    if not wheel_path.exists():
        print(f"❌ Wheel file not found: {wheel_path}")
        sys.exit(1)
    print(f"🔧 Installing wheel: {wheel_path.name}")
    run_command(f"{PIP_CMD} install {wheel_path}", f"Failed to install wheel {wheel_path.name}")
    print(f"✅ Installed wheel: {wheel_path.name}")


def handle_install_hailo_packages(
    hailort_version: str,
    install_pyhailort: bool,
    tappas_version: str,
    install_tappas_core: bool,
    server_url: str,
    storage_dir: str
) -> None:
    """
    Download and install HailoRT and hailo-tappas-core wheels if needed.
    """
    download_dir = Path(storage_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    if install_pyhailort:
        version = hailort_version
        py_tag = f"cp{sys.version_info.major}{sys.version_info.minor}-cp{sys.version_info.major}{sys.version_info.minor}"
        machine = platform.machine()
        if 'x86_64' in machine:
            platform_tag = 'linux_x86_64'
        elif 'aarch64' in machine or 'arm64' in machine:
            platform_tag = 'linux_aarch64'
        else:
            print(f"❌ Unsupported architecture: {machine}")
            sys.exit(1)
        wheel_name = f"{HAILORT_PACKAGE}-{version}-{py_tag}-{platform_tag}.whl"
        url = f"{server_url}/{wheel_name}"
        wheel_path = download_wheel(url, download_dir)
        install_wheel(wheel_path)
    else:
        print(f"✅ HailoRT {hailort_version} already installed.")

    if install_tappas_core:
        version = tappas_version
        wheel_name = f"tappas_core_python_binding-{version}-py3-none-any.whl"
        url = f"{server_url}/{wheel_name}"
        wheel_path = download_wheel(url, download_dir)
        install_wheel(wheel_path)
    else:
        print(f"✅ TAPPAS {tappas_version} already installed.")


def main():
    parser = argparse.ArgumentParser(
        description="Installation script for Hailo Apps Infra."
    )
    parser.add_argument(
        "-c", "--config", type=str, default=None,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})"
    )
    parser.add_argument(
        "-g", "--group", type=str, default=RESOURCES_GROUP_DEFAULT,
        help="Group name for downloading resources"
    )
    parser.add_argument(
        "-r", "--resources-config", type=str, default=DEFAULT_RESOURCES_CONFIG_PATH,
        help=f"Path to resources config file (default: {DEFAULT_RESOURCES_CONFIG_PATH})"
    )
    parser.add_argument(
        "-a", "--all", action="store_true",
        help="Download all resources"
    )
    parser.add_argument(
        "--apps-infra-path", type=str, default=None,
        help="Set the path to project directory , used for when installing hailo-apps-infra in other projects"
    )
    args = parser.parse_args()
    if args.all:
        args.group = RESOURCES_GROUP_ALL

    config = load_and_validate_config(args.config)
    print("✅ Configuration loaded successfully.")

    storage_dir = config.get(STORAGE_PATH_KEY, STORAGE_PATH_DEFAULT)
    server_url = config.get(SERVER_URL_KEY, SERVER_URL_DEFAULT)

    virtual_env_name = config.get(VIRTUAL_ENV_NAME_KEY, VIRTUAL_ENV_NAME_DEFAULT)
    hailort_version = handle_hailort_version(config.get(HAILORT_VERSION_KEY))
    tappas_version, tappas_variant, tappas_postproc_dir = handle_tappas(
        config.get(TAPPAS_VERSION_KEY, TAPPAS_VERSION_DEFAULT),
        config.get(TAPPAS_VARIANT_KEY, TAPPAS_VARIANT_DEFAULT)
    )

    install_pyhailort, install_tappas_core , venv_pip_cmd , venv_python_cmd = handle_virtualenv(
        virtual_env_name,
        PYTHON_CMD,
        tappas_variant
    )
    handle_dot_env()
    handle_set_and_persist_env(
        handle_host_arch(config.get(HOST_ARCH_KEY, HOST_ARCH_DEFAULT)),
        handle_hailo_arch(config.get(HAILO_ARCH_KEY, HAILO_ARCH_DEFAULT)),
        config.get(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT),
        tappas_postproc_dir,
        config.get(MODEL_ZOO_VERSION_KEY, MODEL_ZOO_VERSION_DEFAULT),
        hailort_version,
        tappas_version,
        virtual_env_name,
        server_url,
        storage_dir,
        tappas_variant
    )

    load_environment()
    print("✅ Environment variables set successfully.")

    if install_pyhailort or install_tappas_core:
        print("🔧 Downloading and installing missing python bindings...")
        handle_install_hailo_packages(
            hailort_version,
            install_pyhailort,
            tappas_version,
            install_tappas_core,
            server_url,
            storage_dir
        )

    print("🔧 Installing core modules and requirements...")
    install_core_modules(pip_cmd=venv_pip_cmd,hailo_apps_infra_path= args.apps_infra_path)
    print("✅ Core modules and requirements installed successfully.")

    print("Creating directories for resources and storage...")
    setup_resource_dirs(storage_dir)
    print("✅ Resource directories created successfully.")


    print(f"🔗 Linking resources directory to {config.get(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT)}...")
    create_symlink(RESOURCES_ROOT_PATH_DEFAULT, config.get(RESOURCES_PATH_KEY, RESOURCES_PATH_DEFAULT))

    # print("⬇️ Downloading resources...")
    download_resources(args.group, args.resources_config)

    # print("⚙️ Compiling post-process...")
    compile_postprocess(args.apps_infra_path)

    print("✅ Hailo Infra installation complete.")


if __name__ == "__main__":
    main()
