from setuptools import setup, find_packages
import platform

os_name = platform.system().lower()
if 'windows' in os_name:
    exclusions = {'DSSATspatial': ['bin/dscsm0480', 'bin/dscsm0485', 'bin/dscsm0486']}
else:
    exclusions = {'DSSATspatial': ['bin/*.exe']}

setup(
    name='DSSATspatial',
    version='1.0.0',
    author='Sivakumar Sakthivel',
    description='A robust spatial and batch-processing framework for large-scale DSSAT agroecosystem simulations',
    packages=find_packages(),
    include_package_data=True,
    exclude_package_data=exclusions,
    install_requires=[
        'pandas',
        'rosetta-soil',
        'chardet',
        'tqdm',
        'dask',
        'geopandas',
        'openpyxl',
        'shiny',
        'pyarrow'
    ],
    python_requires='>=3.12'
)