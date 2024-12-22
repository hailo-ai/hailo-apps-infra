from setuptools import setup, find_packages
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_requirements():
    with open("requirements.txt", "r") as f:
        return f.read().splitlines()
requirements = read_requirements()

def check_hailo_package():
    try:
        import hailo
    except ImportError:
        logger.error("Hailo python package not found. Please make sure you're in the Hailo virtual environment. Run 'source setup_env.sh' and try again.")
        sys.exit(1)
        
def run_shell_command(command, error_message):
    logger.info(f"Running command: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        logger.error(f"{error_message}. Exit code: {result.returncode}")
        sys.exit(result.returncode)
    else:
        print(f"{command} succeded")

def get_downloaded_files():
    """Collect files from resources directory after they have been downloaded."""
    resource_dir = os.path.join(os.path.dirname(__file__), 'hailo_apps_infra', 'resources')
    downloaded_files = []
    for root, _, files in os.walk(resource_dir):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), 'hailo_apps_infra')
            downloaded_files.append(relative_path)
    return downloaded_files

def main():
    check_hailo_package()

    requirements = read_requirements()

    logger.info("Compiling C++ code...")
    run_shell_command("./compile_postprocess.sh", "Failed to compile C++ code")
    logger.info("Downloading Resources...")
    run_shell_command("./download_resources.sh --all", "Failed to download resources")
    
    setup(
        name='hailo_apps_infra',
        version='0.1.0',
        description='A collection of infrastructure utilities for Hailo applications',
        long_description=open('README.md').read(),
        long_description_content_type='text/markdown',
        author='Gilad Nahor,
        author_email='giladn@hailo.ai',
        url='https://github.com/hailo-ai/hailo-apps-infra',
        install_requires=requirements,
        package_data={
            'hailo_apps_infra': ['*.json', '*.sh', '*.cpp', '*.hpp', '*.pc', '*.mp4'] + get_downloaded_files(),
        },
        packages=find_packages(exclude=["tests", "docs"]),
        include_package_data=True,
        entry_points={
            'console_scripts': [
                'get-usb-camera=hailo_apps_infra.get_usb_camera:main'
            ],
        },
    )
    
if __name__ == '__main__':
    main()
    