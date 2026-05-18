from setuptools import setup, find_packages

setup(
    name="blender-motion-state-inspector",
    version="0.1.0",
    packages=find_packages(include=["analyzer*", "addon*"]),
    entry_points={
        "console_scripts": [
            "blender-state-inspector=analyzer.cli:main",
        ],
    },
)
