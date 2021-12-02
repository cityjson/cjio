from setuptools import setup
from pathlib import Path

CURRENT_DIR = Path(__file__).parent

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name='cjio',
    version='0.7.2',
    description='CLI to process and manipulate CityJSON files',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url='https://github.com/cityjson/cjio',
    author='Hugo Ledoux, Balázs Dukai',
    author_email='h.ledoux@tudelft.nl, b.dukai@tudelft.nl',
    python_requires='>=3.6',
    packages=['cjio'],
    # include_package_data=True,
    license = 'MIT',
    classifiers=[
        # https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows'
    ],
    install_requires=[
        'Click',
    ],
    extras_require={
        'develop': [
            'pytest',
            'bump2version'
        ],
        'export': [
            'numpy',
            'pandas',
            'mapbox-earcut'
        ],
        'validate': [
            'cjvalpy'
        ],        
        'reproject': [
            'pyproj'
        ]
    },
    entry_points='''
        [console_scripts]
        cjio=cjio.cjio:cli
    ''',
)
