from setuptools import setup

setup(
    name='cjio',
    version='0.1.0',
    description='Work with CityJSON effortlessly',
    url='https://github.com/tudelft3d/cityjson_tools',
    author='Hugo Ledoux, Balázs Dukai',
    author_email='h.ledoux@tudelft.nl, b.dukai@tudelft.nl',
    python_requires='>=3',
    packages=['cjio'],
    package_data={'cjio': ['schemas/*']},
    include_package_data=True,
    license = 'MIT',
    classifiers=[
        # https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: GIS',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux'
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows'
    ],
    entry_points='''
        [console_scripts]
        cjio=cjio.cjio:cli
    ''',
)
