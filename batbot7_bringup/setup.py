from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

setup(
    name="batbot7_bringup",
    version="7.0.0",
    package_dir={"": "src"},
    description="Batbot7 gui bringup application",
    packages=find_packages(where="src"),
    python_requires=">=3.8"
)