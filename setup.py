from setuptools import setup, find_packages

setup(name='cobrakbase',
      version='0.1.0',
      description='KBase interface for COBRApy',
      url='https://github.com/Fxe/cobrakbase',
      author='Filipe Liu',
      author_email='fliu@anl.gov',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          "cobra >= 0.13.4"
      ],
      zip_safe=False)