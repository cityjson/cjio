from setuptools import setup

setup(
    name='cjio',
    version='0.2.1',
    description='Python CLI to process and manipulate CityJSON files',
    long_description='Python CLI to process and manipulate [CityJSON](http://www.cityjson.org) files. The different operators can be chained to perform several processing in one step, the CityJSON model goes through them and allows to save to a new CityJSON at the end.',
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
