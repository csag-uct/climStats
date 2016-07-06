from setuptools import setup, find_packages
version='0.1.1'

setup(
      name='climstats',
      version=version,
      description='Multi-dimensional environmental data manipulation and statitics',
      url='https://github.com/csag-uct/climstats',
      author='Jackaranda',
      author_email='cjack@csag.uct.ac.za',
      license='Apache',
      packages=['climstats'],
      scripts=['bin/climstats', 'bin/areastats'],
      install_requires=[
      		'netCDF4',
      		'numpy',
      		'cfunits',
      ],
      zip_safe=False)

