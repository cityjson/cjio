from setuptools import setup
import re
from pathlib import Path

CURRENT_DIR = Path(__file__).parent

with open("README.md", "r") as fh:
    long_description = fh.read()

def get_version():
    cjio_py = CURRENT_DIR / "cjio/cjio.py"
    print(cjio_py)
    _version_re = re.compile(r"__version__\s+=\s+(?P<version>.*)")
    with open(cjio_py, "r", encoding="utf8") as f:
        match = _version_re.search(f.read())
        version = match.group("version") if match is not None else '"unknown"'
    return str(version)

setup(
    name='cjio',
    version=get_version(),
    description='CLI to process and manipulate CityJSON files',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/tudelft3d/cjio',
    author='Hugo Ledoux, Balázs Dukai',
    author_email='h.ledoux@tudelft.nl, b.dukai@tudelft.nl',
    python_requires='>=3',
    packages=['cjio'],
    # package_data={'cjio': ['schemas/*', 'schemas/v06/*']},
    include_package_data=True,
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
        'jsonschema',
        'jsonref'
    ],
    entry_points='''
        [console_scripts]
        cjio=cjio.cjio:cli
    ''',
)
