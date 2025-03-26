from setuptools import setup, find_packages

setup(
    name='hailo_apps_infra',
    version='0.3.0',
    description='A collection of infrastructure utilities for Hailo applications',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Hailo',
    author_email='support@hailo.ai',
    url='https://github.com/hailo-ai/hailo-apps-infra',
    install_requires=[],
    packages=find_packages(exclude=["tests", "docs"]),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'get-usb-camera=hailo_apps_infra.get_usb_camera:main'
        ],
    },
)