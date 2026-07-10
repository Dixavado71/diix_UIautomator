from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="diix-ui-automator",
    version="0.1.0",
    description="Framework modularizado Python para automação Android via ADB e UIAutomator2.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dixavado71",
    packages=find_packages(include=["ui_automator", "ui_automator.*"]),
    python_requires=">=3.8",
    install_requires=["uiautomator2"],
    entry_points={
        "console_scripts": [
            "diix-ui-automator=ui_automator.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
