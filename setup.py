from setuptools import setup, find_packages

setup(name='cobrakbase',
      version='0.2.3',
      description='KBase interface for COBRApy',
      url='https://github.com/Fxe/cobrakbase',
      author='Filipe Liu',
      author_email='fliu@anl.gov',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          "cobra >= 0.14.2"
      ],
      zip_safe=False)