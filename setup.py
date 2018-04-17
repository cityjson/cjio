from setuptools import setup

setup(
    name='cjio',
    version='0.1',
    py_modules=['cjio'],
    include_package_data=True,
    install_requires=[
        'click',
        'jsonschema',
        'jsonref',
    ],
    entry_points='''
        [console_scripts]
        cjio=cjio:cli
    ''',
)
