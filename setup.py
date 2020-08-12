from setuptools import setup, find_packages

setup(name='cobrakbase',
      version='0.2.7',
      description='KBase interface for COBRApy',
      url='https://github.com/Fxe/cobrakbase',
      author='Filipe Liu',
      author_email='fliu@anl.gov',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          "networkx >= 2.4",
          "cobra >= 0.17.1"
      ],
      zip_safe=False)