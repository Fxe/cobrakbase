from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

setup(
    name="cobrakbase",
    version="0.3.1",
    description="KBase interface for COBRApy",
    long_description_content_type="text/markdown",
    long_description=readme,
    url="https://github.com/Fxe/cobrakbase",
    author="Filipe Liu",
    author_email="fliu@anl.gov",
    license="MIT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Natural Language :: English"
    ],
    install_requires=[
        # "modelseedpy >= 1.0.0", # when available in pypi
        "pandas >= 1.0.0",
        "networkx >= 2.4",
        "modelseedpy >= 0.3.0",
    ],
    zip_safe=True,
)
