from setuptools import setup

setup(name='cobrakbase',
      version='0.0.1',
      description='KBase interface for COBRApy',
      url='https://github.com/Fxe/cobrakbase',
      author='Filipe Liu',
      author_email='fliu@anl.gov',
      license='MIT',
      packages=['cobrakbase'],
      install_requires=[
          "cobra >= 0.13.4"
      ],
      zip_safe=False)