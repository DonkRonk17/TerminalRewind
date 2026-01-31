#!/usr/bin/env python3
"""
Setup script for TerminalRewind.

TerminalRewind - Command+Z for Your Terminal
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="terminalrewind",
    version="1.0.0",
    author="ATLAS (Team Brain)",
    author_email="logan@metaphy.io",
    description="Command+Z for Your Terminal - Never Lose Track of What Happened",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonkRonk17/TerminalRewind",
    py_modules=["terminalrewind"],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - stdlib only
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "trewind=terminalrewind:main",
            "terminalrewind=terminalrewind:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    keywords="terminal, history, command, undo, rollback, session, export, agent",
    project_urls={
        "Bug Reports": "https://github.com/DonkRonk17/TerminalRewind/issues",
        "Source": "https://github.com/DonkRonk17/TerminalRewind",
        "Documentation": "https://github.com/DonkRonk17/TerminalRewind#readme",
    },
)
