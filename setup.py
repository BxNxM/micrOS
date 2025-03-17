#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools

# https://towardsdatascience.com/create-your-custom-python-package-that-you-can-pip-install-from-your-git-repository-f90465867893

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# micrOS devToolKit dependencies
dependencies = ['adafruit-ampy', 'mpremote', 'esptool', 'ipaddress', 'netaddr',
                'pylint', 'pyserial', 'resources', 'flask', 'flask_restful', 'numpy',
                'json2html', 'requests', 'Flask-BasicAuth', 'soundfile']

# Optional dependencies in devToolKit.py: 'PyQt5', 'opencv-python', 'PyAudio', 'mpy-cross==1.20.0'

setuptools.setup(
    name='micrOSDevToolKit',
    version='2.9.11',
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
)
