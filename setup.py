from setuptools import setup, find_packages

setup(
    name="cs425-project",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "sqlalchemy",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "cs425=cs425.cli:main",
        ],
    },
    python_requires=">=3.6",
    author="Your Name",
    description="CS425 Project for Spring 2025",
)