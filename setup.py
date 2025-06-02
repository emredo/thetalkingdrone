from setuptools import setup, find_namespace_packages

setup(
    name="thetalkingdrone",
    version="0.1.0",
    description="API for the Talking Drone simulation",
    author="The Talking Drone Team",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        # Read requirements from requirements.txt
        line.strip()
        for line in open("requirements.txt")
        if not line.startswith("#") and line.strip() != ""
    ],
    entry_points={
        "console_scripts": [
            "talking-drone=src:main",
        ],
    },
) 