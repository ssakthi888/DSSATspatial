from setuptools import setup, find_packages

setup(
    name='DSSATspatial',
    version='1.0.0',
    author='Sivakumar Sakthivel',
    description='A robust spatial and batch-processing framework for large-scale DSSAT agroecosystem simulations',
    packages=find_packages(exclude=['notebook_demo', 'notebook_demo.*', 'sample_data', 'sample_data.*']),
    include_package_data=True,
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