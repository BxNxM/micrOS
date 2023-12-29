#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools
import platform

# https://towardsdatascience.com/create-your-custom-python-package-that-you-can-pip-install-from-your-git-repository-f90465867893

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# micrOS devToolKit dependencies
dependencies = ['adafruit-ampy', 'mpremote', 'esptool', 'ipaddress', 'mpy-cross==1.20.0', 'netaddr',
                'pylint', 'PyQt5', 'pyserial', 'resources', 'flask', 'flask_restful', 'numpy',
                'matplotlib', 'json2html', 'opencv-python', 'requests', 'Flask-BasicAuth']

# Hack for raspbian - remove dep: PyQt5
if platform.system().lower() == 'linux':
    # Check if the distribution is Raspbian
    try:
        with open('/etc/os-release', 'r') as file:
            os_release = file.read()
            if 'raspbian' in os_release.lower():
                dependencies.remove('PyQt5')
                dependencies.remove('opencv-python')
    except Exception as e:
        print(f"Non Raspberry: {e}")

setuptools.setup(
    name='micrOSDevToolKit',
    version='1.46.0',
    author='Marcell Ban',
    author_email='miros.framework@gmail.com',
    description='Development and deployment environment for micrOS, the diy micropython automation OS (IoT)',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/BxNxM/micrOS',
    project_urls={
        "Bug Tracker": "https://github.com/BxNxM/micrOS/issues",
        "GitHub Discussions": "https://github.com/BxNxM/micrOS/discussions"
    },
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=dependencies,
    scripts=['devToolKit.py'],
    include_package_data=True,
    use_scm_version=True
    #setup_requires=['setuptools_scm']
)
